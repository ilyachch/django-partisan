import logging
import multiprocessing as mp
import os
import signal
from queue import Empty
from typing import Optional, TYPE_CHECKING

import setproctitle
from django import db

from django_partisan.settings import PARTISAN_CONFIG
from django_partisan.settings.const import DEFAULT_QUEUE_NAME

if TYPE_CHECKING:
    from django_partisan.models import Task

logger = logging.getLogger(__name__)


class Worker(mp.Process):
    def __init__(
        self,
        queue: mp.Queue,
        queue_name: str = DEFAULT_QUEUE_NAME,
        tasks_before_death: Optional[int] = None,
    ) -> None:
        super().__init__()
        self.queue = queue
        self.queue_name = queue_name
        self.settings = PARTISAN_CONFIG.get(self.queue_name)
        if not self.settings:
            raise RuntimeError(f'No settings for queue "{queue_name}" found!')
        self.tasks_before_death = (
            tasks_before_death or self.settings.TASKS_PER_WORKER_INSTANCE
        )
        self.tasks_processed = 0

    def run(self) -> None:
        logger.info("Worker started")
        setproctitle.setproctitle("partisan/worker")
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        try:
            while self.shoud_process_tasks():
                try:
                    task: Optional['Task'] = self.queue.get(timeout=5)
                    if task is None:
                        logger.info('Worker stopped')
                        return
                except Empty:  # pragma: no cover
                    if os.getppid() == 1:  # validate parent
                        exit(0)
                    continue

                try:
                    task.run()
                    self.tasks_processed += 1
                    task.complete()
                except Exception as err:
                    task.fail(err)
                    raise
            else:
                logger.info(
                    'Processed %d of %d tasks. Exiting',
                    self.tasks_processed,
                    self.tasks_before_death,
                )
        except Exception:
            logger.exception('Got exception, exiting')

    def shoud_process_tasks(self) -> bool:
        if self.tasks_before_death is None:
            return True
        return self.tasks_processed < self.tasks_before_death
