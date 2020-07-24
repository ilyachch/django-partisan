import logging
from unittest.mock import patch, call, Mock, MagicMock

from django.test import TestCase

from django_partisan.worker import Worker


class TestBackgroundWorker(TestCase):
    def setUp(self):
        self.logger = logging.getLogger('django_partisan.worker')

    def test_bad_settings(self):
        queue = Mock()
        with self.assertRaises(RuntimeError):
            Worker(queue, 'some_bad_queue_name')

    def test_none_in_queue(self):
        queue = Mock()
        queue.get = MagicMock(return_value=None)
        with patch.object(self.logger, 'info') as logger_info_mock:
            Worker(queue).run()
            logger_info_mock.assert_has_calls(
                [call('Worker started'), call('Worker stopped'),]
            )

    def test_bad_task(self):
        task_mock = MagicMock(**{'run.side_effect': ValueError})
        queue = Mock()
        queue.get.return_value = task_mock
        with patch.object(self.logger, 'exception') as logger_mock:
            Worker(queue).run()
            logger_mock.assert_has_calls([call('Got exception, exiting')])
        task_mock.run.assert_called()
        task_mock.fail.assert_called()

    def test_selfkill(self):
        task_mock = MagicMock()
        queue = Mock()
        queue.get.return_value = task_mock
        with patch.object(self.logger, 'info') as logger_mock:
            Worker(queue, tasks_before_death=5).run()
            logger_mock.assert_has_calls(
                [call('Processed %d of %d tasks. Exiting', 5, 5)]
            )
        self.assertEqual(queue.get.call_count, 5)
