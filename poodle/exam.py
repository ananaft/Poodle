from config import *
from core import *

import os
import re
from PIL import Image
import numpy as np
import json


def create_exam(exam, filename='import.xml', mode='terminal', questions=None, message=True):
    """
    Creates an xml file out of questions within the database. While using this
    function the user will be asked whether they want to use automatic or manual
    creation mode. In automatic mode a file which contains questions' names
    separated by whitespace is used to automatically generate the xml file. In
    manual mode the user will type in each question one by one.

    After the xml file is created, an exam document will be added to the EXAMS
    collection and all corresponding question documents will be modified within
    the QUESTIONS collection.

    Arguments:
    ----------
    exam (str):
      Name of the exam within Moodle/Poodle.
    filename (str):
      Name of the output xml file.
    mode (str):
      Changes behavior depending on if function is used in terminal or in GUI.
    questions (list):
      If used in GUI, a list of question names will be passed to this argument.
      The argument isn't used otherwise.

    ------------------------------
    Dependencies: config, core, re
    """

    # Write XML
    questionlist, info = create_xml(exam, filename, mode, questions)

    # Update database
    EXAMS.insert_one({
        'name': exam,
        'points_max': info[2],
        'time_est': info[0],
        'difficulty_avg': info[1],
        'questions': questionlist
    })
    for q in questionlist:
        QUESTIONS.find_one_and_update(
            {'name': q}, {'$set': {f'in_exams.{exam}': np.nan}}
        )

    # Final report
    if message:
        print((
            f'\nTotal points: {info[2]}\n'
            f'Average difficulty: {info[1]}\n'
            f'Estimated time: {info[0]} minutes\n'
        ))
        print('Database updated.')


def create_testexam(exam, filename='import.xml'):
    """
    This function is very similar to 'create_exam()' and is intended for
    experimenting with its features. It will not create any entries within the
    database upon creation of the exam. Apart from this, 'create_testexam()'
    functions exactly like 'create_exam()'.

    Arguments:
    ----------
    exam (str):
      Name of the exam within Moodle/Poodle.
    filename (str):
      Name of the output xml file.

    ------------------------------
    Dependencies: config, core, re
    """

    # Write XML
    questionlist, info = create_xml(exam, filename)

    print((
        f'\nTotal points: {info[2]}\n'
        f'Average difficulty: {info[1]}\n'
        f'Estimated time: {info[0]} minutes\n'
    ))
    print('Test exam successfully created.')
    

def remove_exam(exam, message=True):
    """
    Remove an exam from the database. This will remove the exam's document from
    the exams collection, as well as all entries of this exam within the
    questions.

    Arguments:
    ----------
    exam (str):
      Name of the exam that will be removed from the database.

    --------------------
    Dependencies: config
    """

    deletion = EXAMS.delete_many({'name': exam})
    updates = QUESTIONS.update_many(
        {'_id': {'$type': 7}}, {'$unset': {f'in_exams.{exam}': ''}}
    )
    # Final report
    if message:
        print(f'{deletion.deleted_count} document(s) have been removed ' +
              'from the exams collection.\n' +
              f'{updates.modified_count} question(s) have been updated.')


def evaluate_exam(exam_name, stats_file, ratings_file):
    """
    This function will evaluate the JSON files which are exported from Moodle
    within the categories 'Statistik' and 'Bewertung'. The evaluated information
    regarding individual questions' and the exam's average score will be passed
    to the database.

    Arguments:
    ----------
    exam_name (str):
      Name of the exam within the database.
    stats_file (str):
      Path of the JSON file exported from 'Statistik'.
    ratings_file (str):
      Path of the JSON file exported from 'Bewertung'.

    ------------------------
    Dependencies: json, numpy
    """

    # Check for correct exam name
    if exam_name not in os.listdir(f'{BASE_PATH}/databases/{DB.name}/exams/'):
        prompt = ('Warning! Exam name was not found in directory. ' +
                  f'Do you still wish to evaluate exam {exam_name}? (y/n)\n')
        if yesno(prompt) == 'y':
            pass
        else:
            return 'Evaluation aborted.'
    assert EXAMS.find_one({'name': exam_name}), \
        f'Exam {exam_name} does not exist in database!'

    # Read stats_file for question names
    with open(stats_file, 'r') as rf:
        stats = json.load(rf)
    # Check again for correct exam name
    assert stats[0][0]['test-name'] == exam_name, \
        f'Exam name in stats file is not {exam_name}!'
    name_pairs = {}
    for q in stats[1]:
        # Ignore "clones" from rvar questions
        if '.' not in q['f']:
            # Check question in database
            question = QUESTIONS.find_one({'name': q['titelderfrage']})
            if question:
                moodle_name = 'f' + q['f'] + str(question['points'] * 100)
                name_pairs[moodle_name] = [q['titelderfrage'], question['points']]
            else:
                print(f'{q["titelderfrage"]} not in database. ' +
                      'Ignoring question for evaluation.')

    # Read ratings_file for exam and question scores
    with open(ratings_file, 'r') as rf:
        averages = json.load(rf)[0][-1]
    assert averages['nachname'] == 'Gesamtdurchschnitt', \
        f'Last entry in ratings is not Gesamtdurchschnitt, but {averages["nachname"]} instead!'
    # Append average question scores to name_pairs
    for q in name_pairs:
        avg = averages[q]
        if avg == '-':
            avg = np.nan
        else:
            avg = float(avg.replace(',', '.'))
        name_pairs[q].append(avg)
    # Get average exam score
    exam_average = float([
        averages[k] for k, v in averages.items() if k.startswith('bewertung')
    ][0].replace(',', '.'))
    # Update questions in DB
    for k, v in name_pairs.items():
        QUESTIONS.find_one_and_update(
            {'name': v[0]}, {'$set': {f'in_exams.{exam_name}': v[2]}}
        )
    # Update exam in DB
    rel_averages = {
        v[0]: np.round(v[2] / v[1], 2) for k, v in name_pairs.items()
    }
    EXAMS.find_one_and_update(
        {'name': exam_name},
        {'$set': {
            'points_avg': exam_average,
            'question_avgs': rel_averages
         }}
    )

    print(f'\nExam {exam_name} succesfully evaluated.')
