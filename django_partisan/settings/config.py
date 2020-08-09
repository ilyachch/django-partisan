from django.conf import settings

from django_partisan.settings import const
from django_partisan.settings.settings_models import QueueSettings
from django_partisan.settings.utils import get_merged_config
from django_partisan.settings import defaults

PARTISAN_CONFIG = {
    const.DEFAULT_QUEUE_NAME: QueueSettings(
        **get_merged_config(
            {
                const.MIN_QUEUE_SIZE: getattr(
                    settings, const.MIN_QUEUE_SIZE, defaults.MIN_QUEUE_SIZE
                ),
                const.MAX_QUEUE_SIZE: getattr(
                    settings, const.MAX_QUEUE_SIZE, defaults.MAX_QUEUE_SIZE
                ),
                const.CHECKS_BEFORE_CLEANUP: getattr(
                    settings,
                    const.CHECKS_BEFORE_CLEANUP,
                    defaults.CHECKS_BEFORE_CLEANUP,
                ),
                const.WORKERS_COUNT: getattr(
                    settings, const.WORKERS_COUNT, defaults.WORKERS_COUNT
                ),
                const.SLEEP_DELAY_SECONDS: getattr(
                    settings, const.SLEEP_DELAY_SECONDS, defaults.SLEEP_DELAY_SECONDS
                ),
                const.TASKS_PER_WORKER_INSTANCE: getattr(
                    settings,
                    const.TASKS_PER_WORKER_INSTANCE,
                    defaults.TASKS_PER_WORKER_INSTANCE,
                ),
                const.DELETE_TASKS_ON_COMPLETE: getattr(
                    settings,
                    const.DELETE_TASKS_ON_COMPLETE,
                    defaults.DELETE_TASKS_ON_COMPLETE,
                ),
                const.DEFAULT_POSTPONE_DELAY_SECONDS: getattr(
                    settings,
                    const.DEFAULT_POSTPONE_DELAY_SECONDS,
                    defaults.DEFAULT_POSTPONE_DELAY_SECONDS,
                ),
                const.DEFAULT_POSTPONES_COUNT: getattr(
                    settings,
                    const.DEFAULT_POSTPONES_COUNT,
                    defaults.DEFAULT_POSTPONES_COUNT,
                ),
            }
        )
    )
}

PARTISAN_CONFIG.update(
    {
        queue_name: QueueSettings(**get_merged_config(queue_config))
        for queue_name, queue_config in getattr(settings, 'PARTISAN_CONFIG', {}).items()
    }
)
