import pytest

from openapi_tester import OpenAPISchemaError, SchemaTester

example_schema_array = {"type": "array", "items": {"type": "string"}}
example_array = ["string"]

tester = SchemaTester()


def test_bad_schema_type():
    """
    Unsupported schema types should raise an error.
    """
    with pytest.raises(OpenAPISchemaError, match="Received a bad schema type: str"):
        schema_array = {"type": "array", "items": {"type": "str"}}
        tester.test_schema_section(schema_array, example_array, reference="")
