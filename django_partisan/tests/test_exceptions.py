from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from django_partisan.exceptions import (
    ProcessorClassNotFound,
    ProcessorClassAlreadyRegistered,
    ProcessorClassException,
    MaxPostponesReached,
)


class TestExceptions(TestCase):
    def test_processor_not_found_exception(self):
        with self.assertRaisesMessage(
            ProcessorClassNotFound,
            'Processor class TestClass cannot be found. Is it registered?',
        ):
            raise ProcessorClassNotFound('TestClass')

    def test_processor_already_registered_exception(self):
        with self.assertRaisesMessage(
            ProcessorClassAlreadyRegistered,
            'Processor class TestClass already registered',
        ):
            raise ProcessorClassAlreadyRegistered('TestClass')

    def test_exception_without_message(self):
        class BadException(ProcessorClassException):
            pass

        with self.assertRaises(NotImplementedError):
            raise BadException('')

    def test_exception_with_bad_message(self):
        class BadException(ProcessorClassException):
            message = '{} {}'

        with self.assertRaises(ImproperlyConfigured):
            raise BadException('')

    def test_exception_with_not_formatable_message(self):
        class BadException(ProcessorClassException):
            message = 'some message'

        with self.assertRaises(ImproperlyConfigured):
            raise BadException('')


class TestPostponeExceptions(TestCase):
    def test_correct_message(self):
        with self.assertRaisesMessage(
            MaxPostponesReached, 'Maximum postpones (15) reached. Failing'
        ):
            raise MaxPostponesReached(15)
