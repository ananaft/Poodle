import pymongo
import os
import sys
import json

BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

def setup_db(db) -> None:
    # Check directories
    if db not in os.listdir(BASE_PATH + '/databases/'):
        os.mkdir(BASE_PATH + f'/databases/{db}')
    DB_PATH = BASE_PATH + f'/databases/{db}/'
    for d in ['backup', 'exams', 'img', 'random_vars']:
        if d not in os.listdir(DB_PATH):
            os.mkdir(DB_PATH + d)
    # Check JSON config
    if 'config.json' not in os.listdir(DB_PATH):
        config = {
            'NAME': db,
            'Q_CATEGORIES': [],
            'SHUFFLE': 1,
            'RANDOM_ARR_SIZE': 100,
            'COLLECTIONS': ['questions', 'exams']
        }
        with open(DB_PATH + 'config.json', 'w') as wf:
            json.dump(config, wf, indent=2)


def apply_config():
    db = DB.name
    with open(BASE_PATH + f'/databases/{db}/config.json', 'r') as rf:
        config = json.load(rf)
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
        db_categories = input(
            f'No question categories specified for database {db}!\n' +
            'Please input list of categories you want to set for this database\n' +
            'or input 0 if no predetermined categories are desired:\n'
        )
        try:
            db_categories = eval(db_categories)
        except SyntaxError:
            pass
        config['Q_CATEGORIES'] = db_categories
    # Update and reload JSON
    with open(BASE_PATH + f'/databases/{db}/config.json', 'w') as wf:
        json.dump(config, wf, indent=2)
    with open(BASE_PATH + f'/databases/{db}/config.json', 'r') as rf:
        config = json.load(rf)
    # Set variables defined in JSON
    Q_CATEGORIES = config['Q_CATEGORIES']
    SHUFFLE = config['SHUFFLE']
    RANDOM_ARR_SIZE = config['RANDOM_ARR_SIZE']

    return Q_CATEGORIES, SHUFFLE, RANDOM_ARR_SIZE


## Global variables
# Manage arguments passed from shell script to launch.py
args = [x for x in sys.argv if x != '']
if len(args) == 5:
    CREDENTIALS = (sys.argv[-4], sys.argv[-3])
del args
CONNECTION = sys.argv[-2]
CLIENT = pymongo.MongoClient(f'{CONNECTION}')
DB = eval(f'CLIENT.{sys.argv[-1]}')
QUESTIONS = DB.questions
EXAMS = DB.exams

setup_db(DB.name)
Q_CATEGORIES, SHUFFLE, RANDOM_ARR_SIZE = apply_config()

# Expected value types for question keys
KEY_TYPES = {
    'general': {
        'name': str, 'question': str, 'family_type': str, 'moodle_type': str,
        'points': int, 'in_exams': dict, 'time_est': int, 'difficulty': int
    },
    'optional': {
        'img_files': list, 'tables': dict
    },
    # Moodle types
    'multichoice': {
        'correct_answers': list, 'false_answers': list, 'single': int
    },
    'numerical': {
        'correct_answers': list, 'tolerance': float
    },
    'shortanswer': {
        'correct_answers': list, 'usecase': int
    },
    'essay': {
        'answer_files': list
    },
    'matching': {
        'correct_answers': dict, 'false_answers': list
    },
    'gapselect': {
        'correct_answers': dict, 'false_answers': dict
    },
    'ddimageortext': {
        'correct_answers': list, 'drops': dict, 'img_files': list
    },
    'calculated': {
        'correct_answers': list, 'tolerance': list, 'vars': list
    }
}
