from typing import Optional

from pydantic import BaseModel, validator


class QueueSettings(BaseModel):
    MIN_QUEUE_SIZE: int
    MAX_QUEUE_SIZE: int
    CHECKS_BEFORE_CLEANUP: int
    WORKERS_COUNT: int
    SLEEP_DELAY_SECONDS: int
    TASKS_PER_WORKER_INSTANCE: Optional[int]
    DELETE_TASKS_ON_COMPLETE: bool = False
    DEFAULT_POSTPONE_DELAY_SECONDS: int
    DEFAULT_POSTPONES_COUNT: Optional[int]

    @validator(
        'MIN_QUEUE_SIZE',
        'MAX_QUEUE_SIZE',
        'CHECKS_BEFORE_CLEANUP',
        'WORKERS_COUNT',
        'SLEEP_DELAY_SECONDS',
        'TASKS_PER_WORKER_INSTANCE',
        'DEFAULT_POSTPONE_DELAY_SECONDS',
        'DEFAULT_POSTPONES_COUNT',
    )
    def must_be_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return None
        if v < 0:
            raise ValueError('Value should be positive integer')
        return v
