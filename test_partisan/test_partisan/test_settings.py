INSTALLED_APPS = [
    'django_partisan',
    'test_app',
]

PARTISAN_CONFIG = {
    'default': {
        'MIN_QUEUE_SIZE': 2,
        'MAX_QUEUE_SIZE': 10,
        'CHECKS_BEFORE_CLEANUP': 50,
        'WORKERS_COUNT': 2,
        'SLEEP_DELAY_SECONDS': 2,
        'TASKS_PER_WORKER_INSTANCE': None,
        'DELETE_TASKS_ON_COMPLETE': False,
        'DEFAULT_POSTPONE_DELAY_SECONDS': 2,
        'DEFAULT_POSTPONES_COUNT': 2
    }
}
