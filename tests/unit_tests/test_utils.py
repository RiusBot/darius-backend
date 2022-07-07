import pytest
from asynctest import TestCase, Mock, CoroutineMock
from asynctest.mock import patch
from parameterized import parameterized
from ccxt import BaseError

from main.src.utils import generate_random_string, pagination, data_decrypt, error_handler, input_filter
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
        self.assertEqual(len(generate_random_string(test_input)), expected)

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

    @patch('main.src.utils.decrypt')
    def test_data_decrypt(self, decrypt):
        decrypt.return_value = 'decrpyted'

        self.assertEqual(
            data_decrypt({'api_key': '123', 'api_secret': '456'}),
            {'api_key': '123', 'api_secret': 'decrpyted', 'headers': {}}
        )

        self.assertEqual(
            data_decrypt({'api_key': '123', 'api_secret': '456', 'password': '789'}),
            {'api_key': '123', 'api_secret': 'decrpyted', 'password': 'decrpyted', 'headers': {}}
        )

        self.assertEqual(
            data_decrypt({'api_key': '123', 'api_secret': '456', 'password': None}),
            {'api_key': '123', 'api_secret': 'decrpyted', 'password': '', 'headers': {}}
        )

    @patch("main.src.utils.fetch_secret_token_firestore")
    async def test_fetch(self, fetch_secret_token_firestore):
        pass

    @parameterized.expand([
        (BackendException, 400),
        (BaseError, 400),
        (Exception, 500),
        (None, 200),
    ])
    async def test_error_handler(self, test_input, expected):

        @error_handler()
        async def test(exception):
            if exception:
                raise exception()

        json_response = await test(test_input)
        self.assertEqual(json_response._status, expected)

    async def test_input_filter(self):

        @input_filter()
        async def test(data, arg1):
            return data, arg1

        get_request = Mock()
        get_request.method = "GET"
        get_request.rel_url = Mock()
        get_request.rel_url.query = {1: 1}
        filter_data, arg1 = await test(get_request, 1)
        self.assertEqual(filter_data, {1: 1})
        self.assertEqual(arg1, 1)

        post_request = Mock()
        post_request.json = CoroutineMock(return_value={2: 2})
        filter_data, arg1 = await test(post_request, '2')
        self.assertEqual(filter_data, {2: 2})
        self.assertEqual(arg1, '2')
