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
    # Modify categories if needed
    if DB.name not in Q_CATEGORIES.keys():
        db_categories = smart_input(
            f'No question categories specified for database {DB.name}!\n' +
            'Please input list of categories you want to set for this database\n' +
            'or input False if no predetermined categories are desired: ')
        Q_CATEGORIES[DB.name] = db_categories
        f = open(BASE_PATH + '/poodle/config.py', 'r')
        contents = f.read()
        f.close()
        contents = re.sub(r'(?<=Q_CATEGORIES = ){.*?}', str(Q_CATEGORIES), contents,
                          flags=re.DOTALL)
        f = open(BASE_PATH + '/poodle/config.py', 'w')
        f.write(contents)
        f.close()
    else:
        pass
    # Backup routine
    last_backup = sorted(os.listdir(BASE_PATH + '/backup'))[-1]
    rf = open(BASE_PATH + '/backup/' + last_backup + '/timestamp', 'r')
    last_backup = float(rf.read())
    rf.close()
    # Automatic backup if last backup is older than one week
    if time.time() - last_backup > 604800:
        backup()
    else:
        pass
    # Report status
    print(f'Current database: {DB.name}\n')
    for c in DB.list_collection_names():
        print('Documents in collection %s: %d' % (c, DB.get_collection(c).count_documents({})))
