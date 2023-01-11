import pymongo
import os
import sys
import json

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

def apply_config():
    db = DB.name
    with open(BASE_PATH + f'/databases/{db}/config.json', 'r') as f:
        config = json.load(f)
    # Check for config keys
    template = {
        'NAME': f'{db}',
        'Q_CATEGORIES': [],
        'SHUFFLE': 1,
        'RANDOM_ARR_SIZE': 100,
        'COLLECTIONS': ['questions', 'exams']
    }
    for i, j in template.items():
        if i not in config.keys():
            config[i] = j
    # Check for question categories
    if config['Q_CATEGORIES'] == []:
        db_categories = smart_input(
            f'No question categories specified for database {db}!\n' +
            'Please input list of categories you want to set for this database\n' +
            'or input 0 if no predetermined categories are desired:\n'
        )
        config['Q_CATEGORIES'] = db_categories
    # Update and reload JSON
    with open(BASE_PATH + f'/databases/{db}/config.json', 'w') as f:
        json.dump(config, f, indent=2)
    with open(BASE_PATH + f'/databases/{db}/config.json', 'r') as f:
        config = json.load(f)
    # Set variables defined in JSON
    Q_CATEGORIES = config['Q_CATEGORIES']
    SHUFFLE = config['SHUFFLE']
    RANDOM_ARR_SIZE = config['RANDOM_ARR_SIZE']

    return Q_CATEGORIES, SHUFFLE, RANDOM_ARR_SIZE


# Global variables
CLIENT = pymongo.MongoClient()
DB = eval(f'CLIENT.{sys.argv[-1]}')
QUESTIONS = DB.questions
EXAMS = DB.exams
Q_CATEGORIES, SHUFFLE, RANDOM_ARR_SIZE = apply_config()
# Q_CATEGORIES = []
# SHUFFLE = 1
# RANDOM_ARR_SIZE = 100
