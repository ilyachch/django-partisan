[![codecov](https://codecov.io/gh/ilyachch/django-partisan/branch/master/graph/badge.svg)](https://codecov.io/gh/ilyachch/django-partisan)

[![PyPI version](https://badge.fury.io/py/django-partisan.svg)](https://pypi.org/project/django-partisan/)
[![Downloads](https://pepy.tech/badge/django-partisan)](https://pepy.tech/project/django-partisan)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/django-partisan.svg)](https://pypi.org/project/django-partisan/)

# django-backgroud-tasks-framework
Framework to allow creating background tasks in django without MQ

# Usage

## Requirements
Python versions: 3.6+

Django versions: 1.9+

## General usage
Install app with:
```
$ pip install django-partisan
```

Add it to your `INSTALLED_APPS`

Run migrate command:
```
$ python manage.py migrate
```

Write your task and register it:
```python
# partisan_tasks.py
from django_partisan.processor import BaseTaskProcessor
from django_partisan import registry


@registry.register
class MyProcessor(BaseTaskProcessor):
    PRIORITY = 5  # Optional, by default 10
    UNIQUE_FOR_PARAMS = True  # Optional, by default True

    def run(self):
        do_something(*self.args, **self.kwargs)

```

> Please note, that all tasks should be in module `partisan_tasks.py` in root of your application. 
> You can write them there or just import from your preferable place. 
> It's needed to make autodiscover available

And then put this task to queue:
```python
from partisan_tasks import MyProcessor


def do_something_and_postpone_task(*args, **kwargs):
    MyProcessor(args, kwargs).delay()

```

To start tasks processing you should start workers:

```
$ python manage.py start_partisan
``` 

## Advanced

### Postpone tasks

You can postpone task by raising special exception `PostponeTask`:

Also you can manage posponing delay by setting `DEFAULT_POSTPONE_DELAY_SECONDS` 
in your `settings.py` (by default - 5 seconds) or pass it to `PostponeTask`:
```python
from django_partisan.exceptions import PostponeTask

def do_something():
    raise PostponeTask(300)  # 5 minutes

```
It's possible to configure postponing rules for every single processor. 
Just define `POSTPONE_CONFIG` in your processor class as instance of `PostponeConfig`:
```python
from django_partisan.config.processor_configs import PostponeConfig
from django_partisan.processor import BaseTaskProcessor
from django_partisan import registry
from django_partisan.exceptions import PostponeTask

@registry.register
class MyProcessor(BaseTaskProcessor):
    POSTPONE_CONFIG = PostponeConfig(
        max_postpones=5
    )
    def run(self):
        do_something(*self.args, **self.kwargs)

def do_something(*args, **kwargs):
    raise PostponeTask(300)  # 5 minutes

```

With such configuration the task will be postponed for 5 times and, if it will be tried to be postponed one more time,
`MaxPostponesReached` exception will be rised.

Also you can globally set maximum postpones in settings with `DEFAULT_POSTPONES_COUNT` in `settings.py` (by default - 15).
It was made to make task processing finite. If you want to make your task be processed forever, until they would be finished,
you can set it to `None`, but it is dangerous.

### Errors handling
You can set for task processor special config, that is managing, how to handle errors:
```python
from django_partisan.config.processor_configs import ErrorsHandleConfig
from django_partisan.config import const
from django_partisan.processor import BaseTaskProcessor
from django_partisan import registry

@registry.register
class MyProcessor(BaseTaskProcessor):
    RETRY_ON_ERROR_CONFIG = ErrorsHandleConfig(
        retry_on_errors=[TimeoutError,], 
        retries_count=3, retry_pause=3,
        retry_pause_strategy=const.DELAY_STRATEGY_INCREMENTAL
    )
    def run(self):
        do_something(*self.args, **self.kwargs)

def do_something(*args, **kwargs):
    pass
``` 

With such configuration, the task will be redelayed if `TimeoutError` will be rised for 3 times with 3 sec pause.

`ErrorsHandleConfig` params:
 * `retry_on_errors` - list of exceptions;
 * `retries_count` - positive int. Task will be redelayed for `retries_count` times if any of errors will be rised;
 * `retry_pause` - positive int. Time in seconds to wait before renew task processing;
 * `retry_pause_strategy` - one of options: `django_partisan.config.const.DELAY_STRATEGY_INCREMENTAL`, 
 `django_partisan.config.const.DELAY_STRATEGY_CONSTANT`. By default - `DELAY_STRATEGY_CONSTANT`. If is set to `DELAY_STRATEGY_CONSTANT` - 
 on error task will be redelayed with `retry_pause` seconds gap every time. If is set to `DELAY_STRATEGY_INCREMENTAL` - 
 every next time task will be redelayed with increasing by `retry_pause` time gap 
 (with `retry_pause = 3`, and `retries_count = 3` it will redelay for 3, 6, 9 seconds and then fail). 


### Separate by queues

If you want to separate your tasks into separate queues, you need to define queues in setting as a dict, 
where key is a queue name, and value - dict of settings for this queue:

```python
PARTISAN_CONFIG = {
    'default': {  # 'default' - is registered name for default queue, it will be exist anyway
        # ...
    },
    'another_queue': {
        # ...
    }
}
```

Also you need to set queue for your tasks:
```python
from django_partisan.processor import BaseTaskProcessor
from django_partisan import registry


@registry.register
class MyProcessor(BaseTaskProcessor):
    QUEUE_NAME = 'another_queue'
    def run(self):
        do_something(*self.args, **self.kwargs)

def do_something(*args, **kwargs):
    pass

```

After it you can run partisan to run this queue:

```bash
$ python manage.py start_partisan --queue_name another_queue
```

Note:
* If you will not set `QUEUE_NAME` for `Processor`, it will be `default`;
* If you will run this command without specifiing `queue_name` it will serve `default` queue;
* If you will not set settings for queues, the settings will be default for `default` queue;

# Settings
In your project settings you can define such params as:

* `MIN_QUEUE_SIZE` `(int)` - if number of tasks in queue will reach this amount, 
queue manager will add new tasks (default = 2);
* `MAX_QUEUE_SIZE` `(int)` - queue manager will fill queue up to this count of tasks (default = 10);
* `CHECKS_BEFORE_CLEANUP` `(int)` - number of gatherings new tasks before cleaning database connections (default = 50);
* `WORKERS_COUNT` `(int)` - number of workers, that would be instanced by workers manager (default = number of cores);
* `SLEEP_DELAY_SECONDS` `(int)` - time to sleep between queue checks (default = 2);
* `TASKS_PER_WORKER_INSTANCE` `(Optional[int])` - if is set, the worker will be restarted after this count of 
tasks processed (default = None);
* `DELETE_TASKS_ON_COMPLETE` `(bool)` - if True, task object will be deleted from db, if it successfully processed;

But it will be better, if you'll make settings as a dict:
```python
PARTISAN_CONFIG = {
    'default': {  # 'default' - is registered name for default queue, it will be exist anyway
        'MIN_QUEUE_SIZE':10,
        'MAX_QUEUE_SIZE':20,
        'CHECKS_BEFORE_CLEANUP':50,
        'WORKERS_COUNT':5,
        'SLEEP_DELAY_SECONDS':5,
        'TASKS_PER_WORKER_INSTANCE': 50,
        'DELETE_TASKS_ON_COMPLETE':False,
        'DEFAULT_POSTPONE_DELAY_SECONDS':5,
        'DEFAULT_POSTPONES_COUNT':None,
    }
}
```

It is possible to override some of this settings by cli args for `start_partisan`:
* `--min_queue_size` - `MIN_QUEUE_SIZE`;
* `--max_queue_size` - `MAX_QUEUE_SIZE`;
* `--checks_before_cleanup` - `CHECKS_BEFORE_CLEANUP`;
* `--workers_count` - `WORKERS_COUNT`;
* `--sleep_delay_seconds` - `SLEEP_DELAY_SECONDS`;

# API
* `BaseTaskProcessor`

    * `BaseTaskProcessor.delay(*, priority: int = 0, execute_after: datetime = None)` accept only keyword arguments. 
    It is possible to override priority of task and set execution datetime (task will not be processed before this time);
    * `BaseTaskProcessor.PRIORITY` - property of TaskProcessor. The lower the number, the higher the priority. 
    Tasks with higher priority would be taken for processing first;
    * `BaseTaskProcessor.UNIQUE_FOR_PARAMS` - boolean property of TaskProcessor. If `True`, it will ignore for 
    task adding if task with exactly same args and kwargs is already in queue;
    
    
# Some behavior features
* This tool works only with PostgreSQL, as it supports `JSONField`
* After Manager process got a kill signal, it will wait for workers to finish their jobs, and gracefully shut down them;
* If for some reason Manager process was killed without gracefull shut down, 
after restart it will take for work tasks, that were not finished and only after them it will take all other tasks;

# Known issues
* This tool can be launched on MacOS, but it's strongly recomened to use it only with Linux as multiprocessing Queue 
not fully compatible with MacOS. Use it on MacOS only for development and debugging.
* After calling SIG_TERM, tool can cause some exceptions. It does't break anything and I'm trying to fix it. 
Don't worry about it

# Contributing 
If you experience any problems with usage of this package, 
feel free to open an issue or pull-request

Pull-request requirements:
* Code style according to PEP-8 (use `make black` for it);
* 100% test coverage (use `make coverage`);
* Typing (use `make check_mypy`;
* Version bump (you can use `make major_release`, `make minor_release`, `make patch_release` for it)

All this checks are in CI
