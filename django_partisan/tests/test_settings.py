from django_partisan.settings.settings_models import QueueSettings
from django_partisan.settings import get_queue_settings
from django.test import TestCase


class TestQueueSettings(TestCase):
    valid_settings = dict(
        MIN_QUEUE_SIZE=10,
        MAX_QUEUE_SIZE=20,
        CHECKS_BEFORE_CLEANUP=50,
        WORKERS_COUNT=5,
        SLEEP_DELAY_SECONDS=5,
        DELETE_TASKS_ON_COMPLETE=False,
        DEFAULT_POSTPONE_DELAY_SECONDS=5,
        DEFAULT_POSTPONES_COUNT=None,
    )

    def test_valid_settings(self):
        queue_settings = QueueSettings(**self.valid_settings)

    def test_invalid_settings(self):
        invalid_settings = {
            **self.valid_settings,
            'MIN_QUEUE_SIZE': -10,
        }
        with self.assertRaises(ValueError):
            QueueSettings(**invalid_settings)

    def test_get_queue_settings(self):
        self.assertIsNotNone(get_queue_settings())

    def test_get_queue_settings_bad_queue(self):
        with self.assertRaises(RuntimeError):
            get_queue_settings('some_bad_queue_name')
