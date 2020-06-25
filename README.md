[![codecov](https://codecov.io/gh/ilyachch/django-partisan/branch/master/graph/badge.svg)](https://codecov.io/gh/ilyachch/django-partisan)
# django-backgroud-tasks-framework
Framework to allow creating background tasks in django without MQ

# Usage
Install app with:
```
$ pip install django-partisan
```

Add it to your `INSTALLED_APPS`

Run migrate command:
```
$ python manage.py migrate
```

Write your task:
```python3
# partisan_tasks.py
from django_partisan.processor import BaseTaskProcessor

class MyProcessor(BaseTaskProcessor):
    PRIORITY = 5  # Optional, by default 10
    UNIQUE_FOR_PARAMS = True  # Optional, by default True

    def run(self):
        do_something(*self.args, **self.kwargs)

```

And then pospone this task:
```python3
from partisan_tasks import MyProcessor

def do_something_and_postpone_task(*args, **kwargs):
    MyProcessor(args, kwargs).delay()

```

To start tasks processing you should lauch workers:

```
$ python manage.py start_partisan
``` 

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
