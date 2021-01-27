import pytest

from openapi_tester import DocumentationError, SchemaTester

example_schema_array = {"type": "array", "items": {"type": "string"}}
example_array = ["string"]

tester = SchemaTester()


def test_nothing_wrong():
    """ This should always pass """
    tester.test_schema_section(example_schema_array, example_array, "")


def test_empty_list():
    """ An empty array should always pass """
    tester.test_schema_section(example_schema_array, [], "")


def test_null():
    """ A null value should always raise an error """
    with pytest.raises(DocumentationError, match="Mismatched types, expected list but received NoneType"):
        tester.test_schema_section(example_schema_array, None, reference="")


def test_nullable():
    """ A null value is allowed when the array is nullable """
    schema = {"type": "array", "items": {"type": "string"}, "nullable": True}
    tester.test_schema_section(schema, None, reference="")


def test_wrong_type():
    """ Type mismatches should raise errors """
    with pytest.raises(DocumentationError, match="expected list but received dict."):
        tester.test_schema_section(example_schema_array, {}, "")
    with pytest.raises(DocumentationError, match="expected list but received str."):
        tester.test_schema_section(example_schema_array, "test", "")
    with pytest.raises(DocumentationError, match="expected list but received int."):
        tester.test_schema_section(example_schema_array, 1, "")
    with pytest.raises(DocumentationError, match="expected list but received float."):
        tester.test_schema_section(example_schema_array, 1.1, "")
    with pytest.raises(DocumentationError, match="expected list but received tuple."):
        tester.test_schema_section(example_schema_array, ("test",), "")
