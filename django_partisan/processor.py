import abc

from django_partisan.exceptions import WorkerClassNotFound
from django_partisan.models import Task


class BaseTaskProcessor(abc.ABC):
    PRIORITY = None

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    @classmethod
    def get_processor_class(cls, subclass_name):
        for subclass in cls.__subclasses__():
            if subclass.__name__ == subclass_name:
                return subclass
        raise WorkerClassNotFound('{} not found'.format(subclass_name))

    @abc.abstractmethod
    def run(self):
        raise NotImplementedError()

    def delay(self, priority=None):
        task_data = {
            'processor_class': self.__class__.__name__,
            'arguments': {'args': self.args, 'kwargs': self.kwargs},
        }
        if self.PRIORITY is not None:
            task_data.update(priority=self.PRIORITY)
        if priority is not None:
            task_data.update(priority=priority)
        return Task.objects.create(**task_data)
