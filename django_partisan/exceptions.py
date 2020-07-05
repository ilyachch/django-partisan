from typing import Any

from django.core.exceptions import ImproperlyConfigured


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
