
from __future__ import absolute_import
from __future__ import unicode_literals
from orca.store import store
from orca.store.utils import (
    set_path, get_path, list_stores, delete_store, delete_stores)

__all__ = ['store', 'get_path', 'set_path',
           'list_stores', 'delete_store', 'delete_stores']
name = 'amanzi.orca'

__version__ = '0.5.4-dev0'
