import datetime
import logging
import multiprocessing as mp
import os
import signal
import sys
import time
from queue import Empty
from typing import Any, List

import setproctitle
from django import db
from django.core.management import BaseCommand

from django_partisan.models import Task
from django_partisan import settings

logger = logging.getLogger(__name__)

running = False


def worker_subprocess(tasks_queue: mp.Queue,) -> None:
    logger.info("Parser started")
    setproctitle.setproctitle("background_worker/worker")
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    db.connections.close_all()

    # noinspection PyBroadException
    try:
        while True:
            try:
                task = tasks_queue.get(timeout=5)
                if task is None:
                    return
            except Empty:
                if os.getppid() == 1:  # validate parent
                    exit(0)
                continue

            try:
                task.run()
            except Exception as err:
                task.fail(err)
                raise
            finally:
                db.connections.close_all()
    except Exception as err:
        logger.exception('got exception ({}), exiting'.format(str(err)))


def exit_func(sig_num: int, _: Any) -> None:
    global running
    logger.info("Killed with %s. Exiting...\n", sig_num)
    signal.signal(signal.SIGTERM, exit_func)
    signal.signal(signal.SIGINT, exit_func)
    running = False


class Command(BaseCommand):
    def __init__(self) -> None:
        self.queue: mp.Queue = mp.Queue()
        self.workers: List[mp.Process] = []

        self.cleanup_counter = 0
        self.add2queue = True

        self.min_queue_size = settings.MIN_QUEUE_SIZE
        self.max_queue_size = settings.MAX_QUEUE_SIZE
        self.tasks_before_cleanup = settings.TASKS_BEFORE_CLEANUP
        self.workers_count = settings.WORKERS_COUNT
        super(Command, self).__init__()

    def add_arguments(self, parser) -> None:  # type: ignore
        parser.add_argument('--min_queue_size')

    def handle(self, *args: Any, **options: Any) -> None:
        global running

        signal.signal(signal.SIGTERM, exit_func)
        signal.signal(signal.SIGINT, exit_func)
        logger.info("Starting background parser")

        now = datetime.datetime.now()

        db.connections.close_all()
        setproctitle.setproctitle("background_worker/parent")

        running = True

        while running:
            # noinspection PyBroadException
            try:
                self.manage_workers()
                self.manage_queue()
            except db.Error as err:
                logger.warning("Database error: %s", err)
                db.connections.close_all()
            except Exception as err:
                logger.exception("unexpected error: %s", err)
                db.connections.close_all()
                # logger.warning("unexpected error, going to restart")
                # running = False

        self.clear_queue()

        self.stop_workers()
        logger.info("Ready to exit, active_children: %r", mp.active_children())
        logger.info("Exit after %d seconds", (datetime.datetime.now() - now).seconds)
        sys.exit()

    def create_workers(self) -> None:
        for _ in range(self.workers_count):
            p = mp.Process(target=worker_subprocess, args=(self.queue,))
            p.start()
            self.workers.append(p)

    def manage_workers(self) -> None:
        nothing_to_do = True
        qsize = self.queue.qsize()
        if not self.add2queue and qsize <= self.min_queue_size:
            self.add2queue = True
        if self.add2queue and qsize < self.max_queue_size:
            self.add2queue = False

            task_objs = Task.objects.select_for_process(self.max_queue_size - qsize)

            if len(task_objs) > 0:
                nothing_to_do = False
                for task_obj in task_objs:
                    self.queue.put(task_obj)
                logger.info("Added to queue %d tasks", len(task_objs))
        if nothing_to_do:
            time.sleep(2)

    def manage_queue(self) -> None:
        # cleanup DB - close database connections periodically to clean Django ORM requests list in memory
        self.cleanup_counter += 1
        if self.cleanup_counter >= self.tasks_before_cleanup:
            db.connections.close_all()
            self.cleanup_counter = 0
            for i in range(len(self.workers)):  # check children
                if not self.workers[i].is_alive():
                    self.workers[i].join()
                    self.workers[i] = mp.Process(
                        target=worker_subprocess, args=(self.queue,)
                    )
                    self.workers[i].start()
                    logger.warning("watchdog: worker#%d lost in space, restarted", i)

    def clear_queue(self) -> None:
        if not self.queue.empty():
            logger.info("Flush tasks queue")
            flush_cnt = 0
            while not self.queue.empty():
                # noinspection PyBroadException
                try:
                    self.queue.get(block=False)
                    flush_cnt += 1
                except Empty:
                    break
                except Exception:
                    break
            logger.info("Flushed %d requests", flush_cnt)

    def stop_workers(self,) -> None:
        logger.info("Stop workers")
        for _ in self.workers:
            self.queue.put(None)
        for d in self.workers:
            if d.is_alive():
                logger.info("Awaiting for %d to stop", d.pid)
                d.join(2)
                logger.info("Awaiting for %d ended", d.pid)
                if d.is_alive():
                    logger.warning("Have to kill process due to restart request.")
                    d.terminate()
                    time.sleep(0.2)
            mp.active_children()
        self.queue.close()
