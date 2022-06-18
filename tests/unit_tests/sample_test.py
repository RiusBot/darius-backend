from unittest import mock
from unittest import TestCase


class SampleTest(TestCase):

    def setUp(self):
        pass

    def test_pass(self):
        assert True

    def test_1(self):
        expected_result = mock.MagicMock()
        assert expected_result == True