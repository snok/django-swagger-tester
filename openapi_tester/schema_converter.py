from datetime import datetime
from typing import Any, List, Optional

from openapi_tester.constants import OPENAPI_PYTHON_MAPPING


class SchemaToPythonConverter:
    """
    This class is used both by the DocumentationError format method and the various test suites.
    """

    def __init__(self, schema: dict, with_faker: bool = False):
        while any(keyword in schema for keyword in ["allOf", "oneOf", "anyOf"]):
            if "allOf" in schema:
                from openapi_tester.schema_tester import SchemaTester

                merged_schema = SchemaTester.handle_all_of(**schema)
                schema = merged_schema
            if "oneOf" in schema:
                schema = schema["oneOf"][0]
            if "anyOf" in schema:
                schema = schema["anyOf"][0]
        if with_faker:
            """ We are importing faker here to ensure this remains a dev dependency """
            from faker import Faker

            Faker.seed(0)
            self.faker = Faker()
        schema_type = schema.get("type")
        if not schema_type:
            if "properties" in schema:
                schema_type = "object"
            else:
                raise ValueError(
                    f"Schema type is not specified and cannot be inferred, "
                    f"please make sure to definte the type key for schema: {schema}"
                )
        if schema_type == "array":
            self.result = self._iterate_schema_list(schema)  # type :ignore
        elif schema_type == "object":
            self.result = self._iterate_schema_dict(schema)  # type :ignore
        else:
            self.result = self._to_mock_value(schema_type, schema.get("enum"), schema.get("format"))  # type :ignore

    def _to_mock_value(self, schema_type: Any, enum: Optional[List[Any]], _format: Optional[str]) -> Any:
        if not hasattr(self, "faker"):
            return OPENAPI_PYTHON_MAPPING[schema_type]
        if enum:
            return enum[0]
        elif _format:
            if schema_type == "string":
                if _format == "date":
                    return datetime.now().date().isoformat()
                elif _format == "date-time":
                    return datetime.now().isoformat()
                elif _format == "bytes":
                    return self.faker.pystr().encode("utf-8")
        faker_handlers = {
            "boolean": self.faker.pybool,
            "string": self.faker.pystr,
            "file": self.faker.pystr,
            "array": self.faker.pylist,
            "object": self.faker.pydict,
            "integer": self.faker.pyint,
            "number": self.faker.pyfloat,
        }
        return faker_handlers[schema_type]()

    def _iterate_schema_dict(self, schema_object: Any) -> Any:
        parsed_schema = {}
        if "allOf" in schema_object:
            from openapi_tester.schema_tester import SchemaTester

            schema_object = SchemaTester.handle_all_of(**schema_object)
        if "properties" in schema_object:
            properties = schema_object["properties"]
        elif "additionalProperties" in schema_object:
            properties = {"": schema_object["additionalProperties"]}
        else:
            properties = {}

        for key, value in properties.items():
            if "example" in value:
                parsed_schema[key] = value["example"]
            elif "anyOf" in value:
                value = value["anyOf"][0]
            elif "oneOf" in value:
                value = value["oneOf"][0]
            value_type = value.get("type")
            if not value_type and "properties" in value:
                value_type = "object"
            elif not value_type:
                continue
            if value_type == "object":
                parsed_schema[key] = self._iterate_schema_dict(value)
            elif value_type == "array":
                parsed_schema[key] = self._iterate_schema_list(value)
            else:
                parsed_schema[key] = self._to_mock_value(value["type"], value.get("enum"), value.get("format"))
        return parsed_schema

    def _iterate_schema_list(self, schema_array: Any) -> Any:
        parsed_items = []
        raw_items = schema_array["items"]
        if "allOf" in raw_items.keys():
            from openapi_tester.schema_tester import SchemaTester

            raw_items = SchemaTester.handle_all_of(**raw_items)
        items_type = raw_items.get("type")
        if not items_type:
            if "properties" in raw_items:
                items_type = "object"
            else:
                return []
        if items_type == "object":
            parsed_items.append(self._iterate_schema_dict(raw_items))  # type :ignore
        elif items_type == "array":
            parsed_items.append(self._iterate_schema_list(raw_items))  # type :ignore
        else:
            parsed_items.append(
                self._to_mock_value(items_type, raw_items.get("enum"), raw_items.get("format"))
            )  # type :ignore
        return parsed_items
