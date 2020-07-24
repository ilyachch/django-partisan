from typing import Any, Optional

from django.core.exceptions import ImproperlyConfigured

from django_partisan.settings import const, PARTISAN_CONFIG, get_queue_settings


class PartisanException(Exception):
    pass


class ProcessorClassException(PartisanException):
    message: str

    def __init__(self, processor_class_name: str, *args: Any, **kwargs: Any) -> None:
        if not hasattr(self, 'message') or not self.message:
            raise NotImplementedError('Error should have a message')
        if not '{}' in self.message:
            raise ImproperlyConfigured('Message should be formatable')
        if self.message.count('{}') > 1:
            raise ImproperlyConfigured(
                'Message should have 1 placeholder for processor class name'
            )
        super().__init__(self.message.format(processor_class_name))


class ProcessorClassNotFound(ProcessorClassException):
    message = 'Processor class {} cannot be found. Is it registered?'


class ProcessorClassAlreadyRegistered(ProcessorClassException):
    message = 'Processor class {} already registered'


class Postpone(Exception):
    """Base Exception for postponing"""


class PostponeTask(Postpone):
    def __init__(self, postpone_for_seconds: Optional[int] = None) -> None:
        self.postpone_for_seconds = (
            postpone_for_seconds or get_queue_settings().DEFAULT_POSTPONE_DELAY_SECONDS
        )
        super().__init__()


class MaxPostponesReached(Postpone):
    def __init__(self, max_tries: int) -> None:
        super().__init__(f'Maximum postpones ({max_tries}) reached. Failing')
