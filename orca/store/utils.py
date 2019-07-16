import shutil
from pathlib import Path
import os
from orca.store.config import DEFAULT_ORCA_PATH
import json
import gzip
from dateutil import parser
from datetime import datetime

# TODO break encoders into their own module (relevant for all of orca)?
# TODO add simplified connect api for connecting a specific tasks data
# TODO allow azr blob storage or s3 bucket file protocols
# TODO update to a faster compression e.g. snappy?
# TODO create an abstractions for "readers" and "writers"? support different types, protobuf, json, sql etc

def get_path(*args):
    return Path(os.path.join(os.getenv('ORCA_CACHE_LOCATION', DEFAULT_ORCA_PATH), *args))


def build_path(*args):
    return Path(os.path.join(*args))


class OrcaJsonEncoder(json.JSONEncoder):
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    def default(self, o):
        if isinstance(o, datetime):
            return {
                '_type': "datetime",
                "value": o.strftime("%s %s" % (self.DATE_FORMAT, self.TIME_FORMAT))
            }
        if isinstance(o, (bytes, bytearray)):
            return {
                '_type': "bytes",
                'value': o.decode()
            }
       
        return super(OrcaJsonEncoder, self).default(o)


class OrcaJsonDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if '_type' not in obj:
            return obj
        _type = obj['_type']
        if _type == 'datetime':
            return parser.parse(obj['value'])
        if _type == 'bytes':
            return str.encode(obj['value'])
       

def __write_json__(file_path: Path, data={}):
    json_str = json.dumps(data, cls=OrcaJsonEncoder)
    json_bytes = json_str.encode('utf-8')
    with gzip.GzipFile(file_path, 'wb') as f:
        f.write(json_bytes)


def __read_json__(file_path: Path):
    with gzip.GzipFile(file_path, 'rb') as f:
        json_bytes = f.read()
    json_str = json_bytes.decode('utf-8')
    return json.loads(json_str, cls=OrcaJsonDecoder)


def read_data(path, filters=None):
    data = __read_json__(build_path(path, 'data.json.gz'))
    if filters:
        tmp = data
        for f in filters:
            tmp = tmp.get(f, None)
            if tmp is None:
                raise ValueError("""
                    Property %s was not found 
                """ % f)
        return tmp
    return data


def write_data(path, data):
    data_file = build_path(path, 'data.json.gz')
    __write_json__(data_file, data)


def converter(o):
    if isinstance(o, datetime):
        return o.__str__()


def read_metadata(path):
    """ use this to construct paths for future storage support """
    return __read_json__(build_path(path, 'metadata.json.gz'))


def write_metadata(path, metadata={}):
    """ use this to construct paths for future storage support """
    now = datetime.now()
    metadata['_updated'] = now.strftime('%Y-%m-%d %H:%I:%S.%f')
    metadata['_id'] = id(metadata)
    meta_file = build_path(path, 'metadata.json.gz')
    __write_json__(meta_file, metadata)


def set_path(path):
    if path is None:
        path = get_path()

    else:
        path = path.rstrip('/').rstrip('\\').rstrip(' ')
        if "://" in path and "file://" not in path:
            raise ValueError("OrcaStorage only works with local file system")
    path = get_path()
    if not path_exists(path):
        os.makedirs(get_path().__bytes__())

    return get_path()


def path_exists(path: Path):
    return path.exists()


def subdirs(d):
    """ use this to construct paths for future storage support """
    return [o.parts[-1] for o in Path(d).iterdir()
            if o.is_dir() and o.parts[-1] != '_snapshots']


def list_stores():
    if not path_exists(get_path()):
        os.makedirs(get_path().__bytes__())
    return subdirs(get_path())


def delete_stores():
    shutil.rmtree(get_path())
    return True


def delete_store(store):
    shutil.rmtree(get_path(store))
    return True
