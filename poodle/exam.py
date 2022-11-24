from config import *
from core import *

import os
import re
from PIL import Image
import numpy as np
import json
import warnings
import copy

def create_exam(exam, filename='import.xml'):
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

    ------------------------------
    Dependencies: config, core, re
    """

    # Write XML
    questionlist, info = create_xml(exam, filename)

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
    

def remove_exam(exam):
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
    print(f'{deletion.deleted_count} document(s) have been removed from the exams collection.\n' +
          f'{updates.modified_count} question(s) have been updated.')


def evaluate_exam(exam_name, stats_file, ratings_file):
    """
    This function will evaluate the JSON files which are exported from examUP
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
    Dependencies: json, numpy, warnings, copy
    """

    # Check for correct exam name
    if exam_name not in os.listdir(f'{BASE_PATH}/databases/{DB.name}/exams/'):
        prompt = ('Warning! Exam name was not found in directory. ' +
                  f'Do you still wish to evaluate exam {exam_name}? (y/n)\n')
        if yesno(prompt) == 'y':
            pass
        else:
            return 'Evaluation aborted.'
    # Read stats_file for question names
    rf = open(stats_file)
    stats_list = json.load(rf)
    rf.close()
    # Remove "clones" of rvar questions
    stats_list = [
        q for q in stats_list[1] if type(q[0]) == int
    ]
    name_list = [
        q[2] for q in stats_list
    ]
    # Read ratings_file for exam and question scores
    rf = open(ratings_file)
    ratings_list = json.load(rf)
    rf.close()
    # Reverse each student element and keep only question and exam scores
    scores_list = [list(reversed(ratings_list[0][s])) for s in range(len(ratings_list[0]))]
    scores_list = [s[:len(name_list)+1] for s in scores_list]
    name_list.reverse()
    exam_scores = [s.pop() for s in scores_list]
    # Check consistency between name_list and scores
    for s in scores_list:
        assert len(s) == len(name_list), 'Amount of questions and scores are not equal!'
    question_scores = [
        [stud[q] for stud in scores_list]
        for q in range(len(name_list))
    ]
    # Cleaning
    exam_scores = [
        np.nan if pt == '-' else float(pt.replace(',', '.')) for pt in exam_scores
    ]
    question_scores = [
        [np.nan if pt == '-' else
         0 if float(pt.replace(',', '.')) < 0 else
         float(pt.replace(',', '.')) for pt in q]
        for q in question_scores
    ]
    # Calculate averages and merge with question names
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=RuntimeWarning)
        exam_average = np.nanmean(exam_scores).round(2)
        averages = [np.nanmean(q).round(2) for q in question_scores]
    q_averages = dict(zip(name_list, averages))
    # Remove questions that don't exist in database
    q_averages_copy = copy.deepcopy(q_averages)
    for k, v in q_averages_copy.items():
        if not QUESTIONS.find_one({'name': k}):
            q_averages.pop(k)
            print(f'Question {k} not in database!')
        else:
            pass
    rel_q_averages = {
        k: round(v / QUESTIONS.find_one({'name': k})['points'], 2)
        for k, v in q_averages.items()
    }
    # Update database
    EXAMS.find_one_and_update(
        {'name': exam_name}, {'$set': {'points_avg': exam_average,
                                       'questions_avgs': rel_q_averages}}
    )
    for k, v in q_averages.items():
        QUESTIONS.find_one_and_update(
            {'name': k}, {'$set': {f'in_exams.{exam_name}': v}}
        )
