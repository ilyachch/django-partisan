from typing import Any, Dict

from django_partisan.settings import const, defaults


def get_merged_config(config: Dict[str, Any]) -> Dict[str, Any]:
    default_config = _get_default_config()
    default_config.update(config)
    return default_config


def _get_default_config() -> Dict[str, Any]:
    return {
        const.MIN_QUEUE_SIZE: defaults.MIN_QUEUE_SIZE,
        const.MAX_QUEUE_SIZE: defaults.MAX_QUEUE_SIZE,
        const.CHECKS_BEFORE_CLEANUP: defaults.CHECKS_BEFORE_CLEANUP,
        const.WORKERS_COUNT: defaults.WORKERS_COUNT,
        const.SLEEP_DELAY_SECONDS: defaults.SLEEP_DELAY_SECONDS,
        const.TASKS_PER_WORKER_INSTANCE: defaults.TASKS_PER_WORKER_INSTANCE,
        const.DELETE_TASKS_ON_COMPLETE: defaults.DELETE_TASKS_ON_COMPLETE,
        const.DEFAULT_POSTPONE_DELAY_SECONDS: defaults.DEFAULT_POSTPONE_DELAY_SECONDS,
        const.DEFAULT_POSTPONES_COUNT: defaults.DEFAULT_POSTPONES_COUNT,
    }
