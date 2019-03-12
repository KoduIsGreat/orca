from jsonschema import Draft7Validator, ValidationError
import logging
import os
import json
from ruamel import yaml
from typing import List
from orca.core.errors import ConfigurationError

log = logging.getLogger(__name__)

LATEST_SCHEMA_VERSION = '1.0'

SCHEMA_FILE_TEMPLATE = "ORCA_SCHEMA_{0}.json"
IMPORTANT_VALIDATORS = ['uniqueItems', 'oneOf']
SCHEMA_LOCATION = os.path.dirname(os.path.abspath(__file__))
MISSING_SCHEMA = "'apiVersion is missing. An API version must be specified on an orca document," + \
                 " the latest current version is {0}'"
INVALID_SCHEMA_VERSION = "The version {0}, is an invalid schema version did not match one of the" + \
                         " supported schema versions: {1}"


def get_schema_location():
    return os.path.dirname(os.path.abspath(__file__))


def handle_errors(errors: List[ValidationError], fmt_err_func, filename):
    errors = list(sorted(errors, key=str))
    if not errors:
        return

    error_msg = '\n'.join(fmt_err_func(error) for error in errors)
    raise ConfigurationError(
        "The Orca configuration: {file} is invalid because:\n {error_msg}".format(
            file_msg=" ' {}'".format(filename) if filename else "",
            error_msg=error_msg
        )
    )


def _parse_anyof_validator(error: ValidationError):
    for context in error.context:
        if context.validator == 'anyOf':
            path, error_msg = _parse_anyof_validator(error)
            return context.path, error_msg

        if context.validator == 'required':
            return (None, context.message)

        if context.validator == 'uniqueItems':
            return (context.path if context.path else None,
                    "contains non-unique items, please remove duplicates from {}".format(
                        context.instance
                    )
                    )


def handle_generic_error(error):
    msg_format = None
    error_msg = error.message
    if error.validator == 'required':
        msg_format = 'Missing Property: {0}'
        error_msg = msg_format.format(error_msg)
    if error.validator == 'anyOf':
        error_msg = _parse_anyof_validator(error)


def check(file_data: str):
    orca_data = yaml.load(file_data, yaml.Loader)
    version = orca_data['apiVersion']
    schema_file = os.path.join(SCHEMA_LOCATION, SCHEMA_FILE_TEMPLATE.format(version))
    with open(schema_file) as fp:
        schema_data = json.load(fp)
        validator = Draft7Validator(schema_data)
        errors = list(validator.iter_errors(orca_data))
        handle_errors(errors, handle_generic_error, fp.name)
