import logging
import multiprocessing as mp
import os
import signal
from queue import Empty

import setproctitle
from django import db

logger = logging.getLogger(__name__)


def worker_subprocess(tasks_queue: mp.Queue,) -> None:
    logger.info("Worker started")
    setproctitle.setproctitle("partisan/worker")
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # noinspection PyBroadException
    try:
        while True:
            try:
                task = tasks_queue.get(timeout=5)
                if task is None:
                    logger.info('Worker stopped')
                    return
            except Empty:  # pragma: no cover
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
        logger.exception('got exception (%s), exiting', str(err))
