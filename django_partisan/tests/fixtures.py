from django_partisan.config.processor_configs import ErrorsHandleConfig, PostponeConfig
from django_partisan.exceptions import PostponeTask
from django_partisan.processor import BaseTaskProcessor


class TestTaskProcessor(BaseTaskProcessor):
    def run(self):
        return self.args[0]


class ConfiguredTestTaskProcessor(BaseTaskProcessor):
    RETRY_ON_ERROR_CONFIG = ErrorsHandleConfig(
        retry_on_errors=[ValueError,], retries_count=5, retry_pause=0,
    )

    def run(self):
        return self.args[0]


class ConfiguredFailingTestTaskProcessor(BaseTaskProcessor):
    RETRY_ON_ERROR_CONFIG = ErrorsHandleConfig(
        retry_on_errors=[ValueError,], retries_count=5, retry_pause=0,
    )

    def run(self):
        raise ValueError()


class PostponableTestTaskProcessor(BaseTaskProcessor):
    def run(self):
        raise PostponeTask(15)


class PostponableConfiguredTestTaskProcessor(BaseTaskProcessor):
    POSTPONE_CONFIG = PostponeConfig(max_postpones=5)

    def run(self):
        raise PostponeTask(15)
