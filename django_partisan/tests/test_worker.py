import logging
from typing import Any
from unittest.mock import patch, call, Mock, MagicMock

from django.test import TestCase

from django_partisan.models import Task
from django_partisan.processor import BaseTaskProcessor
from django_partisan.worker import worker_subprocess


class TestTask(BaseTaskProcessor):
    def run(self) -> Any:
        raise ValueError()


class TestBackgroundWorker(TestCase):
    def setUp(self):
        self.logger = logging.getLogger('django_partisan.worker')

    def test_none_in_queue(self):
        queue = Mock()
        queue.get = MagicMock(return_value=None)
        with patch.object(self.logger, 'info') as logger_info_mock:
            worker_subprocess(tasks_queue=queue)
            logger_info_mock.assert_has_calls(
                [call('Worker started'), call('Worker stopped'),]
            )

    def test_bad_task(self):
        TestTask().delay()
        task = Task.objects.first()
        queue = Mock()
        queue.get = MagicMock(return_value=task)
        with patch.object(self.logger, 'exception') as logger_mock:
            worker_subprocess(queue)
            logger_mock.assert_has_calls([call('got exception (%s), exiting', '')])
