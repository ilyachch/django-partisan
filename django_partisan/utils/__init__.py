# type: ignore
# pragma: no cover

import sys

if sys.platform == 'darwin':  # pragma: no cover
    from django_partisan.utils._macos import Queue
else:  # pragma: no cover
    from multiprocessing import Queue

__all__ = [
    'Queue',
]
