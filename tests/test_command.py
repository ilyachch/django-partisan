# from unittest.mock import patch
#
# from django.test import TestCase
#
# from django_partisan.management.commands.runworker import worker_subprocess
#
#
# class EmptyQueueMock:
#     def __init__(self, *args, **kwargs):
#         pass
#
#     def get(self, *args, **kwargs):
#         return None
#
#
# class TestQueueException(Exception):
#     pass
#
#
# class ExceptionQueueMock:
#     def __init__(self, *args, **kwargs):
#         pass
#
#     def get(self, *args, **kwargs):
#         raise TestQueueException('test error')
#
#
# class TestWorkerSubprocess(TestCase):
#     @patch('django.db.connections')
#     def test_worker_subprocess(self, db_conn_mock):
#         queue = EmptyQueueMock()
#         worker_subprocess(queue)
#
#     @patch('django.db.connections')
#     def test_exception_processing(self, db_conn_mock):
#         queue = ExceptionQueueMock()
#         worker_subprocess(queue)
