import shutil
from pathlib import Path
import os
from orca.store.config import DEFAULT_ORCA_PATH
import json
from datetime import datetime


def get_path(*args):
    return Path(os.path.join(os.getenv('ORCA_CACHE_LOCATION', DEFAULT_ORCA_PATH), *args))


def build_path(*args):
    return Path(os.path.join(*args))


def __write_json__(file_path: Path, data={}):
    with file_path.open('w') as f:
        json.dump(data, f)


def __read_json__(file_path: Path):
    with file_path.open('r') as f:
        return json.loads(f.read(), encoding='utf-8')


def read_data(path, filters=None):
    data = __read_json__(build_path(path, 'data.json'))
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
    data_file = build_path(path, 'data.json')
    __write_json__(data_file, data)


def read_metadata(path):
    """ use this to construct paths for future storage support """
    return __read_json__(build_path(path, 'metadata.json'))


def write_metadata(path, metadata={}):
    """ use this to construct paths for future storage support """
    now = datetime.now()
    metadata['_updated'] = now.strftime('%Y-%m-%d %H:%I:%S.%f')
    meta_file = build_path(path, 'metadata.json')
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
