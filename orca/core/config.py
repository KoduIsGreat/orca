import json
import logging
import os
import re
from typing import List, Dict, TextIO

from dotted.collection import DottedDict
from ruamel import yaml
from orca.schema.validation import validate
from orca.core.errors import ConfigurationError
log = logging.getLogger(__name__)

# all payload data during processing. must be global!
task = DottedDict()
var = DottedDict()


class OrcaConfig(object):
    """ Orca configuration class"""

    @staticmethod
    def __process_config(file: TextIO) -> Dict:
        try:
            # first pass: start by validating the yaml file against the schema version.
            data = validate(file)
            # processing single quote string literals: " ' '
            repl = r"^(?P<key>\s*[^#:]*):\s+(?P<value>['].*['])\s*$"
            fixed_data = re.sub(repl, '\g<key>: "\g<value>"',
                                data, flags=re.MULTILINE)
            log.debug("Processed yaml: {0}".format(fixed_data))
            # second pass: appropriately quote strings in the yaml file.
            config = yaml.load(fixed_data, Loader=yaml.Loader)

            if log.isEnabledFor(logging.DEBUG):  # to avoid always dump json
                log.debug("Loaded yaml: {0}".format(
                    json.dumps(config, indent=2)))

            return config
        except yaml.YAMLError as e:
            log.error(e)
            raise ConfigurationError("error loading yaml file.", e)
        except ConfigurationError as e:
            # lets capture it log it and reraise it.
            log.error(e)
            raise e

    @staticmethod
    def create(file: TextIO, args: List[str] = None) -> 'OrcaConfig':
        d = OrcaConfig.__process_config(file)
        return OrcaConfig(d, file.name, args)

    def __init__(self, config: Dict, file: str = None, args: List[str] = None):
        # the yaml file (if used)

        self.file = file
        self.api_version = config.get('apiVersion')
        self.conf = config.get('conf', {})
        self.deps = config.get('dependencies', [])
        self.var = config.get('var', {})
        self.job = config.get('job')
        self.version = config.get('version', '0.0')
        self.name = config.get('name', file)

        self.__set_vars({} if self.var is None else self.var,
                        args if args is not None else [])

    def get_yaml_dir(self) -> str:
        return os.path.dirname(self.file) if self.file is not None else "."

    def get_yaml_file(self) -> str:
        return self.file

    def get_version(self) -> str:
        return self.version

    def get_name(self) -> str:
        return self.name

    def __resolve_dependencies(self):
        for dep in self.deps:
            try:
                exec("import " + dep, globals())
                log.debug("importing dependency: '{0}'".format(dep))
            except Exception as e:
                raise ConfigurationError(
                    "Cannot not resolve the '{0}' dependency".format(dep), e)

    def __set_vars(self, variables: Dict, args: List[str]) -> None:
        """put all variables as globals"""
        log.debug("setting job variables:")
        for key, val in variables.items():
            if not key.isidentifier():
                raise ConfigurationError(
                    'Invalid variable identifier: "{0}"'.format(key))
            try:
                exec("var.{0}={1}".format(key, val), globals())
                log.debug(
                    "  set var.{0} = {1} -> {2}".format(key, str(val), str(eval("var." + key))))
            except Exception as e:
                raise ConfigurationError(
                    "Cannot set variable: {0}".format(key), e)
