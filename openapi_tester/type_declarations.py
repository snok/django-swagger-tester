import sys
from typing import TYPE_CHECKING, Callable, List, Optional


class Exporter:
    """
    This class can replace a module with itself and this way let that module
    export any identifier. The value of the identifier will be the name
    of the identifier (as a string):
    https://mail.python.org/pipermail/python-ideas/2012-May/014969.html
    """

    def __getattr__(self, item: str) -> str:
        return item

    @classmethod
    def export_anything(cls, module_name: str) -> None:
        """
        We are exploiting duck-typing here, so we need to add an exception
        to the type checker here.
        """
        # noinspection PyTypeChecker
        sys.modules[module_name] = cls()  # type: ignore


if not TYPE_CHECKING:
    """
    if we are running the code, let this module export any identifier.
    The value of the identifier will always be the name of the identifier.
    In this example, it would be equivalent to Foo, Bar = 'Foo', 'Bar'
    """
    Exporter.export_anything(__name__)

else:
    """
    if we are type checking, import/define the actual classes/types
    We don't have to worry about circular imports here, since
    the type checker does not actually run the code.
    """
    from rest_framework.response import Response  # noqa: F401
    from rest_framework.test import APITestCase  # noqa: F401

    from openapi_tester.loaders import BaseSchemaLoader, StaticSchemaLoader  # noqa: F401

    class OpenAPITestCase(APITestCase):
        def assertResponse(
            self,
            response: Response,
            case_tester: Optional[Callable[[str], None]] = None,
            ignore_case: Optional[List[str]] = None,
        ) -> None:
            ...
