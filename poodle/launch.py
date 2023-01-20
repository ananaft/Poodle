from config import *
from core import *
from exam import *
from question import *
from viewing import *
from experimental import *

import pymongo
import os
import time
import types


def list_functions():
    """
    Display a list of all available functions.

    -------------------
    Dependencies: types
    """

    all_functions = [f for f in globals().values() if type(f) == types.FunctionType]

    for f in all_functions:
        if (f.__module__ != 'core' and
            f.__name__ != 'pprint' and
            f.__name__ != 'list_functions'):

            print(f.__name__)


if __name__ == "__main__":
    # Backup routine
    if os.listdir(BASE_PATH + f'/databases/{DB.name}/backup/'):
        last_backup = sorted(os.listdir(BASE_PATH + f'/databases/{DB.name}/backup/'))[-1]
        with open(BASE_PATH + f'/databases/{DB.name}/backup/' + last_backup + '/timestamp', 'r') as rf:
            last_backup = float(rf.read())
        # Automatic backup if last backup is older than one week
        if time.time() - last_backup > 604800:
            backup()
    else:
        print('No backups found.')
    # Report status
    print(f'Current database: {DB.name}\n')
    for c in DB.list_collection_names():
        print('Documents in collection %s: %d' % (c, DB.get_collection(c).count_documents({})))
