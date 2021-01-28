import pytest

from openapi_tester import DocumentationError, SchemaTester

example_schema_string = {"type": "string", "minLength": 3, "maxLength": 5}
example_string = "str"

tester = SchemaTester()


# region: string


def test_nothing_wrong():
    """ This should always pass """
    tester.test_schema_section(example_schema_string, example_string, "")


def test_min_length_violated():
    """ Not adhering to minlength limitations should raise an error """
    # with pytest.raises(
    #     DocumentationError,
    # match="Mismatched content. Response string violates the minimum string " "length defined in the schema",
    # ):
    tester.test_schema_section(example_schema_string, "a" * 2, "")


def test_max_length_violated():
    """ Not adhering to maxlength limitations should raise an error """
    with pytest.raises(
        DocumentationError,
        match="Mismatched content. Response string violates the maximum string " "length defined in the schema",
    ):
        tester.test_schema_section(example_schema_string, "a" * 6, "")


def test_null():
    """ A null value should always raise an error """
    with pytest.raises(DocumentationError, match="Mismatched types, expected str but received NoneType"):
        tester.test_schema_section(example_schema_string, None, reference="")


def test_nullable():
    """ A null value is allowed when the array is nullable """
    schema = {"type": "string", "nullable": True}
    tester.test_schema_section(schema, None, reference="")


def test_wrong_type():
    """ Type mismatches should raise errors """
    with pytest.raises(DocumentationError, match="expected str but received dict."):
        tester.test_schema_section(example_schema_string, {}, "")
    with pytest.raises(DocumentationError, match="expected str but received list."):
        tester.test_schema_section(example_schema_string, [], "")
    with pytest.raises(DocumentationError, match="expected str but received int."):
        tester.test_schema_section(example_schema_string, 1, "")
    with pytest.raises(DocumentationError, match="expected str but received float."):
        tester.test_schema_section(example_schema_string, 1.1, "")
    with pytest.raises(DocumentationError, match="expected str but received tuple."):
        tester.test_schema_section(example_schema_string, ("test",), "")


# endregion: string

# region: special formats


def test_good_date():
    tester.test_schema_section({"type": "string", "format": "date"}, "2040-01-01", "")


def test_bad_date():
    with pytest.raises(DocumentationError, match="expected a value with the format date but received 01-31-2019"):
        tester.test_schema_section({"type": "string", "format": "date"}, "01-31-2019", "")


def test_good_datetime():
    """ Should pass """
    tester.test_schema_section({"type": "string", "format": "date-time"}, "2040-01-01 08:00", "")


def test_bad_datetime():
    with pytest.raises(
        DocumentationError, match="expected a value with the format date-time but received 2040-01-01 0800"
    ):
        tester.test_schema_section({"type": "string", "format": "date-time"}, "2040-01-01 0800", "")


def test_good_byte():
    tester.test_schema_section({"type": "string", "format": "byte"}, b"test", "")


def test_bad_byte():
    with pytest.raises(DocumentationError, match="expected a value with the format byte but received test"):
        tester.test_schema_section({"type": "string", "format": "byte"}, "test", "")


# endregion: special formats
