import multiprocessing as mp

from django.conf import settings

MIN_QUEUE_SIZE = getattr(settings, 'MIN_QUEUE_SIZE', 2)
MAX_QUEUE_SIZE = getattr(settings, 'MAX_QUEUE_SIZE', 10)
CHECKS_BEFORE_CLEANUP = getattr(settings, 'CHECKS_BEFORE_CLEANUP', 50)
WORKERS_COUNT = getattr(settings, 'WORKERS_COUNT', mp.cpu_count())
SLEEP_DELAY_SECONDS = getattr(settings, 'SLEEP_DELAY_SECONDS', 2)
