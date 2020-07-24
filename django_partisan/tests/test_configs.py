from django.test import TestCase
from django.utils import timezone

from django_partisan.settings import get_queue_settings
from django_partisan.config import const
from django_partisan.config.processor_configs import ErrorsHandleConfig, PostponeConfig
from django_partisan.exceptions import PostponeTask

settings = get_queue_settings()


class TestErrorsHandleConfig(TestCase):
    normal_config = {
        'retry_on_errors': (ValueError, TabError),
        'retries_count': 2,
        'retry_pause': 5,
        'retry_pause_strategy': const.DELAY_STRATEGY_CONSTANT,
    }

    def test_validation_empty_errors(self):
        with self.assertRaises(ValueError):
            ErrorsHandleConfig(**{**self.normal_config, 'retry_on_errors': []})

    def test_validation_not_errors(self):
        with self.assertRaises(ValueError):
            ErrorsHandleConfig(
                **{**self.normal_config, 'retry_on_errors': ['not exception']}
            )

    def test_validation_zero_retries(self):
        with self.assertRaises(ValueError):
            ErrorsHandleConfig(**{**self.normal_config, 'retries_count': 0})

    def test_validation_negative_retries(self):
        with self.assertRaises(ValueError):
            ErrorsHandleConfig(**{**self.normal_config, 'retries_count': -1})

    def test_validation_negative_pause(self):
        with self.assertRaises(ValueError):
            ErrorsHandleConfig(**{**self.normal_config, 'retry_pause': -1})

    def test_validation_bad_strategy(self):
        with self.assertRaises(ValueError):
            ErrorsHandleConfig(
                **{**self.normal_config, 'retry_pause_strategy': 'not strategy id'}
            )

    def test_config_should_be_retried(self):
        config = ErrorsHandleConfig(**self.normal_config)
        self.assertTrue(config.shoud_be_retried(1))
        self.assertFalse(config.shoud_be_retried(3))

    def test_config_get_new_datetime_for_delay_constant(self):
        config = ErrorsHandleConfig(**self.normal_config)
        now = timezone.now().timestamp()
        new_date = config.get_new_datetime_for_retry(2)
        self.assertEqual(round(new_date.timestamp() - now), 5)

    def test_config_get_new_datetime_for_delay_incremental(self):
        config = ErrorsHandleConfig(
            **{
                **self.normal_config,
                'retry_pause_strategy': const.DELAY_STRATEGY_INCREMENTAL,
            }
        )
        now = timezone.now().timestamp()
        new_date = config.get_new_datetime_for_retry(2)
        self.assertEqual(round(new_date.timestamp() - now), 10)

    def test_config_get_new_datetime_for_delay_error(self):
        config = ErrorsHandleConfig(
            **{
                **self.normal_config,
                'retry_pause_strategy': const.DELAY_STRATEGY_INCREMENTAL,
            }
        )
        now = timezone.now().timestamp()
        with self.assertRaises(RuntimeError):
            new_date = config.get_new_datetime_for_retry(5)


class TestPostponeConfig(TestCase):
    def test_get_new_datetime_for_postpone_not_set_in_signal(self):
        config = PostponeConfig(max_postpones=10)
        now = timezone.now().timestamp()
        new_datetime_for_postpone = config.get_new_datetime_for_postpone(
            PostponeTask()
        ).timestamp()
        self.assertEqual(
            round(new_datetime_for_postpone - now),
            settings.DEFAULT_POSTPONE_DELAY_SECONDS,
        )

    def test_get_new_datetime_for_postpone_set_in_signal(self):
        config = PostponeConfig(max_postpones=10)
        now = timezone.now().timestamp()
        new_datetime_for_postpone = config.get_new_datetime_for_postpone(
            PostponeTask(10)
        ).timestamp()
        self.assertEqual(round(new_datetime_for_postpone - now), 10)
