#!/usr/bin/env python

import os
import pathlib
import sys
from typing import Mapping, Optional

from django import setup as django_setup
from django.db.transaction import set_autocommit, rollback
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.validation import Validator, ValidationError

from cli_utils.cli_helper import arg_parser


class ServerPathValidator(Validator):
    def validate(self, document: Document) -> None:
        path = pathlib.Path(document.text)
        if path.exists() and (path / 'manage.py').exists():
            pass
        else:
            raise ValidationError(
                message='The server location you provided {} is not valid'.format(str(path)),
                cursor_position=len(document.text) - 1)


_path_completer = PathCompleter()
_server_path_validator = ServerPathValidator()


def get_server_location() -> pathlib.Path:
    return pathlib.Path(
        prompt(message='Please reenter the Django server location which contains `manage.py` '
                       'file: ',
               validator=_server_path_validator,
               completer=_path_completer,
               ))


def get_valid_server_path(default: str = './') -> pathlib.Path:
    server_path: Optional[pathlib.Path] = pathlib.Path(default)
    while not (server_path and server_path.exists() and (server_path / 'manage.py').exists()):
        server_path = get_server_location()
    return server_path


def init_server_settings(server_path: pathlib.Path) -> None:
    # TODO this will raise exceptions
    #  django.core.exceptions.ImproperlyConfigured
    sys.path.append(str(server_path))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "graphery.settings.test")
    django_setup()
    set_autocommit(False)


def main(command_mapping: Mapping[str, str]):
    # TODO add command line argument here

    from cli_utils.cli_controller import CommandWrapper
    command = command_mapping['command']
    CommandWrapper.run_command(command)


if __name__ == '__main__':
    command_map: Mapping[str, str] = arg_parser()

    server_folder_path: pathlib.Path = get_valid_server_path()
    init_server_settings(server_folder_path)

    try:
        main(command_map)
    finally:
        print('Rollback any unsaved transactions.')
        rollback()
