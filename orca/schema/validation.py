from jsonschema import Draft7Validator, ValidationError
import logging
import os
import json
from ruamel import yaml
from typing import List, TextIO
from orca.core.errors import ConfigurationError

log = logging.getLogger(__name__)

LATEST_SCHEMA_VERSION = '1.0'
AVAILABLE_SCHEMA_VERSIONS = ['1.0']


def get_schema_location():
    return os.path.dirname(os.path.abspath(__file__))


def handle_errors(errors: List[ValidationError], fmt_err_func, filename):
    errors = list(sorted(errors, key=str))
    if not errors:
        return

    error_msg = '\n'.join(fmt_err_func(error) for error in errors)
    raise ConfigurationError(
        "The Orca configuration: {file} is invalid because:\n {error_msg}".format(
            file=" ' {}'".format(filename) if filename else "",
            error_msg=error_msg
        )
    )


def _parse_oneof_validator(error: ValidationError):
    """
    Parse jsonschema oneOf Validator
    reason about which sub schemas and validators we are interested in.
    :param error: the validation error with a validator of oneOf
    :return:  path: the absolute path of the most relevant error, message: the error message for the most relevant error
    """
    for context in error.context:
        if context.validator == 'required':
            return context.absolute_path, context.message


def _parse_anyof_validator(error: ValidationError):
    """
    Parses a Jsonschema anyOf validator
    Most of our data is nested under anyOf validators, so we need reason about which validators are important and
    create meaningful error messages for them. Additionally we may need to recursively process anyOf validators until we
    find a meaningful error.
    :param error:  the toplevel Validation error
    :return:  path: the path to the error in the yaml tree,
    error_msg: the most relevant error_message for this branch of the tree.
    """
    for context in error.context:

        if context.validator == 'anyOf':
            path, error_msg = _parse_anyof_validator(error)
            return path, error_msg

        if context.validator == 'oneOf':
            path, error_msg = _parse_oneof_validator(error)
            return path, error_msg

        if context.validator == 'required':
            return context.absolute_path, context.message

        if context.validator == 'uniqueItems':
            return (context.absolute_path if context.path else None,
                    "contains non-unique items, please remove duplicates from {}".format(context.instance)
                    )
        if context.validator == 'type':
            return context.absolute_path, 'An invalid type was declared: {0}'.format(context.message)


def handle_generic_error(error):
    """
    Handle top-level orca document errors
    :param error:
    :return:
    """
    error_msg = error.message
    if error.validator == 'required':
        msg_format = 'missing a required property: {0}'
        return msg_format.format(error_msg)

    if error.validator == 'additionalProperties':
        msg_format = 'An invalid property has been defined: {0}'
        return msg_format.format(error_msg)

    if error.validator == 'type':
        msg_format = 'An invalid type was declared {0}'
        return msg_format.format(error_msg)

    if error.validator == 'anyOf':
        path, error_msg = _parse_anyof_validator(error)
        msg_format = 'Error validating job at {0}, error message: {1}'
        return msg_format.format(path, error_msg)

    if error.validator == 'oneOf':
        path, error_msg = _parse_oneof_validator(error)
        msg_format = 'The task located at {0}, does not define a valid kind: {1}'
        return msg_format.format(path, error_msg)


def validate(file: TextIO):
    """
    Checks the orca file against a schema. which schema is determined by the 'apiVersion' defined in the
    orca configuration, if no configuration
    :param file:
    :return:
    """
    data = file.read()
    log.debug("Raw yaml: {0}".format(data))

    orca_data = yaml.load(data, yaml.Loader)
    print(json.dumps(orca_data, indent=2))
    try:
        version = orca_data['apiVersion']
    except KeyError as e:
        raise ConfigurationError(
            "'apiVersion is missing. An API version must be specified on an orca document," +
            " the latest current version is {0}'".format(LATEST_SCHEMA_VERSION), e
        )

    schema_file = os.path.join(get_schema_location(), "ORCA_SCHEMA_{0}.json".format(version))
    if os.path.isfile(schema_file):  # check if the schema file exists.
        with open(schema_file) as fp:
            schema_data = json.load(fp)
            validator = Draft7Validator(schema_data)
            errors = list(validator.iter_errors(orca_data))
            handle_errors(errors, handle_generic_error, fp.name)
            return data
    else:
        raise ConfigurationError(
            "'The version {0}, is an invalid schema version. It did not match one of the" +
            " supported schema versions: {1}'".format(version, AVAILABLE_SCHEMA_VERSIONS)
        )
