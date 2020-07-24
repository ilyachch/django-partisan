from django_partisan.settings.config import PARTISAN_CONFIG
from django_partisan.settings.const import DEFAULT_QUEUE_NAME

__all__ = ['PARTISAN_CONFIG', 'get_queue_settings']

from django_partisan.settings.settings_models import QueueSettings


def get_queue_settings(queue_name: str = DEFAULT_QUEUE_NAME) -> QueueSettings:
    config = PARTISAN_CONFIG.get(queue_name)
    if config is None:
        raise RuntimeError(f'No config for "{DEFAULT_QUEUE_NAME}" queue found!')
    return config
