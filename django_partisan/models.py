from typing import Optional, Any

from django.contrib.postgres.fields import JSONField
from django.db import models, transaction
from django.db.models import QuerySet
from django.utils import timezone


class TasksManager(models.Manager):
    def get_queryset(self) -> QuerySet:
        return QuerySet(self.model, using=self._db)

    def get_new_tasks(self, count: Optional[int] = None) -> QuerySet:
        base_qs = (
            self.get_queryset()
            .select_for_update()
            .filter(status=Task.STATUS_NEW, execute_after__lte=timezone.now())
        )
        if count is not None:
            return base_qs[:count]
        return base_qs

    @transaction.atomic
    def select_for_process(self, count: Optional[int] = None) -> QuerySet:
        new_tasks_list = list(self.get_new_tasks(count).values_list('pk', flat=True))
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

    def run(self) -> Any:
        from django_partisan.processor import BaseTaskProcessor

        args = self.arguments.get('args', [])
        kwargs = self.arguments.get('kwargs', {})
        processor_class = BaseTaskProcessor.get_processor_class(self.processor_class)
        processor = processor_class(*args, **kwargs)
        return processor.run()

    def complete(self) -> None:
        self.status = self.STATUS_FINISHED
        self.save(update_fields=('status', 'updated_at'))

    def fail(self, err: Exception) -> None:
        self.status = self.STATUS_ERROR
        self.extra = {'message': str(err)}
        self.save(update_fields=('status', 'extra', 'updated_at'))

    class Meta:
        ordering = ('-priority',)

    def __str__(self) -> str:
        return '{} ({}) - {}'.format(
            self.processor_class, self.arguments, self.get_status_display()  # type: ignore
        )
