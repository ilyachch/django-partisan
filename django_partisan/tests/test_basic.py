from unittest import mock

from django.test import TestCase

from django_partisan import settings
from django_partisan.models import Task
from django_partisan.processor import BaseTaskProcessor


class TestTaskProcessor(BaseTaskProcessor):
    def run(self):
        return self.args[0]


class TestTaskModel(TestCase):
    def setUp(self) -> None:
        for i in range(10):
            TestTaskProcessor(i).delay()

    def test_task_verbose_name(self):
        new_task = Task.objects.first()
        self.assertEqual(
            str(new_task),
            "TestTaskProcessor ({'args': [0], 'kwargs': {}}) - New",
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
        task = Task.objects.select_for_process().first()
        task.complete()
        self.assertEqual(task.status, Task.STATUS_FINISHED)

    def test_task_fail(self):
        exception_text = 'Some exception text'
        task = Task.objects.select_for_process().first()
        task.fail(Exception(exception_text))
        self.assertEqual(task.status, Task.STATUS_ERROR)
        self.assertEqual(task.extra, {'message': exception_text})

    def test_task_deling_on_complete(self):
        task = Task.objects.select_for_process().first()
        with mock.patch.object(settings, 'DELETE_TASKS_ON_COMPLETE', return_value=True):
            task.complete()
        self.assertEqual(Task.objects.count(), 9)
