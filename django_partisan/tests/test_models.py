from unittest import mock

from django.test import TestCase
from django.utils import timezone

from django_partisan.settings import get_queue_settings
from django_partisan.exceptions import MaxPostponesReached
from django_partisan.models import Task
from django_partisan.tests.fixtures import (
    TestTaskProcessor,
    ConfiguredTestTaskProcessor,
    ConfiguredFailingTestTaskProcessor,
    PostponableTestTaskProcessor,
    PostponableConfiguredTestTaskProcessor,
)

settings = get_queue_settings()


class TestTaskModel(TestCase):
    def setUp(self) -> None:
        for i in range(10):
            TestTaskProcessor(i).delay()

    def test_task_verbose_name(self):
        new_task = Task.objects.first()
        self.assertEqual(
            str(new_task), "TestTaskProcessor ({'args': [0], 'kwargs': {}}) - New",
        )

    def test_select_for_processing_with_count(self):
        tasks = Task.objects.select_for_process()
        self.assertTrue(all([task.status == Task.STATUS_IN_PROCESS for task in tasks]))
        self.assertEqual(len(tasks), 10)

    def test_reset_tasks_to_initial_status(self):
        Task.objects.select_for_process(2)
        self.assertNotEqual(Task.objects.filter(status=Task.STATUS_NEW).count(), 10)
        Task.objects.reset_tasks_to_initial_status()
        self.assertEqual(Task.objects.filter(status=Task.STATUS_NEW).count(), 10)

    def test_select_for_processing(self):
        tasks = Task.objects.select_for_process(5)
        self.assertTrue(all([task.status == Task.STATUS_IN_PROCESS for task in tasks]))
        self.assertEqual(len(tasks), 5)

    def test_task_complete(self):
        task = Task.objects.select_for_process()[0]
        task.complete()
        self.assertEqual(task.status, Task.STATUS_FINISHED)

    def test_task_fail(self):
        exception_text = 'Some exception text'
        task = Task.objects.select_for_process()[0]
        task.fail(Exception(exception_text))
        self.assertEqual(task.status, Task.STATUS_ERROR)
        self.assertEqual(task.extra, {'message': exception_text})

    def test_task_deling_on_complete(self):
        task = Task.objects.select_for_process()[0]
        with mock.patch.object(settings, 'DELETE_TASKS_ON_COMPLETE', return_value=True):
            task.complete()
        self.assertEqual(Task.objects.count(), 9)

    def test_tries_count(self):
        task = Task.objects.select_for_process()[0]
        self.assertEqual(task.tries_count, 0)
        task.tries_count = 3
        self.assertEqual(task.tries_count, 3)
        task.tries_count = 6
        self.assertEqual(task.tries_count, 6)

    def test_get_initialized_processor(self):
        task = TestTaskProcessor(10, test_key='test').delay()
        processor = task.get_initialized_processor()
        self.assertIsInstance(processor, TestTaskProcessor)
        self.assertEqual(processor.task_obj.id, task.id)
        self.assertEqual(processor.args, (10,))
        self.assertEqual(processor.kwargs, {'test_key': 'test'})

    def test_configured_processor_task_run(self):
        task = ConfiguredTestTaskProcessor(10).delay()
        self.assertEqual(task.run(), 10)

    def test_configured_processor_task_run_redelayed(self):
        task = ConfiguredFailingTestTaskProcessor(10).delay()
        task.run()
        self.assertEqual(task.tries_count, 1)
        self.assertEqual(task.status, Task.STATUS_NEW)

    def test_configured_processor_task_run_fails(self):
        task = ConfiguredFailingTestTaskProcessor(10).delay()
        task.tries_count = 5
        with self.assertRaises(ValueError):
            task.run()

    def test_postponable_processor_run(self):
        task = PostponableTestTaskProcessor().delay()
        task.run()
        now = timezone.now().timestamp()
        self.assertEqual(task.postpones_count, 1)
        self.assertEqual(task.status, Task.STATUS_NEW)
        self.assertEqual(round(task.execute_after.timestamp() - now), 15)

    def test_postpones_count(self):
        task = PostponableTestTaskProcessor().delay()
        self.assertEqual(task.postpones_count, 0)
        task.postpones_count = 3
        self.assertEqual(task.postpones_count, 3)
        task.postpones_count = 6
        self.assertEqual(task.postpones_count, 6)

    def test_max_postpones_reached_not_configured_processor(self):
        task = PostponableTestTaskProcessor().delay()
        task.postpones_count = settings.DEFAULT_POSTPONES_COUNT
        with self.assertRaises(MaxPostponesReached):
            task.run()

    def test_max_postpones_reached_configured_processor(self):
        task = PostponableConfiguredTestTaskProcessor().delay()
        task.postpones_count = 5
        with self.assertRaises(MaxPostponesReached):
            task.run()
