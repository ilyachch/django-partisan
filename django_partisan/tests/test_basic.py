from django.test import TestCase, override_settings

from django_partisan.exceptions import WorkerClassNotFound
from django_partisan.models import Task
from django_partisan.processor import BaseTaskProcessor


class SimpleTaskProcessor(BaseTaskProcessor):
    def run(self):
        return self.args[0]


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

    def test_multiple_tasks_creation(self):
        SimpleTaskProcessor(1).delay()
        SimpleTaskProcessor(2).delay()
        SimpleTaskProcessor(3).delay()
        self.assertEqual(Task.objects.count(), 3)

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
        SimpleTaskProcessor(2).delay(1000)
        high_priority_task: Task = Task.objects.first()
        self.assertEqual(high_priority_task.processor_class, 'SimpleTaskProcessor')

    def test_processor_error(self):
        Task.objects.create(
            processor_class='SomeMissingTaskProcessor',
            arguments={'args': [], 'kwargs': {}},
        )
        task_obj: Task = Task.objects.first()
        with self.assertRaises(WorkerClassNotFound):
            BaseTaskProcessor.get_processor_class(task_obj.processor_class)

    def test_run_from_model(self):
        value = 10
        SimpleTaskProcessor(value).delay()
        result = Task.objects.first().run()
        self.assertEqual(result, value)


class TestTaskModel(TestCase):
    def setUp(self) -> None:
        for i in range(10):
            SimpleTaskProcessor(i).delay()

    def test_task_verbose_name(self):
        new_task = Task.objects.get_new_tasks(1).first()
        self.assertEqual(
            str(new_task),
            "SimpleTaskProcessor ({'args': [0], 'kwargs': {}}) - New",
        )

    def test_get_new_tasks(self):
        new_tasks = Task.objects.get_new_tasks()
        self.assertEqual(len(new_tasks), 10)
        for task in Task.objects.all()[:5]:
            task.complete()
        new_tasks = Task.objects.get_new_tasks()
        self.assertEqual(len(new_tasks), 5)

    def test_get_new_tasks_with_count(self):
        new_tasks = Task.objects.get_new_tasks(5)
        self.assertEqual(len(new_tasks), 5)

    def test_select_for_processing(self):
        tasks = Task.objects.select_for_process(5)
        for task in tasks:
            task.refresh_from_db()
        self.assertTrue(all([task.status == Task.STATUS_IN_PROCESS for task in tasks]))
        self.assertEqual(len(tasks), 5)

    def test_task_complete(self):
        task = Task.objects.get_new_tasks().first()
        task.complete()
        self.assertEqual(task.status, Task.STATUS_FINISHED)

    def test_task_fail(self):
        exception_text = 'Some exception text'
        task = Task.objects.get_new_tasks().first()
        task.fail(Exception(exception_text))
        self.assertEqual(task.status, Task.STATUS_ERROR)
        self.assertEqual(task.extra, {'message': exception_text})
