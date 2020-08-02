from datetime import timedelta
from typing import Optional, Any, TYPE_CHECKING, List

from django.contrib.postgres.fields import JSONField
from django.db import models, transaction
from django.db.models import QuerySet
from django.utils import timezone

from django_partisan.config.processor_configs import PostponeConfig, ErrorsHandleConfig
from django_partisan.exceptions import PostponeTask, MaxPostponesReached
from django_partisan.settings import get_queue_settings, const

if TYPE_CHECKING:
    from django_partisan.processor import BaseTaskProcessor


class TasksManager(models.Manager):
    def get_queryset(self) -> QuerySet:
        return QuerySet(self.model, using=self._db)

    @transaction.atomic
    def reset_tasks_to_initial_status(self) -> None:
        self.get_queryset().select_for_update().filter(
            status=Task.STATUS_IN_PROCESS
        ).update(status=Task.STATUS_NEW)

    @transaction.atomic
    def select_for_process(
        self, count: Optional[int] = None, queue_name: str = const.DEFAULT_QUEUE_NAME
    ) -> List['Task']:
        base_qs = (
            self.get_queryset()
            .select_for_update()
            .filter(
                status=Task.STATUS_NEW,
                execute_after__lte=timezone.now(),
                queue_name=queue_name,
            )
        )
        if count is not None:
            base_qs = base_qs.all()[:count]
        new_tasks_list = list(base_qs.values_list('pk', flat=True))
        selected_tasks = (
            self.get_queryset().select_for_update().filter(id__in=new_tasks_list)
        )
        self.get_queryset().select_for_update().filter(id__in=new_tasks_list).update(
            status=Task.STATUS_IN_PROCESS
        )
        return list(selected_tasks)


class Task(models.Model):
    STATUS_NEW = 'new'
    STATUS_IN_PROCESS = 'in_process'
    STATUS_ERROR = 'error'
    STATUS_FINISHED = 'finished'
    STATUS_CHOICES = (
        (STATUS_NEW, 'New'),
        (STATUS_IN_PROCESS, 'In Process'),
        (STATUS_ERROR, 'Error'),
        (STATUS_FINISHED, 'Finished'),
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    queue_name = models.CharField(max_length=50, default=const.DEFAULT_QUEUE_NAME)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processor_class = models.CharField(max_length=128)
    priority = models.IntegerField(default=10)
    execute_after = models.DateTimeField(default=timezone.now)
    arguments = JSONField(default=dict)
    extra = JSONField(default=dict)

    objects = TasksManager()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.settings = get_queue_settings(self.queue_name)

    def get_initialized_processor(self) -> 'BaseTaskProcessor':
        from django_partisan.processor import BaseTaskProcessor

        processor_class = BaseTaskProcessor.get_processor_class(self.processor_class)
        return processor_class.get_initialized_processor(self)

    def run(self) -> Any:
        processor = self.get_initialized_processor()
        retries_config = processor.RETRY_ON_ERROR_CONFIG
        postpones_config = processor.POSTPONE_CONFIG
        errors_to_retry_on = (
            retries_config.retry_on_errors if retries_config is not None else ()
        )

        try:
            return processor.run()
        except PostponeTask as postpone_signal:
            self.handle_postpone(processor, postpones_config, postpone_signal)
        except errors_to_retry_on as error_signal:
            self.handle_error(processor, retries_config, error_signal)

    def handle_postpone(
        self,
        processor: 'BaseTaskProcessor',
        postpones_config: Optional[PostponeConfig],
        postpone_signal: PostponeTask,
    ) -> None:
        postpone_num = self.postpones_count + 1
        if (
            postpones_config is not None
            and postpone_num > postpones_config.max_postpones
        ) or (
            self.settings.DEFAULT_POSTPONES_COUNT is not None
            and postpone_num > self.settings.DEFAULT_POSTPONES_COUNT
        ):
            raise MaxPostponesReached(postpone_num)
        self.postpones_count = postpone_num
        new_start_time_for_task = timezone.now() + timedelta(
            seconds=postpone_signal.postpone_for_seconds
        )
        processor.delay_for_retry(execute_after=new_start_time_for_task)

    def handle_error(
        self,
        processor: 'BaseTaskProcessor',
        retries_config: Optional[ErrorsHandleConfig],
        error_signal: Exception,
    ) -> None:
        try_num = self.tries_count + 1
        if not retries_config or not retries_config.shoud_be_retried(try_num):
            raise
        self.tries_count = try_num
        new_start_time_for_task = retries_config.get_new_datetime_for_retry(try_num)
        processor.delay_for_retry(execute_after=new_start_time_for_task)

    def complete(self) -> None:
        if self.settings.DELETE_TASKS_ON_COMPLETE:
            self.delete()
            return
        self.status = self.STATUS_FINISHED
        self.save(update_fields=('status', 'updated_at'))

    def fail(self, err: Exception) -> None:
        self.status = self.STATUS_ERROR
        self.extra = {'message': str(err)}
        self.save(update_fields=('status', 'extra', 'updated_at'))

    @property
    def postpones_count(self) -> int:
        return self.extra.get('postpones', {'count': 0}).get('count')

    @postpones_count.setter
    def postpones_count(self, num: int) -> None:
        extra_data = self.extra.get('postpones', {'count': 0})
        extra_data.update({'postpones': {'count': num}})
        self.extra = extra_data
        self.save(update_fields=['updated_at', 'extra'])

    @property
    def tries_count(self) -> int:
        return self.extra.get('retries', {'count': 0}).get('count')

    @tries_count.setter
    def tries_count(self, num: int) -> None:
        extra_data = self.extra.get('retries', {'count': 0})
        extra_data.update({'retries': {'count': num}})
        self.extra = extra_data
        self.save(update_fields=['updated_at', 'extra'])

    class Meta:
        ordering = ('-priority',)

    def __str__(self) -> str:
        return '{} ({}) - {}'.format(
            self.processor_class, self.arguments, self.get_status_display()  # type: ignore
        )
