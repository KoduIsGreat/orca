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

# TODO refactor so task and var are no longer needed.
# TODO remove __set_vars and evals

# all payload data during processing. must be global!
task = DottedDict()
var = DottedDict()


def resolve_file_path(config: "OrcaConfig", name: str, ext: str) -> str:
    """ resolve the full qualified path name"""

    def _resolve_file_path(config: OrcaConfig, _name: str) -> str:
        """ resolve the full qualified path name"""
        if os.path.isfile(_name):
            return _name
        # otherwise find the relative dir
        yaml_dir = config.yaml_dir
        rel_path = os.path.join(yaml_dir, _name)
        if os.path.isfile(rel_path):
            # path relative to yaml file
            return rel_path
        else:
            # this should be a file but it's not.
            raise ConfigurationError('File not found: "{0}"'.format(_name))

    # check to see if the value ends with an extension
    if name.endswith(ext):
        # check if its an absolute path
        return _resolve_file_path(config, name)
    # check if its a variable
    elif name.startswith("var."):
        try:
            name = eval(str(name), globals())
        except Exception as e:
            # ok, never mind
            log.debug(e)
        if not name:
            return name
        return _resolve_file_path(config, name)


class OrcaConfig(object):
    """ Orca configuration class"""

    @staticmethod
    def __process_config(file: TextIO) -> Dict:
        try:
            # first pass: start by validating the yaml file against the schema version.
            data = validate(file)
            # processing single quote string literals: " ' '
            repl = r"^(?P<key>\s*[^#:]*):\s+(?P<value>['].*['])\s*$"
            fixed_data = re.sub(repl, '\g<key>: "\g<value>"', data, flags=re.MULTILINE)
            log.debug("Processed yaml: {0}".format(fixed_data))
            # second pass: appropriately quote strings in the yaml file.
            config = yaml.load(fixed_data, Loader=yaml.Loader)

            if log.isEnabledFor(logging.DEBUG):  # to avoid always dump json
                log.debug("Loaded yaml: {0}".format(json.dumps(config, indent=2)))

            return config
        except yaml.YAMLError as e:
            log.error(e)
            raise ConfigurationError("error loading yaml file.", e)
        except ConfigurationError as e:
            # lets capture it log it and reraise it.
            raise e

    @staticmethod
    def create(file: TextIO, args: List[str] = None) -> "OrcaConfig":
        d = OrcaConfig.__process_config(file)
        return OrcaConfig(d, file.name, args)

    def __init__(self, config: Dict, file: str = None, args: List[str] = None):
        # the yaml file (if used)

        self.file = file
        self.api_version = config.get("apiVersion")
        self.sym_table = {}
        self.conf = config.get("conf", {})
        self.var = config.get("var", {})
        self.job = config.get("job")
        self.version = config.get("version", "0.0")
        self.name = config.get("name", file)
        self.cache = None

        self.__set_vars({} if self.var is None else self.var)

    @property
    def yaml_dir(self) -> str:
        return os.path.dirname(self.file) if self.file is not None else "."

    @property
    def yaml_file(self) -> str:
        return self.file

    def get_version(self) -> str:
        return self.version

    def get_name(self) -> str:
        return self.name

    def __set_vars(self, variables: Dict) -> None:
        """put all variables as globals"""
        log.debug("setting job variables:")
        for key, val in variables.items():
            if not key.isidentifier():
                raise ConfigurationError(
                    'Invalid variable identifier: "{0}"'.format(key)
                )
            try:
                exec("var.{0}={1}".format(key, val), globals())
                log.debug(
                    "  set var.{0} = {1} -> {2}".format(
                        key, str(val), str(eval("var." + key))
                    )
                )
            except Exception as e:
                raise ConfigurationError("Cannot set variable: {0}".format(key), e)
