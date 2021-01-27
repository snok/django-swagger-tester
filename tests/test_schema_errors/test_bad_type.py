import pytest

from openapi_tester import OpenAPISchemaError, SchemaTester

example_schema_array = {"type": "array", "items": {"type": "string"}}
example_array = ["string"]

tester = SchemaTester()


def test_bad_schema_type():
    """
    Unsupported schema types should raise an error.
    TODO: Implement error handling in the schema tester - this currently isn't handled
    """
    for _type in ["str", "list", "dict", "123", 123]:
        with pytest.raises(OpenAPISchemaError, match="Received a bad schema type: str"):
            schema_array = {"type": "array", "items": {"type": _type}}
            tester.test_schema_section(schema_array, example_array, reference="")
