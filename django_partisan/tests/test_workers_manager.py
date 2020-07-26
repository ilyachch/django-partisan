from queue import Empty
from unittest.mock import patch, Mock, MagicMock, call, ANY

from django.db import DatabaseError
from django.test import TestCase

from django_partisan.workers_manager import WorkersManager

is_alive_return_value = 'is_alive.return_value'
is_alive_side_effect = 'is_alive.side_effect'


@patch('django_partisan.workers_manager.logger')
@patch('django_partisan.workers_manager.Task')
@patch('django_partisan.workers_manager.time')
@patch('django_partisan.workers_manager.db')
@patch('django_partisan.workers_manager.mp')
@patch('django_partisan.workers_manager.Worker')
class TestWorkersManager(TestCase):
    @patch('django_partisan.workers_manager.sys')
    @patch.object(WorkersManager, 'stop_workers')
    @patch.object(WorkersManager, 'flush_queue')
    @patch.object(WorkersManager, 'manage_workers')
    @patch.object(WorkersManager, 'manage_queue')
    @patch.object(WorkersManager, 'create_workers')
    def test_partisan(
        self,
        create_workers_mock,
        manage_queue_mock,
        manage_workers_mock,
        flush_queue_mock,
        stop_workers_mock,
        sys_mock,
        worker_mock,
        mp_mock,
        db_mock,
        time_mock,
        task_mock,
        logger_mock,
    ):
        manage_queue_mock.side_effect = [DatabaseError, None]
        manage_workers_mock.side_effect = ValueError
        mp_mock.active_children.return_value = 10
        manager = WorkersManager()
        manager.run_partisan()
        logger_mock.exception.assert_has_calls(
            [call("Database error"), call("Unexpected error"),]
        )
        logger_mock.info.assert_has_calls(
            [
                call("Ready to exit, active_children: %r", 10),
                call("Exit after %d seconds", ANY),
            ]
        )
        create_workers_mock.assert_called()
        manage_queue_mock.assert_called()
        manage_workers_mock.assert_called()
        flush_queue_mock.assert_called_once()
        stop_workers_mock.assert_called_once()
        sys_mock.exit.assert_called_once()
        task_mock.objects.reset_tasks_to_initial_status.assert_called_once()

    def test_bad_settings(
        self, worker_mock, mp_mock, db_mock, time_mock, task_mock, logger_mock
    ):
        with self.assertRaises(RuntimeError):
            WorkersManager(queue_name='some_bad_queue_name')

    def test_create_workers(
        self, worker_mock, mp_mock, db_mock, time_mock, task_mock, logger_mock
    ):
        test_workers_count = 4
        manager = WorkersManager(workers_count=test_workers_count)
        manager.create_workers()
        self.assertEqual(worker_mock.call_count, test_workers_count)

    def test_manage_queue_queue_is_full(
        self, worker_mock, mp_mock, db_mock, time_mock, task_mock, logger_mock
    ):
        manager = WorkersManager(workers_count=4, min_queue_size=4)
        queue_mock = Mock()
        queue_mock.qsize = MagicMock(return_value=5)
        manager.queue = queue_mock
        manager.manage_queue()
        time_mock.sleep.assert_called_once_with(2)

    def test_manage_queue_queue_to_be_filled(
        self, worker_mock, mp_mock, db_mock, time_mock, task_mock, logger_mock
    ):
        manager = WorkersManager(workers_count=4, min_queue_size=4, max_queue_size=8)
        queue_mock = Mock()
        queue_mock.qsize = MagicMock(return_value=2)
        task_mock.objects.select_for_process = MagicMock(
            return_value=[1, 2, 3, 4, 5, 6]
        )
        manager.queue = queue_mock
        manager.manage_queue()
        task_mock.objects.select_for_process.assert_called_with(6, 'default')
        self.assertEqual(queue_mock.put.call_count, 6)
        time_mock.sleep.assert_not_called()

    def test_manage_workers(
        self, worker_mock, mp_mock, db_mock, time_mock, task_mock, logger_mock
    ):
        manager = WorkersManager(workers_count=4,)
        manager.manage_workers()
        db_mock.asser_not_called()

    def test_manage_workers_all_alive(
        self, worker_mock, mp_mock, db_mock, time_mock, task_mock, logger_mock
    ):
        manager = WorkersManager(workers_count=4,)
        manager.workers = [
            Mock(**{is_alive_return_value: True}),
            Mock(**{is_alive_return_value: True}),
            Mock(**{is_alive_return_value: True}),
            Mock(**{is_alive_return_value: True}),
        ]
        manager.cleanup_counter = 50
        manager.manage_workers()
        db_mock.asser_was_called()
        mp_mock.Process.assert_not_called()

    def test_manage_workers_half_dead(
        self, worker_mock, mp_mock, db_mock, time_mock, task_mock, logger_mock
    ):
        manager = WorkersManager(workers_count=4,)
        manager.workers = [
            Mock(**{is_alive_return_value: True}),
            Mock(**{is_alive_return_value: False}),
            Mock(**{is_alive_return_value: True}),
            Mock(**{is_alive_return_value: False}),
        ]
        manager.cleanup_counter = 50
        manager.manage_workers()
        db_mock.asser_was_called()
        self.assertEqual(worker_mock.call_count, 2)
        manager.workers[0].start.assert_not_called()
        manager.workers[1].start.assert_called()
        manager.workers[2].start.assert_not_called()
        manager.workers[3].start.assert_called()

    def test_flush_empty_queue(
        self, worker_mock, mp_mock, db_mock, time_mock, task_mock, logger_mock
    ):
        manager = WorkersManager()
        queue_mock = Mock()
        queue_mock.empty = MagicMock(return_value=True)
        manager.queue = queue_mock
        manager.flush_queue()
        logger_mock.info.asser_not_called()
        queue_mock.empty.assert_called()

    def test_flush_queue(
        self, worker_mock, mp_mock, db_mock, time_mock, task_mock, logger_mock
    ):
        manager = WorkersManager()
        queue_mock = Mock()
        queue_mock.empty.side_effect = [False, False, True]
        manager.queue = queue_mock
        manager.flush_queue()
        logger_mock.info.assert_has_calls(
            [call("Flush tasks queue"), call("Flushed %d tasks", 1),]
        )

    def test_flush_queue_empty(
        self, worker_mock, mp_mock, db_mock, time_mock, task_mock, logger_mock
    ):
        manager = WorkersManager()
        queue_mock = Mock()
        queue_mock.empty.return_value = False
        queue_mock.get.side_effect = Empty
        manager.queue = queue_mock
        manager.flush_queue()
        logger_mock.exception.assert_has_calls(
            [call('Queue is already empty'),]
        )

    def test_flush_queue_error(
        self, worker_mock, mp_mock, db_mock, time_mock, task_mock, logger_mock
    ):
        manager = WorkersManager()
        queue_mock = Mock()
        queue_mock.empty.return_value = False
        queue_mock.get.side_effect = ValueError
        manager.queue = queue_mock
        manager.flush_queue()
        logger_mock.exception.assert_has_calls(
            [call('Got error while flushing queue'),]
        )

    def test_stop_workers(
        self, worker_mock, mp_mock, db_mock, time_mock, task_mock, logger_mock
    ):
        manager = WorkersManager(workers_count=3)
        manager.queue = Mock()
        worker_to_terminate = Mock(**{is_alive_return_value: True})
        worker_dead = Mock(**{is_alive_return_value: False})
        worker_normally_finished = Mock(**{is_alive_side_effect: [True, False]})
        manager.workers = [
            worker_to_terminate,
            worker_dead,
            worker_normally_finished,
        ]
        manager.stop_workers()
        worker_to_terminate.join.assert_called_once()
        worker_to_terminate.terminate.assert_called_once()
        worker_dead.join.assert_not_called()
        worker_dead.terminate.assert_not_called()
        worker_normally_finished.join.assert_called_once()
        worker_normally_finished.terminate.assert_not_called()
