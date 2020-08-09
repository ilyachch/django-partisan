import datetime
import logging
import multiprocessing as mp
import signal
import sys
import time
from queue import Empty
from typing import List, Any

import setproctitle
from django import db
from django.db import Error

from django_partisan.models import Task
from django_partisan.registry import initialize_processors
from django_partisan.settings import PARTISAN_CONFIG
from django_partisan.settings.const import DEFAULT_QUEUE_NAME
from django_partisan.worker import Worker
from django_partisan.utils import Queue  # type: ignore


logger = logging.getLogger(__name__)

running = False


def exit_func(sig_num: int, _: Any) -> None:  # pragma: no cover
    global running
    logger.info("Killed with %s. Exiting...\n", sig_num)
    signal.signal(signal.SIGTERM, exit_func)
    signal.signal(signal.SIGINT, exit_func)
    running = False


class WorkersManager:
    def __init__(
        self,
        *,
        queue_name: str = DEFAULT_QUEUE_NAME,
        min_queue_size: int = None,
        max_queue_size: int = None,
        checks_before_cleanup: int = None,
        workers_count: int = None,
        sleep_delay_seconds: int = None,
    ) -> None:
        self.queue: mp.Queue = Queue()
        self.workers: List[mp.Process] = []

        self.cleanup_counter = 0

        self.queue_name = queue_name
        self.settings = PARTISAN_CONFIG.get(queue_name)
        if not self.settings:
            raise RuntimeError(f'No settings for queue "{queue_name}" found!')

        self.min_queue_size = min_queue_size or self.settings.MIN_QUEUE_SIZE
        self.max_queue_size = max_queue_size or self.settings.MAX_QUEUE_SIZE
        self.checks_before_cleanup = (
            checks_before_cleanup or self.settings.CHECKS_BEFORE_CLEANUP
        )
        self.workers_count = workers_count or self.settings.WORKERS_COUNT
        self.sleep_delay_seconds = (
            sleep_delay_seconds or self.settings.SLEEP_DELAY_SECONDS
        )

    def run_partisan(self) -> None:
        global running

        signal.signal(signal.SIGTERM, exit_func)
        signal.signal(signal.SIGINT, exit_func)
        logger.info("Starting background parser")

        now = datetime.datetime.now()

        initialize_processors()

        db.connections.close_all()
        setproctitle.setproctitle("partisan/parent")

        running = True

        Task.objects.reset_tasks_to_initial_status()

        self.create_workers()

        while running:
            # noinspection PyBroadException
            try:
                self.manage_queue()
                self.manage_workers()
            except Error:
                logger.exception("Database error")
                db.connections.close_all()
            except Exception:
                logger.exception("Unexpected error")
                db.connections.close_all()
                break

        self.flush_queue()

        self.stop_workers()
        logger.info("Ready to exit, active_children: %r", mp.active_children())
        logger.info("Exit after %d seconds", (datetime.datetime.now() - now).seconds)
        sys.exit()

    def create_workers(self) -> None:
        for _ in range(self.workers_count):
            p = Worker(self.queue, self.queue_name)
            p.start()
            self.workers.append(p)

    def manage_queue(self) -> None:
        """Fill up queue if queue size is less than min_queue_size
        If queue is filled, sleep until the next check
        """
        nothing_to_do = True
        qsize = self.queue.qsize()
        if qsize <= self.min_queue_size:
            task_objs = Task.objects.select_for_process(
                self.max_queue_size - qsize, self.queue_name
            )
            if len(task_objs) > 0:
                nothing_to_do = False
                for task_obj in task_objs:
                    self.queue.put(task_obj)
                logger.info("Added to queue %d tasks", len(task_objs))
        if nothing_to_do:
            time.sleep(self.sleep_delay_seconds)

    def manage_workers(self) -> None:
        """Checks for workers processes and restarts them, if failed
        Clears database connections every TASKS_BEFORE_CLEANUP times
        """
        self.cleanup_counter += 1
        if self.cleanup_counter >= self.checks_before_cleanup:
            # db.connections.close_all()
            self.cleanup_counter = 0
            for i in range(len(self.workers)):  # check children
                if not self.workers[i].is_alive():
                    self.workers[i].join()
                    self.workers[i] = Worker(self.queue, self.queue_name)
                    self.workers[i].start()
                    logger.warning("watchdog: worker#%d lost in space, restarted", i)

    def flush_queue(self) -> None:
        if not self.queue.empty():
            logger.info("Flush tasks queue")
            flush_cnt = 0
            while not self.queue.empty():
                # noinspection PyBroadException
                try:
                    self.queue.get(block=False)
                    flush_cnt += 1
                except Empty:
                    logger.exception('Queue is already empty')
                    break
                except Exception:
                    logger.exception('Got error while flushing queue')
                    break
            logger.info("Flushed %d tasks", flush_cnt)

    def stop_workers(self,) -> None:
        logger.info("Stop workers")
        for _ in self.workers:
            self.queue.put(None)
        for w in self.workers:
            if w.is_alive():
                logger.info("Awaiting for %d to stop", w.pid)
                w.join(2)
                logger.info("Awaiting for %d ended", w.pid)
                if w.is_alive():
                    logger.warning("Have to kill process due to restart request.")
                    w.terminate()
                    time.sleep(0.2)
        self.queue.close()
