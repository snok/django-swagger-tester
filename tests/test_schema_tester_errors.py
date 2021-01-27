import pytest

from openapi_tester import OpenAPISchemaError, SchemaTester

example_schema_array = {"type": "array", "items": {"type": "string"}}
example_array = ["string"]

tester = SchemaTester()


def test_matching_example_and_schema():
    """
    Nothing should happen.
    """
    tester.test_schema_section(example_schema_array, example_array, reference="")


def test_bad_schema_type():
    """
    We should raise an error.
    """
    with pytest.raises(OpenAPISchemaError, match="Received a bad schema type: str"):
        schema_array = {"type": "array", "items": {"type": "str"}}
        tester.test_schema_section(schema_array, example_array, reference="")


def test_schema_array_contains_items_but_response_is_empty():
    pass


def test_schema_array_contains_items_but_response_is_null():
    pass


def test_schema_array_contains_items_but_response_is_null_and_nullable():
    pass


def test_schema_array_is_empty_but_response_contains_items():
    pass
