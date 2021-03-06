import re
from typing import Any, Callable, Dict, KeysView, List, Optional, Union, cast

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework.response import Response
from rest_framework.test import APITestCase

from openapi_tester import type_declarations as td
from openapi_tester.constants import OPENAPI_PYTHON_MAPPING
from openapi_tester.exceptions import DocumentationError, OpenAPISchemaError, UndocumentedSchemaSectionError
from openapi_tester.loaders import DrfSpectacularSchemaLoader, DrfYasgSchemaLoader, StaticSchemaLoader


class SchemaTester:
    def __init__(
        self,
        case_tester: Optional[Callable[[str], None]] = None,
        ignore_case: Optional[List[str]] = None,
        schema_file_path: Optional[str] = None,
    ) -> None:
        """
        Iterates through an OpenAPI schema object and API response to check that they match at every level.

        :param case_tester: An optional callable that validates schema and response keys
        :param ignore_case: An optional list of keys for the case_tester to ignore
        :schema_file_path: The file path to an OpenAPI yaml or json file. Only passed when using a static schema loader
        :raises: openapi_tester.exceptions.DocumentationError or ImproperlyConfigured
        """
        self.case_tester = case_tester
        self.ignore_case = ignore_case or []

        self.loader: Union[StaticSchemaLoader, DrfSpectacularSchemaLoader, DrfYasgSchemaLoader]
        if schema_file_path is not None:
            self.loader = StaticSchemaLoader(schema_file_path)
        elif "drf_spectacular" in settings.INSTALLED_APPS:
            self.loader = DrfSpectacularSchemaLoader()
        elif "drf_yasg" in settings.INSTALLED_APPS:
            self.loader = DrfYasgSchemaLoader()
        else:
            raise ImproperlyConfigured("No loader is configured.")

    @staticmethod
    def handle_all_of(**kwargs: dict) -> dict:
        properties: Dict[str, Any] = {}
        for entry in kwargs.pop("allOf"):
            for key, value in entry["properties"].items():
                if key in properties and isinstance(value, dict):
                    properties[key] = {**properties[key], **value}
                elif key in properties and isinstance(value, list):
                    properties[key] = [*properties[key], *value]
                else:
                    properties[key] = value
        return {**kwargs, "type": "object", "properties": properties}

    def handle_one_of(
        self,
        schema_section: dict,
        data: Any,
        reference: str,
        case_tester: Optional[Callable[[str], None]] = None,
        ignore_case: Optional[List[str]] = None,
    ):
        matches = 0
        for option in schema_section["oneOf"]:
            try:
                self.test_schema_section(
                    schema_section=option,
                    data=data,
                    reference=reference,
                    case_tester=case_tester,
                    ignore_case=ignore_case,
                )
                matches += 1
            except DocumentationError:
                continue
        if matches != 1:
            raise DocumentationError(
                message=f"expected data to match one and only one of schema types, received {matches} matches.",
                response=data,
                schema=schema_section,
                reference=reference,
            )

    @staticmethod
    def _get_key_value(schema: dict, key: str, error_addon: str = "") -> dict:
        """
        Indexes schema by string variable.
        """
        try:
            return schema[key]
        except KeyError:
            raise UndocumentedSchemaSectionError(
                f"Error: Unsuccessfully tried to index the OpenAPI schema by `{key}`. {error_addon}"
            )

    @staticmethod
    def _get_status_code(schema: dict, status_code: Union[str, int], error_addon="") -> dict:
        """
        Indexes schema by string variable.
        """
        if str(status_code) in schema:
            return schema[str(status_code)]
        elif int(status_code) in schema:
            return schema[int(status_code)]
        raise UndocumentedSchemaSectionError(
            f"Error: Unsuccessfully tried to index the OpenAPI schema by `{status_code}`. {error_addon}"
        )

    @staticmethod
    def _route_error_text_addon(paths: KeysView) -> str:
        route_error_text = ""
        pretty_routes = "\n\t• ".join(paths)
        route_error_text += f"\n\nFor debugging purposes, other valid routes include: \n\n\t• {pretty_routes}"
        return route_error_text

    @staticmethod
    def _method_error_text_addon(methods: KeysView) -> str:
        str_methods = ", ".join(method.upper() for method in methods if method.upper() != "PARAMETERS")
        return f"\n\nAvailable methods include: {str_methods}."

    @staticmethod
    def _responses_error_text_addon(status_code: Union[int, str], response_status_codes: KeysView) -> str:
        return f'\n\nUndocumented status code: {status_code}.\n\nDocumented responses include: {", ".join([str(key) for key in response_status_codes])}. '

    def get_response_schema_section(self, response: td.Response) -> dict:
        """
        Indexes schema by url, HTTP method, and status code to get the schema section related to a specific response.

        :param response: DRF Response Instance
        :return Response schema
        """
        path = response.request["PATH_INFO"]
        method = response.request["REQUEST_METHOD"]
        status_code = str(response.status_code)
        schema = self.loader.get_schema()
        parameterized_path = self.loader.parameterize_path(path)
        paths_object = self._get_key_value(schema=schema, key="paths")
        route_object = self._get_key_value(
            schema=paths_object,
            key=parameterized_path,
            error_addon=self._route_error_text_addon(paths_object.keys()),
        )
        method_object = self._get_key_value(
            schema=route_object, key=method.lower(), error_addon=self._method_error_text_addon(route_object.keys())
        )
        responses_object = self._get_key_value(schema=method_object, key="responses")
        status_code_object = self._get_status_code(
            schema=responses_object,
            status_code=status_code,
            error_addon=self._responses_error_text_addon(status_code, responses_object.keys()),
        )
        if "openapi" not in schema:
            # openapi 2.0, i.e. "swagger" has a different structure than openapi 3.0 status sub-schemas
            return self._get_key_value(schema=status_code_object, key="schema")
        content_object = self._get_key_value(schema=status_code_object, key="content")
        json_object = self._get_key_value(schema=content_object, key="application/json")
        return self._get_key_value(schema=json_object, key="schema")

    @staticmethod
    def is_nullable(schema_item: dict) -> bool:
        """
        Checks if the item is nullable.

        OpenAPI 3 ref: https://swagger.io/docs/specification/data-models/data-types/#null
        OpenApi 2 ref: https://help.apiary.io/api_101/swagger-extensions/

        :param schema_item: schema item
        :return: whether or not the item can be None
        """
        openapi_schema_3_nullable = "nullable"
        swagger_2_nullable = "x-nullable"
        return any(
            nullable_key in schema_item and schema_item[nullable_key]
            for nullable_key in [openapi_schema_3_nullable, swagger_2_nullable]
        )

    def _validate_key_casing(
        self, key: str, case_tester: Optional[Callable[[str], None]] = None, ignore_case: Optional[List[str]] = None
    ) -> None:
        tester = case_tester or getattr(self, "case_tester", None)
        ignore_case = [*self.ignore_case, *(ignore_case or [])]
        if tester and key not in ignore_case:
            tester(key)

    @staticmethod
    def _validate_enum(schema_section: dict, data: str) -> Union[Optional[str], bool]:
        if "enum" not in schema_section:
            return False

        enum = schema_section.get("enum")
        if enum and data not in enum:
            return (
                f'Mismatched values, expected a member of the enum {schema_section["enum"]} but received {str(data)}.'
            )

    @staticmethod
    def _validate_pattern(schema_section: dict, data: str) -> Union[Optional[str], bool]:
        if "pattern" not in schema_section:
            return False
        try:
            compiled_pattern = re.compile(schema_section["pattern"])
        except re.error as e:
            raise OpenAPISchemaError(f"String pattern is not valid regex: {schema_section['pattern']}") from e
        if not compiled_pattern.match(data):
            return f"String '{data}' does not validate using the specified pattern: {schema_section['pattern']}"

    @staticmethod
    def _validate_format(schema_section: dict, data: str) -> Union[Optional[str], bool]:
        format = schema_section.get("format")
        if not format:
            return False

        valid = True
        if format in ["double", "float"]:
            valid = isinstance(data, float)
        elif format == "byte":
            valid = isinstance(data, bytes)
        elif format == "date":
            try:
                result = parse_date(format)
                valid = result is not None
            except ValueError:
                valid = False
        elif format == "date-time":
            try:
                result = parse_datetime(format)
                valid = result is not None
            except ValueError:
                valid = False
        if not valid:
            return f'Mismatched values, expected a value with the format {schema_section["format"]} but received {str(data)}.'

    def _validate_openapi_type(self, schema_section: dict, data: str) -> Union[Optional[str], bool]:
        valid = True
        schema_type = schema_section.get("type")
        if schema_type in ["string", "file"]:
            valid = isinstance(data, str)
        elif schema_type == "integer":
            valid = isinstance(data, int)
        elif schema_type == "number":
            valid = isinstance(data, (int, float))
        elif schema_type == "object":
            valid = isinstance(data, dict)
        elif schema_type == "array":
            valid = isinstance(data, list)
        if data is None:
            valid = self.is_nullable(schema_section)
        if not valid:
            return (
                f"Mismatched types, expected {OPENAPI_PYTHON_MAPPING[schema_type]} "
                f"but received {type(data).__name__}."
            )

    def test_schema_section(
        self,
        schema_section: dict,
        data: Any,
        reference: str = "",
        case_tester: Optional[Callable[[str], None]] = None,
        ignore_case: Optional[List[str]] = None,
    ) -> None:
        """
        This method orchestrates the testing of a schema section
        """
        if "oneOf" in schema_section and data is not None:
            self.handle_one_of(
                schema_section=schema_section,
                data=data,
                reference=reference,
                case_tester=case_tester,
                ignore_case=ignore_case,
            )
        else:
            if "allOf" in schema_section:
                merged_schema = self.handle_all_of(**schema_section)
                schema_section = merged_schema
            schema_section_type = schema_section.get("type")
            if not schema_section_type and "properties" in schema_section:
                schema_section_type = "object"
            if not schema_section_type:
                # No schema type == any schema type, so we return early
                return

            validators = [
                self._validate_openapi_type,
                self._validate_format,
                self._validate_pattern,
                self._validate_enum,
            ]
            for validator in validators:
                error = validator(schema_section, data)
                if isinstance(error, str):
                    raise DocumentationError(message=error, response=data, schema=schema_section, reference=reference)

            if schema_section_type == "object":
                self._test_openapi_type_object(
                    schema_section=schema_section,
                    data=data,
                    reference=reference,
                    case_tester=case_tester,
                    ignore_case=ignore_case,
                )
            elif schema_section_type == "array":
                self._test_openapi_type_array(
                    schema_section=schema_section,
                    data=data,
                    reference=reference,
                    case_tester=case_tester,
                    ignore_case=ignore_case,
                )

    def _test_openapi_type_object(
        self,
        schema_section: dict,
        data: dict,
        reference: str,
        case_tester: Optional[Callable[[str], None]],
        ignore_case: Optional[List[str]],
    ) -> None:
        if "properties" in schema_section:
            properties = schema_section["properties"]
        elif "additionalProperties" in schema_section:
            properties = {"": schema_section["additionalProperties"]}
        else:
            properties = {}
        required_keys = schema_section["required"] if "required" in schema_section else list(properties.keys())
        response_keys = data.keys()

        if len([key for key in response_keys if key in required_keys]) != len(required_keys):
            missing_keys = ", ".join(str(key) for key in sorted(list(set(required_keys) - set(response_keys))))
            hint = "Remove the key(s) from your OpenAPI docs, or include it in your API response."
            message = f"The following properties are missing from the tested data: {missing_keys}."
            raise DocumentationError(
                message=message,
                response=data,
                schema=schema_section,
                reference=reference,
                hint=hint,
            )

        for schema_key, response_key in zip([key for key in properties.keys() if key in response_keys], response_keys):
            self._validate_key_casing(schema_key, case_tester, ignore_case)
            self._validate_key_casing(response_key, case_tester, ignore_case)
            if schema_key in required_keys and schema_key not in response_keys:
                raise DocumentationError(
                    message=f"Schema key `{schema_key}` was not found in the tested data.",
                    response=data,
                    schema=schema_section,
                    reference=reference,
                    hint="The response should contain this key or the documentation should change.",
                )
            if response_key not in properties:
                raise DocumentationError(
                    message=f"Key `{response_key}` not found in the OpenAPI schema.",
                    response=data,
                    schema=schema_section,
                    reference=reference,
                    hint="The response should contain this key or the documentation should change.",
                )

            schema_value = properties[schema_key]
            response_value = data[schema_key]
            self.test_schema_section(
                schema_section=schema_value,
                data=response_value,
                reference=f"{reference}.dict:key:{schema_key}",
                case_tester=case_tester,
                ignore_case=ignore_case,
            )

    def _test_openapi_type_array(
        self,
        schema_section: dict,
        data: dict,
        reference: str,
        case_tester: Optional[Callable[[str], None]],
        ignore_case: Optional[List[str]],
    ) -> None:
        items = schema_section["items"]
        if items is None and data is not None:
            raise DocumentationError(
                message="Mismatched content. Response array contains data, when schema is empty.",
                response=data,
                schema=schema_section,
                reference=reference,
                hint="Document the contents of the empty dictionary to match the response object.",
            )

        for datum in data:
            self.test_schema_section(
                schema_section=items,
                data=datum,
                reference=f"{reference}.list",
                case_tester=case_tester,
                ignore_case=ignore_case,
            )

    def validate_response(
        self,
        response: td.Response,
        case_tester: Optional[Callable[[str], None]] = None,
        ignore_case: Optional[List[str]] = None,
    ):
        """
        Verifies that an OpenAPI schema definition matches an API response.

        :param response: The HTTP response
        :param case_tester: Optional Callable that checks a string's casing
        :param ignore_case: List of strings to ignore when testing the case of response keys
        :raises: ``openapi_tester.exceptions.DocumentationError`` for inconsistencies in the API response and schema.
                 ``openapi_tester.exceptions.CaseError`` for case errors.
        """

        if not isinstance(response, Response):
            raise ValueError("expected response to be an instance of DRF Response")

        response_schema = self.get_response_schema_section(response)
        self.test_schema_section(
            schema_section=response_schema,
            data=response.json(),
            reference="init",
            case_tester=case_tester,
            ignore_case=ignore_case,
        )

    def test_case(self) -> APITestCase:
        validate_response = self.validate_response

        def assert_response(
            response: td.Response,
            case_tester: Optional[Callable[[str], None]] = None,
            ignore_case: Optional[List[str]] = None,
        ) -> None:
            """
            Assert response matches the OpenAPI spec.
            """
            validate_response(response=response, case_tester=case_tester, ignore_case=ignore_case)

        return cast(td.OpenAPITestCase, type("OpenAPITestCase", (APITestCase,), {"assertResponse": assert_response}))
