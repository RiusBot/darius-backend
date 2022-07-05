import asyncio
import pytest
from asynctest import TestCase, Mock, CoroutineMock
from parameterized import parameterized

from main.src.utils import generate_random_string, pagination
from main.src.exception import BackendException


class TestUtilsClass(TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @parameterized.expand([
        (-1, 0),
        (0, 0),
        (1, 1),
        (8, 8),
        (42, 42),
    ])
    def test_generate_random_string(self, test_input, expected):
        assert len(generate_random_string(test_input)) == expected

    async def test_pagination(self):
        query = Mock(name="query")
        limit = Mock(name="limit")
        total_count = 100
        query.limit.return_value = limit
        limit.count = CoroutineMock(return_value=total_count)

        with pytest.raises(BackendException):
            await pagination(query, -1, 0)
            await pagination(query, -1, 10)
            await pagination(query, -1, 100)
            await pagination(query, 100, 100)
            await pagination(query, 100, 0)
            await pagination(query, 100, -1)

        await pagination(query, 0, 1)
        await pagination(query, 1, 80)
        await pagination(query, 8, 10)

    def test_data_decrypt(self):
        pass

    def test_fetch(self):
        pass

    def test_error_handler(self):
        pass

    def test_input_filter(self):
        pass
