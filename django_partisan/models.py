from typing import Optional, Any, Type, TYPE_CHECKING

from django.contrib.postgres.fields import JSONField
from django.db import models, transaction
from django.db.models import QuerySet
from django.utils import timezone

from django_partisan import settings

if TYPE_CHECKING:
    from django_partisan.processor import BaseTaskProcessor  # pragma: no cover


class TasksManager(models.Manager):
    def get_queryset(self) -> QuerySet:
        return QuerySet(self.model, using=self._db)

    @transaction.atomic
    def reset_tasks_to_initial_status(self) -> None:
        self.get_queryset().select_for_update().filter(
            status=Task.STATUS_IN_PROCESS
        ).update(status=Task.STATUS_NEW)

    @transaction.atomic
    def select_for_process(self, count: Optional[int] = None) -> QuerySet:
        base_qs = (
            self.get_queryset()
            .select_for_update()
            .filter(status=Task.STATUS_NEW, execute_after__lte=timezone.now())
        )
        if count is not None:
            base_qs = base_qs[:count]
        new_tasks_list = list(base_qs.values_list('pk', flat=True))
        selected_tasks = (
            self.get_queryset().select_for_update().filter(id__in=new_tasks_list)
        )
        self.get_queryset().select_for_update().filter(id__in=new_tasks_list).update(
            status=Task.STATUS_IN_PROCESS
        )
        return selected_tasks


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

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)  # type: ignore
    updated_at = models.DateTimeField(auto_now=True)  # type: ignore
    processor_class = models.CharField(max_length=128)  # type: ignore
    priority = models.IntegerField(default=10)  # type: ignore
    execute_after = models.DateTimeField(default=timezone.now)  # type: ignore
    arguments = JSONField(default=dict)
    extra = JSONField(null=True, blank=True)

    objects = TasksManager()

    def get_initialized_processor(self) -> 'BaseTaskProcessor':
        from django_partisan.processor import BaseTaskProcessor

        args = self.arguments.get('args', [])
        kwargs = self.arguments.get('kwargs', {})
        processor_class = BaseTaskProcessor.get_processor_class(self.processor_class)
        return processor_class(*args, task=self, **kwargs)

    def run(self) -> Any:
        processor = self.get_initialized_processor()
        retries_config = processor.RETRY_ON_ERROR_CONFIG
        if retries_config is None:
            return processor.run()

        try:
            return processor.run()
        except tuple(retries_config.retry_on_errors):
            try_num = self.tries_count + 1
            if not retries_config.shoud_be_retried(try_num):
                raise
            self.tries_count = try_num
            new_start_time_for_task = retries_config.get_new_datetime_for_delay(try_num)
            processor.delay_for_retry(execute_after=new_start_time_for_task)

    def complete(self) -> None:
        if settings.DELETE_TASKS_ON_COMPLETE:
            self.delete()
            return
        self.status = self.STATUS_FINISHED
        self.save(update_fields=('status', 'updated_at'))

    def fail(self, err: Exception) -> None:
        self.status = self.STATUS_ERROR
        self.extra = {'message': str(err)}
        self.save(update_fields=('status', 'extra', 'updated_at'))

    @property
    def tries_count(self) -> int:
        if self.extra is None:
            return 0
        return self.extra.get('retries', {'count': 0}).get('count')

    @tries_count.setter
    def tries_count(self, num: int) -> None:
        if self.extra is None:
            extra_data = {'retries': {'count': 0}}
        else:
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
