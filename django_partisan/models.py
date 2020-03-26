from typing import Dict, Optional, Any

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.db.models import QuerySet


def get_default_status() -> Dict[str, str]:
    return Task.DEFAULT_STATUS


class TasksManager(models.Manager):
    def get_queryset(self) -> QuerySet:
        return QuerySet(self.model, using=self._db)

    def get_new_tasks(self, count: Optional[int] = None) -> QuerySet:
        base_qs = self.get_queryset().filter(status__status=Task.STATUS_NEW)
        if count is not None:
            return base_qs[:count]
        return base_qs

    def select_to_process(self, count: Optional[int] = None) -> QuerySet:
        base_qs = self.get_new_tasks(count).values_list('pk', flat=True)
        self.get_queryset().filter(id__in=list(base_qs)).update(
            status={'status': Task.STATUS_PROC}
        )
        return self.get_queryset().filter(id__in=list(base_qs))


class Task(models.Model):
    STATUS_NEW = 'New'
    STATUS_PROC = 'In Process'
    STATUS_ERR = 'Error'
    STATUS_FIN = 'Finished'
    DEFAULT_STATUS = {'status': STATUS_NEW}

    created_at = models.DateTimeField(auto_now_add=True)  # type: ignore
    processor_class = models.CharField(max_length=128)  # type: ignore
    priority = models.IntegerField(default=10)  # type: ignore
    arguments = JSONField()
    status = JSONField(default=get_default_status)

    objects = TasksManager()

    def run(self) -> Any:
        from django_partisan.processor import BaseTaskProcessor

        processor_class = BaseTaskProcessor.get_processor_class(self.processor_class)
        processor = processor_class(*self.arguments['args'], **self.arguments['kwargs'])
        return processor.run()

    def complete(self) -> None:
        self.status = {'status': self.STATUS_FIN}
        self.save()

    def fail(self, err: Exception) -> None:
        self.status = {'status': self.STATUS_ERR, 'message': str(err)}
        self.save()

    class Meta:
        ordering = ('-priority',)

    def __str__(self) -> str:
        return '{} ({}) - {}'.format(self.processor_class, self.arguments, self.status)
