
<p align="center"><h1 align='center'>DRF OpenAPI Tester</h1></p>
<p align="center">
    <em>A test utility for validating response documentation</em>
</p>
<p align="center">
    <a href="https://pypi.org/project/drf-openapi-tester/">
        <img src="https://img.shields.io/pypi/v/drf-openapi-tester.svg" alt="Package version">
    </a>
    <a href="https://codecov.io/gh/snok/drf-openapi-tester">
        <img src="https://codecov.io/gh/snok/drf-openapi-tester/branch/master/graph/badge.svg" alt="Code coverage">
    </a>
    <a href="https://pypi.org/project/drf-openapi-tester/">
        <img src="https://img.shields.io/badge/python-3.6%2B-blue" alt="Supported Python versions">
    </a>
    <a href="https://pypi.python.org/pypi/drf-openapi-tester">
        <img src="https://img.shields.io/badge/django%20versions-2.2%2B-blue" alt="Supported Django versions">
    </a>
    <a href="http://mypy-lang.org/">
        <img src="http://www.mypy-lang.org/static/mypy_badge.svg" alt="Checked with mypy">
    </a>
</p>

DRF OpenAPI Tester is a simple test utility. Its aim is to make it easy for
developers to catch and correct documentation errors in their OpenAPI schemas.

Maintaining good documentation is difficult, and shouldn't be done manually.
By simply testing that your API responses match your schema definitions you can
*know* that your schema reflects reality.

## How does it work?

Testing your schema is as simple as calling `validate_response` at the end
of a regular test.

```python
from openapi_tester.case_testers import is_camel_case
from openapi_tester.schema_tester import SchemaTester

schema_tester = SchemaTester(case_tester=is_camel_case)


def test_response_documentation(client):
    response = client.get('api/v1/test/1')

    assert response.status_code == 200
    assert response.json() == expected_response

    schema_tester.validate_response(response=response)
```

See docs further down for more details.

## Supported OpenAPI Implementations

Whether we're able to test your schema or not will depend on how it's implemented.
We currently support the following:

- Testing dynamically rendered OpenAPI schemas with [drf-yasg](https://github.com/axnsan12/drf-yasg)
- Testing dynamically rendered OpenAPI schemas with [drf-spectacular](https://github.com/tfranzel/drf-spectacular)
- Testing any implementation which generates a static yaml or json file (e.g., like [DRF](https://www.django-rest-framework.org/topics/documenting-your-api/#generating-documentation-from-openapi-schemas))

If you're using another method to generate your schema and
would like to use this package, feel free to add an issue or
create a PR.

Adding a new implementation is as easy as adding the
required logic needed to load the OpenAPI schema.

## Installation


```shell script
pip install drf-openapi-tester
```

## Features

The primary feature of the schema tester is to validate your API responses
with respect to your documented responses.
If your schema correctly describes a response, nothing happens;
if it doesn't, we throw an error.

The second, optional feature, is checking the [case](https://en.wikipedia.org/wiki/Naming_convention_(programming)) of your
response keys. Checking that your responses are camel cased is
probably the most common standard, but the package supplies case testers
for the following formats:

- `camelCase`
- `snake_case`
- `PascalCase`
- `kebab-case`

## The schema tester

The schema tester is a class, and can be instantiated once or multiple times, depending on your needs.

```python
from openapi_tester.schema_tester import SchemaTester
from openapi_tester.case_testers import is_camel_case

tester = SchemaTester(
    case_tester=is_camel_case,
    ignore_case=['IP'],
    schema_file_path=file_path
)
```

### Case tester

The case tester argument takes a callable to validate the case
of both your response schemas and responses. If nothing is passed,
case validation is skipped.

### Ignore case

List of keys to ignore. In some cases you might want to declare a global
list of exempt keys; keys that you know are not properly cased, but you do not intend to correct.

See the response tester description for info about ignoring keys for individal responses.

### Schema file path

This is the path to your OpenAPI schema. **This is only required if you use the
StaticSchemaLoader loader class, i.e., you're not using `drf-yasg` or `drf-spectacular`.**

## The validate response method

To test a response, you call the `validate_response` method.

```python
from .conftest import tester

def test_response_documentation(client):
    response = client.get('api/v1/test/1')
    tester.validate_response(response=response)
```

If you want to override the instantiated `ignore_case` list,
or `case_tester` for a single test, you can pass these directly
to the function.

```python
from .conftest import tester
from openapi_tester.case_testers import is_snake_case

def test_response_documentation(client):
    ...
    tester.validate_response(
        response=response,
        case_tester=is_snake_case,
        ignore_case=['DHCP']
    )
```

## Performing response validation in a DRF APIView

In addition to using the `validate_response` method directly, we provide
an APIView  with the possibility of validating your response by calling `self.assertResponse`.

Simply define your view class like this:

```python
from openapi_tester.schema_tester import SchemaTester
from openapi_tester.case_testers import is_camel_case

OpenAPITestCase = SchemaTester(case_tester=is_camel_case).test_case()


class TestApi(OpenAPITestCase):

    def validate_response_schema(self):
        response = self.client.get(...)
        self.assertResponse(response)
```

The `assertResponse` method takes the same arguments as `validate_response`.

## Examples

### Testing with Pytest

```python
from openapi_tester.schema_tester import SchemaTester
from openapi_tester.case_testers import is_camel_case

tester = SchemaTester(case_tester=is_camel_case)

def test_200_response_documentation(client):
    response = client.get('api/v1/test/1')

    assert response.status_code == 200
    assert response.json() == expected_response

    tester.validate_response(response=response)
```

### Testing with Django Test

```python
from openapi_tester.schema_tester import SchemaTester
from openapi_tester.case_testers import is_camel_case

tester = SchemaTester(case_tester=is_camel_case)


class MyApiTest(APITestCase):

    def setUp(self) -> None:
        user, _ = User.objects.update_or_create(username='test_user')
        self.client.force_authenticate(user=user)

    def test_get_200(self) -> None:
        """
        Verifies that a 200 is returned for a valid GET request to the /test/ endpoint.
        """
        response = self.client.get('/api/v1/test/', headers={'Content-Type': 'application/json'})
        expected_response = [...]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_response)

        tester.validate_response(response=response)
```

or

```python
from openapi_tester.schema_tester import SchemaTester
from openapi_tester.case_testers import is_camel_case

OpenAPITestCase = SchemaTester(case_tester=is_camel_case).test_case()


class TestApi(OpenAPITestCase):

    def setUp(self) -> None:
        user, _ = User.objects.update_or_create(username='test_user')
        self.client.force_authenticate(user=user)

    def test_get_200(self) -> None:
        """
        Verifies that a 200 is returned for a valid GET request to the /test/ endpoint.
        """
        response = self.client.get('/api/v1/test/', headers={'Content-Type': 'application/json'})
        expected_response = [...]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_response)

        self.assertResponse(response=response)
```

## Error messages

When found, errors will be raised in the following format:

```shell script
openapi_tester.exceptions.DocumentationError: Item is misspecified:

Expected:   {'name': 'Saab', 'height': 'medium'}

Received:   {'name': 'Saab'}

Hint:       Remove the key(s) from you OpenAPI docs, or include it in your API response.

Sequence:   init.list
```

- `Expected` describes the response data
- `Received` describes the schema.
- `Hint` will sometimes include a suggestion for what actions to take, to correct an error.
- `Sequence` will indicate how the response tester iterated through the data structure, before finding the error.

In this example, the response data is missing two attributes, ``height`` and ``width``, documented in the OpenAPI schema indicating that either the response needs to include more data, or that the OpenAPI schema should be corrected. It might be useful to highlight that we can't be sure whether the response or the schema is wrong; only that they are inconsistent.

### Supporting the project

Please leave a ✭ if this project helped you 👏 and contributions are always welcome!
