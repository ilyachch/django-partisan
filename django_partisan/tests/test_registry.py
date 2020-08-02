from django.test import TestCase

from django_partisan.registry import registry
from django_partisan.exceptions import (
    ProcessorClassNotFound,
    ProcessorClassAlreadyRegistered,
)
from django_partisan.models import Task
from django_partisan.processor import BaseTaskProcessor


@registry.register
class RegisteredSimpleTaskProcessor(BaseTaskProcessor):
    def run(self):
        return self.args[0]


class NotRegisteredSimpleTaskProcessor(BaseTaskProcessor):
    def run(self):
        return None


class TestTaskProcessor(TestCase):
    def test_getting_registered_processor_class(self):
        RegisteredSimpleTaskProcessor(1).delay()
        task_obj: Task = Task.objects.first()
        self.assertEqual(
            BaseTaskProcessor.get_processor_class(task_obj.processor_class),
            RegisteredSimpleTaskProcessor,
        )

    def test_register_decorator(self):
        registry.register(NotRegisteredSimpleTaskProcessor)
        self.assertTrue(
            registry.registry.is_processor_registered(
                NotRegisteredSimpleTaskProcessor.__name__
            )
        )

    def test_processor_is_already_registered(self):
        local_registry = registry.Registry()
        local_registry.register_processor_class(RegisteredSimpleTaskProcessor)
        with self.assertRaises(ProcessorClassAlreadyRegistered):
            local_registry.register_processor_class(RegisteredSimpleTaskProcessor)

    def test_processor_is_not_registered(self):
        local_registry = registry.Registry()
        with self.assertRaises(ProcessorClassNotFound):
            local_registry.get_processor_class_by_name('NotRegisteredTaskProcessor')
