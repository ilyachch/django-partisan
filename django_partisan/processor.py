import abc
from typing import Type, Any

from django_partisan.exceptions import WorkerClassNotFound
from django_partisan.models import Task


class BaseTaskProcessor(abc.ABC):
    PRIORITY = 10

    def __init__(self, *args: Any, **kwargs: Any):
        self.args = args
        self.kwargs = kwargs

    @classmethod
    def get_processor_class(cls, subclass_name: str) -> Type['BaseTaskProcessor']:
        for subclass in cls.__subclasses__():
            if subclass.__name__ == subclass_name:
                return subclass
        raise WorkerClassNotFound('{} not found'.format(subclass_name))

    @abc.abstractmethod
    def run(self) -> Any:
        raise NotImplementedError()

    def delay(self, priority: int = None) -> Task:
        task_data = {
            'processor_class': self.__class__.__name__,
            'arguments': {'args': self.args, 'kwargs': self.kwargs},
            'priority': priority or self.PRIORITY,
        }
        return Task.objects.create(**task_data)
