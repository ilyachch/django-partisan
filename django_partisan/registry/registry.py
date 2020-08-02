from typing import Type, Dict, TYPE_CHECKING

from django_partisan.exceptions import (
    ProcessorClassAlreadyRegistered,
    ProcessorClassNotFound,
)

if TYPE_CHECKING:
    from django_partisan.processor import BaseTaskProcessor


class Registry:
    def __init__(self) -> None:
        self._registry: Dict[str, Type['BaseTaskProcessor']] = {}

    def register_processor_class(
        self, processor_class: Type['BaseTaskProcessor']
    ) -> None:
        processor_name = processor_class.__name__
        if self.is_processor_registered(processor_name):
            raise ProcessorClassAlreadyRegistered(processor_name)
        self._registry[processor_name] = processor_class

    def get_processor_class_by_name(
        self, processor_name: str
    ) -> Type['BaseTaskProcessor']:
        if not self.is_processor_registered(processor_name):
            raise ProcessorClassNotFound(processor_name)
        return self._registry[processor_name]

    def is_processor_registered(self, processor_name: str) -> bool:
        return processor_name in self._registry.keys()


registry = Registry()


def register(klass: Type['BaseTaskProcessor']) -> Type['BaseTaskProcessor']:
    registry.register_processor_class(klass)
    return klass
