import json
import logging
import re
import os
from typing import List, Dict, TextIO
from ruamel import yaml
from dotted.collection import DottedDict


log = logging.getLogger(__name__)

# all payload data during processing. must be global!
task = DottedDict()
var = DottedDict()


class OrcaConfigException(Exception):
    pass


class OrcaConfig(object):
    """ Orca configuration class"""
  
    @staticmethod
    def __process_config(file: TextIO) -> Dict:
      try:
          data = file.read()
          print(data)
          
          # first pass: start with a valid the yaml file.
          yaml.load(data)
          
          # processing single quote string literals: " ' '
          repl = r"^(?P<key>\s*[^#:]*):\s+(?P<value>['].*['])\s*$"
          fixed_data = re.sub(repl, '\g<key>: "\g<value>"', data, flags=re.MULTILINE)
          print(fixed_data)
          
          # second pass: do it.
          config = yaml.load(fixed_data)

          return config
      except yaml.YAMLError as e:
          log.error(e)
          raise OrcaConfigException("error loading yaml file.")
  
    @staticmethod
    def create(file: TextIO, args: List[str] = None) -> 'OrcaConfig' :
      d = OrcaConfig.__process_config(file)
      return OrcaConfig(d, file.name, args)
      
  
    def __init__(self, config: Dict, file: str = None, args: List[str] = None):
        ## the yaml file (if used)
        self.file = file
        self.conf = config.get('conf', {})
        self.deps = config.get('dependencies', [])
        self.var = config.get('var', {})
        self.job = config['job']
        
        self.__resolve_dependencies()
        self.__set_vars({} if self.var is None else self.var, args if args is not None else [])
        
    def get_yaml_dir(self) -> str:
        return os.path.dirname(self.file) if self.file is not None else "."
    
    def get_yaml_file(self) -> str:
        return self.file

    def __resolve_dependencies(self):
        for dep in self.deps:
            try:
                exec("import " + dep, globals())
            except OrcaConfigException as b:
                log.error("Orca could not resolve the {0} dependency".format(dep))
      
    def __set_vars(self, variables: Dict, args: List[str]) -> None:
        """put all variables as globals"""
        print(variables)
        for key, val in variables.items():
            if not key.isidentifier():
                raise OrcaConfigException('Invalid variable identifier: "{0}"'.format(key))
            try:
                exec("var.{0}={1}".format(key,val))
                print("var.{0} = {1} -> {2}".format(key, str(val), str(eval("var."+key))))
            except Exception as e:
                raise e
