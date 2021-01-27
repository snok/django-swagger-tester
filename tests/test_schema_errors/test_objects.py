import pytest

from openapi_tester import DocumentationError, SchemaTester

example_schema_object = {"type": "object", "properties": {"value": {"type": "integer"}}}
example_object = {"value": 1}

tester = SchemaTester()


def test_nothing_wrong():
    """ This should always pass """
    tester.test_schema_section(example_schema_object, example_object, "")


def test_response_is_missing_keys():
    """ Missing keys in a response object should raise an error """
    with pytest.raises(DocumentationError, match="The following properties are missing from the tested data: value"):
        tester.test_schema_section(example_schema_object, {}, "")


def test_schema_object_is_missing_keys():
    """ Excess keys in a response should raise an error """
    with pytest.raises(DocumentationError):
        schema = {"type": "object", "properties": {}}
        tester.test_schema_section(schema, example_object, "")


def test_null():
    """ A null value should always raise an error """
    with pytest.raises(DocumentationError, match="Mismatched types, expected dict but received NoneType"):
        tester.test_schema_section(example_schema_object, None, "")


def test_nullable():
    """ A null value is allowed when the object is nullable """
    schema = {"type": "object", "properties": {"value": {"type": "integer"}}, "nullable": True}
    tester.test_schema_section(schema, None, "")


def test_wrong_type():
    """ Type mismatches should raise errors """
    with pytest.raises(DocumentationError, match="expected dict but received list."):
        tester.test_schema_section(example_schema_object, [], "")
    with pytest.raises(DocumentationError, match="expected dict but received str."):
        tester.test_schema_section(example_schema_object, "test", "")
    with pytest.raises(DocumentationError, match="expected dict but received int."):
        tester.test_schema_section(example_schema_object, 1, "")
    with pytest.raises(DocumentationError, match="expected dict but received float."):
        tester.test_schema_section(example_schema_object, 1.1, "")
    with pytest.raises(DocumentationError, match="expected dict but received tuple."):
        tester.test_schema_section(example_schema_object, ("test",), "")
