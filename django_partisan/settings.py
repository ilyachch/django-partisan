import multiprocessing as mp

from django.conf import settings

MIN_QUEUE_SIZE = getattr(settings, 'MIN_QUEUE_SIZE', 2)
MAX_QUEUE_SIZE = getattr(settings, 'MAX_QUEUE_SIZE', 10)
TASKS_BEFORE_CLEANUP = getattr(settings, 'TASKS_BEFORE_CLEANUP', 50)
WORKERS_COUNT = getattr(settings, 'WORKERS_COUNT', mp.cpu_count())
