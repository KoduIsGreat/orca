from jsonschema import Draft7Validator, ValidationError
import logging
import os
import json
from ruamel import yaml
from typing import List, TextIO, Dict
from orca.core.errors import ConfigurationError
import itertools

log = logging.getLogger(__name__)

LATEST_SCHEMA_VERSION = '1.0'
AVAILABLE_SCHEMA_VERSIONS = ['1.0']


def _get_schema_location():
    """
    gets the dir of the schemas
    :return:  the schema directory
    """
    return os.path.dirname(os.path.abspath(__file__))


def _handle_errors(errors: List[ValidationError], fmt_err_func, filename):
    """
    Handles the tree of errors provided by jsonschema and formats them.
    :param errors:
    :param fmt_err_func:
    :param filename:
    :return:  exits if no errors exist
    """
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


def _dump_section(section: Dict):
    return yaml.dump(section)


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

    def from_contexts(contexts):
        _errors = []
        for e in contexts:
            if e.validator == 'anyOf':
                _errors.extend(from_contexts(e.context))
            else:
                _errors.append(e)
        return _errors

    # recursively walk down the tree gathering nested exceptions deep in the workflow graph
    nested_errors = list(itertools.chain.from_iterable(
        [from_contexts(e.context) for e in error.context if e.validator == 'anyOf'])
    )
    # if we have nested errors, its likely that the real error is in there otherwise use top level errors
    errors = error.context if not nested_errors else nested_errors
    for error in errors:

        if error.validator == 'oneOf':
            return (error.absolute_path,
                    'The task "{0}" defines an incorrect kind, or more than one kind\n error message: {1}'.format(
                        error.instance.get('task'), error.message)
                    )

        if error.validator == 'required':
            return error.absolute_path, error.message

        if error.validator == 'additionalProperties':
            return error.absolute_path, error.message

        if error.validator == 'uniqueItems':
            return (error.absolute_path if error.path else None,
                    "contains non-unique items, please remove duplicates from {}".format(error.instance)
                    )

        if error.validator == 'type':
            return error.absolute_path, 'An invalid type was declared: {0}'.format(error.message)

        return error.absolute_path, error.message


def _handle_generic_error(error):
    """
    Handles a single ValidationError produced by jsonschema
    :param error: the error
    :return: a formatted error message
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
        msg_format = 'Error validating job at {0}\n error message: {1}'
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
    try:
        version = orca_data['apiVersion']
    except KeyError:
        raise ConfigurationError(
            "'apiVersion is missing. An API version must be specified on an orca document," +
            " the latest current version is {0}'".format(LATEST_SCHEMA_VERSION)
        )

    schema_file = os.path.join(_get_schema_location(), "ORCA_SCHEMA_{0}.json".format(version))
    try:  # check if the schema file exists.
        with open(schema_file) as fp:
            schema_data = json.load(fp)
            validator = Draft7Validator(schema_data)
            errors = list(validator.iter_errors(orca_data))
            _handle_errors(errors, _handle_generic_error, file.name)
            return data
    except FileNotFoundError:
        raise ConfigurationError(
            "'The apiVersion {0}, is an invalid apiVersion version. It did not match one of the".format(version) +
            " supported apiVersions: {0}'".format(AVAILABLE_SCHEMA_VERSIONS)
        )
