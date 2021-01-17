from copy import deepcopy
from typing import Callable

import pytest

from openapi_tester import UndocumentedSchemaSectionError
from openapi_tester.schema_tester import SchemaTester
from tests.utils import response_factory

tester = SchemaTester()
parameterized_path = '/api/{version}/cars/correct'
de_parameterized_path = '/api/v1/cars/correct'
method = 'get'
status = '200'


def _mock_schema(schema) -> Callable:
    def _mocked():
        return schema

    return _mocked


def test_validate_response_success_scenario():
    schema = deepcopy(tester.loader.get_schema())

    for path, path_object in schema['paths'].items():
        for method, method_object in path_object.items():
            for status_code, responses_object in method_object['responses'].items():
                if hasattr(responses_object, 'content'):
                    schema_section = responses_object['content']['application/json']['schema']
                    response = response_factory(schema_section, path, method, status_code)
                    assert tester.validate_response(response) == schema_section
                    assert tester.validate_response(response) == schema_section


def test_validate_response_failure_scenario_undocumented_path(monkeypatch):
    schema = deepcopy(tester.loader.get_schema())
    schema_section = schema['paths'][parameterized_path][method]['responses'][status]['content']['application/json'][
        'schema'
    ]
    del schema['paths'][parameterized_path]
    monkeypatch.setattr(tester.loader, 'get_schema', _mock_schema(schema))
    response = response_factory(schema_section, de_parameterized_path, method, status)
    with pytest.raises(
        UndocumentedSchemaSectionError,
        match=f'Error: Unsuccessfully tried to index the OpenAPI schema by `{parameterized_path}`.',
    ):
        tester.validate_response(response)


def test_validate_response_failure_scenario_undocumented_method(monkeypatch):
    schema = deepcopy(tester.loader.get_schema())
    schema_section = schema['paths'][parameterized_path][method]['responses'][status]['content']['application/json'][
        'schema'
    ]
    del schema['paths'][parameterized_path][method]
    monkeypatch.setattr(tester.loader, 'get_schema', _mock_schema(schema))
    response = response_factory(schema_section, de_parameterized_path, method, status)
    with pytest.raises(
        UndocumentedSchemaSectionError,
        match=f'Error: Unsuccessfully tried to index the OpenAPI schema by `{method}`.',
    ):
        tester.validate_response(response)


def test_validate_response_failure_scenario_undocumented_status_code(monkeypatch):
    schema = deepcopy(tester.loader.get_schema())
    schema_section = schema['paths'][parameterized_path][method]['responses'][status]['content']['application/json'][
        'schema'
    ]
    del schema['paths'][parameterized_path][method]['responses'][status]
    monkeypatch.setattr(tester.loader, 'get_schema', _mock_schema(schema))
    response = response_factory(schema_section, de_parameterized_path, method, status)
    with pytest.raises(
        UndocumentedSchemaSectionError,
        match=f'Error: Unsuccessfully tried to index the OpenAPI schema by `{status}`.',
    ):
        tester.validate_response(response)