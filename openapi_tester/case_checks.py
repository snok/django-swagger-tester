import logging
from typing import Union, Callable, Any

from rscase import rscase

from .exceptions import SpecificationError

logger = logging.getLogger('openapi-tester')


def case_check(case: Union[str, None]) -> Callable:
    """
    Returns the appropriate case check based on the `case` input parameter.

    :param case: str
    :return: function
    """
    return {
        'camel case': is_camel_case,
        'snake case': is_snake_case,
        'kebab case': is_kebab_case,
        'pascal case': is_pascal_case,
        None: skip,
    }[case]


def is_camel_case(key: str) -> None:
    """
    Asserts that a value is camelCased.

    :param key: str
    :return: None
    :raises: SpecificationError
    """
    logger.debug('Verifying that %s is properly camel cased.', key)
    if rscase.camel_case(key) != key:
        logger.error('%s is not camel cased correctly.', key)
        raise SpecificationError(f'The property `{key}` is not properly camelCased')


def is_snake_case(key: str) -> None:
    """
    Asserts that a value is snake_cased.

    :param key: str
    :return: None
    :raises: SpecificationError
    """
    logger.debug('Verifying that %s is properly snake cased.', key)
    if rscase.snake_case(key) != key:
        logger.error('%s is not snake cased correctly.', key)
        raise SpecificationError(f'The property `{key}` is not properly snake_cased')


def is_kebab_case(key: str) -> None:
    """
    Asserts that a value is kebab-cased.

    :param key: str
    :return: None
    :raises: SpecificationError
    """
    logger.debug('Verifying that %s is properly kebab cased.', key)
    if rscase.kebab_case(key) != key:
        logger.error('%s is not kebab cased correctly.', key)
        raise SpecificationError(f'The property `{key}` is not properly kebab-cased')


def is_pascal_case(key: str) -> None:
    """
    Asserts that a value is PascalCased.

    :param key: str
    :return: None
    :raises: SpecificationError
    """
    logger.debug('Verifying that %s is properly pascal cased.', key)
    if rscase.pascal_case(key) != key:
        logger.error('%s is not pascal cased correctly.', key)
        raise SpecificationError(f'The property `{key}` is not properly PascalCased')


def skip(*args: Any) -> None:
    """
    Skips case assertion.

    :return: None
    """
    logger.debug('Skipping case check.')
    pass
