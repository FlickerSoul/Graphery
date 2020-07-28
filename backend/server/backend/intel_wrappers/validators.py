import re
from typing import Sequence


class ValidationError(AssertionError):
    pass


def dummy_validator(info):
    return info


uuid_regex = re.compile(r'^[\da-f]{8}-([\da-f]{4}-){3}[\da-f]{12}$', re.IGNORECASE)


def uuid_validator(uuid):
    if not uuid_regex.match(uuid):
        raise ValidationError('`uuid` is not valid!')


def is_published_validator(val: bool):
    if not isinstance(val, bool):
        raise ValidationError('`is_published` must be a boolean variable!')


category_regex = re.compile(r'^[^-][\w -]*[^-]$')


def category_validator(val: str):
    if not isinstance(val, str) or not val or not category_regex.match(val):
        raise ValidationError('`category` must be a non-empty string and does not start or end with `-` or `_`.')


name_regex = re.compile(r'^[a-zA-Z0-9- ]+\Z')


def name_validator(name: str):
    if not isinstance(name, str) or not name or not name_regex.match(name):
        raise ValidationError('`name` must be a non-empty string and does not start or end with `-` or `_`.')


url_regex = re.compile(r'^[^-][a-zA-Z0-9-]*[^-]\Z')


def url_validator(url: str):
    if not isinstance(url, str) or not url or not url_regex.match(url):
        raise ValidationError('`URL must be a non-empty string containing only letters, numbers, and `-`. '
                              'It should not start or end with `-`')


def categories_validator(cats: Sequence):
    if not isinstance(cats, Sequence):
        raise ValidationError('`Categories` wrapped in wrappers.')
    for cat in cats:
        cat.validate()
