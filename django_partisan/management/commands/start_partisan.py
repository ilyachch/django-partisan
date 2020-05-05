import logging
from typing import Any

from django.core.management import BaseCommand

from django_partisan.workers_manager import WorkersManager

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser) -> None:  # type: ignore
        parser.add_argument(
            '--min_queue_size',
            type=int,
            help='Count of tasks, indicating that queue should be refilled',
        )
        parser.add_argument(
            '--max_queue_size',
            type=int,
            help='Count of tasks, that should be in queue after fill and refill',
        )
        parser.add_argument(
            '--checks_before_cleanup',
            type=int,
            help='Count of workers checks, after that should be '
            'performed db connections closing',
        )
        parser.add_argument(
            '--workers_count',
            type=int,
            help='Count of workers, that should be spanwed for this instance',
        )
        parser.add_argument(
            '--sleep_delay_seconds',
            type=int,
            help='Time in seconds, to sleep bef††ore the next tasks presence check',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        manager = WorkersManager(
            min_queue_size=options.get('min_queue_size'),
            max_queue_size=options.get('max_queue_size'),
            checks_before_cleanup=options.get('checks_before_cleanup'),
            workers_count=options.get('workers_count'),
            sleep_delay_seconds=options.get('sleep_delay_seconds'),
        )
        manager.run_partisan()
