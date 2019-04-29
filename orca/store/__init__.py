from .store import store
from .utils import (
    set_path, get_path, list_stores, delete_store, delete_stores)

__version__ = "0.0.1"
__author__ = "Adam Shelton"

__all__ = ['store', 'get_path', 'set_path',
           'list_stores', 'delete_store', 'delete_stores']
