import pytest

from openapi_tester import DocumentationError, SchemaTester

example_schema_array = {"type": "array", "items": {"type": "string"}}
example_array = ["string"]

tester = SchemaTester()


def test_matching_example_and_schema():
    """
    Nothing should happen.
    """
    tester.test_schema_section(example_schema_array, example_array, reference="")


def test_schema_array_contains_items_but_response_is_empty():
    """
    An empty array should pass.
    """
    tester.test_schema_section(example_schema_array, [], reference="")


def test_schema_array_contains_items_but_response_is_null():
    """
    A None instead of an array should raise an error.
    """
    with pytest.raises(DocumentationError, match="Mismatched types, expected list but received NoneType"):
        tester.test_schema_section(example_schema_array, None, reference="")


def test_schema_array_contains_items_but_response_is_null_and_nullable():
    """
    A nullable array should pass.
    """
    schema = {"type": "array", "items": {"type": "string"}, "nullable": True}
    tester.test_schema_section(schema, None, reference="")
