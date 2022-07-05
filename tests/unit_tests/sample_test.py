from unittest import TestCase, mock


class SampleTest(TestCase):

    def setUp(self):
        pass

    def test_pass(self):
        assert True

    def test_1(self):
        expected_result = mock.MagicMock()
        assert expected_result is not None
