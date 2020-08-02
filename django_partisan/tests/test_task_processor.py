from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from django_partisan.exceptions import ProcessorClassNotFound
from django_partisan.models import Task
from django_partisan.processor import BaseTaskProcessor


class SimpleTaskProcessor(BaseTaskProcessor):
    def run(self):
        return self.args[0]


class SimpleTaskProcessorWithConfig(BaseTaskProcessor):
    def run(self):
        return self.args[0]


class SimpleUniqueTaskProcessor(SimpleTaskProcessor):
    UNIQUE_FOR_PARAMS = True


class SimpleHighPriorityTaskProcessor(SimpleTaskProcessor):
    PRIORITY = 100


class TestTaskProcessor(TestCase):
    def test_task_running(self):
        value = 'some value'
        task = SimpleTaskProcessor(value)
        self.assertEqual(task.run(), value)

    def test_task_delay(self):
        value = 'some value'
        SimpleTaskProcessor(value).delay()
        db_task: Task = Task.objects.first()
        self.assertEqual(Task.objects.count(), 1)
        self.assertEqual(db_task.processor_class, 'SimpleTaskProcessor')
        self.assertEqual(db_task.status, Task.STATUS_NEW)
        self.assertEqual(db_task.arguments, {'args': [value], 'kwargs': {}})

    def test_task_delay_until(self):
        now = timezone.now()
        execute_after = now + timedelta(minutes=5)
        SimpleTaskProcessor('some_value').delay(execute_after=execute_after)
        self.assertEqual(Task.objects.first().execute_after, execute_after)

    def test_multiple_tasks_creation(self):
        SimpleTaskProcessor(1).delay()
        SimpleTaskProcessor(2).delay()
        SimpleTaskProcessor(3).delay()
        self.assertEqual(Task.objects.count(), 3)

    def test_unique_task_creating(self):
        SimpleUniqueTaskProcessor(1).delay()
        SimpleUniqueTaskProcessor(1).delay()
        SimpleUniqueTaskProcessor(1).delay()
        self.assertEqual(Task.objects.count(), 1)

    def test_getting_processor_class(self):
        SimpleTaskProcessor(1).delay()
        task_obj: Task = Task.objects.first()
        self.assertEqual(
            BaseTaskProcessor.get_processor_class(task_obj.processor_class),
            SimpleTaskProcessor,
        )

    def test_priority(self):
        SimpleTaskProcessor(1).delay()
        SimpleHighPriorityTaskProcessor(10).delay()
        high_priority_task: Task = Task.objects.first()
        self.assertEqual(
            high_priority_task.processor_class, 'SimpleHighPriorityTaskProcessor'
        )

    def test_manual_priority(self):
        SimpleHighPriorityTaskProcessor(10).delay()
        SimpleTaskProcessor(2).delay(priority=1000)
        high_priority_task: Task = Task.objects.first()
        self.assertEqual(high_priority_task.processor_class, 'SimpleTaskProcessor')

    def test_processor_error(self):
        Task.objects.create(
            processor_class='SomeMissingTaskProcessor',
            arguments={'args': [], 'kwargs': {}},
        )
        task_obj: Task = Task.objects.first()
        with self.assertRaises(ProcessorClassNotFound):
            BaseTaskProcessor.get_processor_class(task_obj.processor_class)

    def test_run_from_model(self):
        value = 10
        SimpleTaskProcessor(value).delay()
        result = Task.objects.first().run()
        self.assertEqual(result, value)

    def test_task_delay_for_retry_fails(self):
        with self.assertRaises(TypeError):
            SimpleTaskProcessor(10).delay_for_retry(execute_after=timezone.now())

    def test_processor_initialized_with_task_obj_delay_fails(self):
        task = SimpleTaskProcessor(10).delay()
        with self.assertRaises(TypeError):
            task.get_initialized_processor().delay()

    def test_task_delay_for_retry(self):
        SimpleTaskProcessor(10).delay()
        task = Task.objects.select_for_process()[0]
        processor = task.get_initialized_processor()
        processor.delay_for_retry()
        self.assertEqual(task.STATUS_NEW, task.status)
