from importlib import import_module

from django.apps import apps

TASKS_MODULE_NAME = 'partisan_tasks'


def initialize_processors() -> None:
    installed_apps = apps.get_app_configs()
    for installed_app in installed_apps:
        try:
            import_module(f'{installed_app.name}.{TASKS_MODULE_NAME}')
        except ModuleNotFoundError:
            pass
