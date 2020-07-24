from unittest.mock import patch, Mock

from django.core.management import call_command
from django.test import TestCase


@patch('django_partisan.management.commands.start_partisan.WorkersManager')
class TestCommand(TestCase):
    command_name = 'start_partisan'

    min_queue_size = 'min_queue_size'
    max_queue_size = 'max_queue_size'
    checks_before_cleanup = 'checks_before_cleanup'
    workers_count = 'workers_count'
    sleep_delay_seconds = 'sleep_delay_seconds'

    def test_default_launch(self, manager_mock):
        manager_instance_mock = Mock()
        manager_mock.return_value = manager_instance_mock
        call_command(self.command_name)
        manager_mock.assert_called_once()
        manager_instance_mock.run_partisan.assert_called_once()

    def test_custom_launch(self, manager_mock):
        call_command(
            self.command_name,
            f'--{self.min_queue_size}=1',
            f'--{self.max_queue_size}=2',
            f'--{self.checks_before_cleanup}=10',
            f'--{self.workers_count}=1',
            f'--{self.sleep_delay_seconds}=1',
        )
        manager_mock.assert_called_with(
            **{
                'queue_name': 'default',
                self.min_queue_size: 1,
                self.max_queue_size: 2,
                self.checks_before_cleanup: 10,
                self.workers_count: 1,
                self.sleep_delay_seconds: 1,
            }
        )
