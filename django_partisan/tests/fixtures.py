from django_partisan.config.configs import ErrorsHandleConfig
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
