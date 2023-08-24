from config import *
import context

import json
import time
import os
import platform
import subprocess
import re
import pyperclip
from lxml import etree as ET
import base64
import numpy as np
import copy
from pprint import pprint


def backup(db=DB.name) -> None:
    """
    Dependencies: config, time, os
    """
    backup_time = time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())
    os.mkdir(f'{BASE_PATH}/databases/{db}/backup/{backup_time}')
    with open(f'{BASE_PATH}/databases/{db}/backup/{backup_time}/timestamp', 'w') as wf:
        wf.write(str(time.time()))
    # Backup from server
    if 'localhost' not in CONNECTION:
        subprocess.run(
            ["mongodump", f"--db={db}",
             f"--out={BASE_PATH}/databases/{db}/backup/{backup_time}",
             f"--authenticationDatabase=admin", f"{CONNECTION}"]
        )
    # Local backup
    else:
        subprocess.run(
            ["mongodump", f"--db={db}",
             f"--out={BASE_PATH}/databases/{db}/backup/{backup_time}"]
        )


def restore(path=None, db=DB.name) -> None:
    """
    Dependencies: config, platform, subprocess
    """
    if path == None:
        folder = sorted(os.listdir(BASE_PATH + f'/databases/{db}/backup/'))[-1]
        path = BASE_PATH + f'/databases/{db}/backup/' + folder
    # Restore local backup files to server
    if 'localhost' not in CONNECTION:
        subprocess.run(
            ["mongorestore", f"--host={CONNECTION[CONNECTION.find('@')+1:]}",
             f"--username={CREDENTIALS[0]}", f"--password={CREDENTIALS[1]}",
             f"--authenticationDatabase=admin", f"--nsInclude={db}.*", f"{path}"]
        )
    # Restore backup files to localhost
    else:
        subprocess.run(["mongorestore", f"--nsInclude={db}.*", f"{path}"])


def yesno(prompt=''):
    choice = input(prompt)
    while choice.lower() != 'y' and choice.lower() != 'n':
        choice = input("Please type either 'y' or 'n'. ")

    return choice.lower()


def smart_input(prompt=''):
    """
    Input function that is able to distinguish between different storage types.
    Since it has to exclude placeholders from lists, this function will
    interpret nested lists as strings.

    Arguments:
    ----------
    prompt (str):
      Input prompt that will be displayed.

    ----------------
    Dependencies: re
    """
    input_obj = input(prompt)
    # Define storage types
    is_bool = re.compile(r'^True$|^False$')
    is_int = re.compile(r'^\d+$')
    is_float = re.compile(r'^\d+\.\d*$')
    is_str = re.compile(r'.+|$')
    is_list = re.compile(r'^\[.*\]$')
    is_tuple = re.compile(r'^\(.*\)$')
    is_dict = re.compile(r'^\{.*\}$')
    # Check for storage type
    storage_dict = {
        is_bool: 'bool', is_list: 'list', is_tuple: 'tuple', is_dict: 'dict',
        is_int: 'int', is_float: 'float', is_str: 'str'
    }
    # Different syntax needed for these storage types
    special_types = [is_bool, is_list, is_tuple, is_dict]

    for k, v in storage_dict.items():
        if k.match(input_obj) and k in special_types:
            return(eval(v + '(' + input_obj + ')'))
        elif k.match(input_obj):
            return(eval(v + '(input_obj)'))


def fast_input(options, prompt=''):
    """
    Input function that utilizes regular expressions to uniquely identify input
    among available options and minimize required typing.

    Arguments:
    ----------
    options (list):
      Available options that can be entered.
    prompt (str):
      Input prompt that will be displayed.

    ----------------
    Dependencies: re
    """

    def check(pattern):
        for o in options:
            if re.match(pattern, o):
                matches.append(o)
        return matches

    matches = []
    regex = re.compile(input(prompt) + '.*')
    # In case of no match
    while len(check(regex)) == 0:
        regex = input('Please choose one of the available options:\n' +
                      str(options) + '\n')
    # Pick unique match
    if len(matches) == 1:
        return matches[0]
    # Let user choose match if more than one
    else:
        choice = smart_input(f'Multiple matches: {matches}\nType index of desired match ' +
                             '(e.g. 1, 2, ...): ')
        while type(choice) != int or choice > len(matches):
            choice = smart_input('Please specify an integer index that is in range.\n')
        return matches[choice - 1]


def inspect_properties(dictionary, mode = 'standard', inspect = True, add = False):
    """
    The purpose of this function is to inspect and potentially modify the fields
    of a question.

    It will go through the keys and values of a dictionary and allows the user
    to make changes individually. It returns the dictionary including any
    changes made during inspection.

    Arguments:
    ----------
    dictionary (dict):
      Object that will be inspected.
    mode (str):
      Decides which keys (question fields) will be included in the inspection.
      The 'standard' setting excludes fields that should never change in case of
      an already created question. The 'specific' setting allows for inspection
      of specified keys. You can simply pass a field's name to only modify that
      field.
    inspect (bool):
      If set to True, the function will print the current values contained in
      the dictionary's keys.
    add (bool):
      If set to True, allows the user to add keys to the dictionary.

    ---------------------------
    Dependencies: re, pyperclip
    """

    # Set fixed_values according to mode
    if mode == 'standard':
        fixed_values = r'_id|name$|family_type|moodle_type|in_exams'
    elif mode == 'child':
        fixed_values = r'_id|name$|question$|family_type|moodle_type|in_exams'
    elif mode == 'parsingle':
        fixed_values = r'_id|name$|family_type|in_exams|moodle_type'
    elif mode == 'all':
        fixed_values = r'_id'
    elif mode == 'specific':
        inspect_keys = smart_input('Which fields do you wish to inspect/modify?\n' +
                                   '(Please input a list.)\n')
        # Insert each key into regular expression
        counter = 1
        fixed_values = r'^(?!.*('
        for key in inspect_keys:
            if counter == len(inspect_keys):
                fixed_values = fixed_values + r'%s$))' % (key)
            else:
                fixed_values = fixed_values + r'%s$|' % (key)
            counter += 1
    elif mode == 'none':
        fixed_values = r'.*'
    else:
        fixed_values = r'^(?!.*%s(?=$))' % (mode)

    ## Inspect/modify dictionary
    if inspect:
        for k, v in dictionary.items():
            if not bool(re.compile(fixed_values).match(str(k))):
                pyperclip.copy(str(v))
                prompt = (str(k) + ': ' + str(v) +
                  '\nDo you want to make any changes? (y/n)\n')
                if yesno(prompt) == 'y':
                    # Check for lists and apply special procedure
                    if type(v) == list:
                        counter = len(v)
                        for i in range(len(v)):
                            print('Element %d is: ' % (i+1) + "'" + str(v[i]) + "'")
                            new_value = smart_input(
                                'New value (press Enter to keep old value): '
                            )
                            if new_value != '':
                                dictionary[k][i] = new_value
                                print('New value has been set.')
                            counter -= 1
                        # Ask about adding values to empty or exhausted lists
                        while counter == 0:
                            if yesno('Do you want to add a value to the list? (y/n)\n') == 'y':
                                new_value = smart_input('New value: ')
                                dictionary[k].append(new_value)
                                print('New value has been added.')
                            else:
                                break
                    # Check for dictionaries and apply special procedure
                    elif type(v) == dict:
                        counter = len(v)
                        for kk, vv in v.items():
                            print('Current element: ' + str(kk) +
                                  '\nCurrent value: ' + str(vv)
                            )
                            new_value = smart_input(
                                'New value (press Enter to keep old value): '
                            )
                            if new_value != '':
                                dictionary[k][kk] = new_value
                                print('New value has been set.')
                            counter -= 1
                        # Ask about adding keys and values to empty
                        # or exhausted dictionaries
                        while counter == 0:
                            if yesno('Do you want to add a key to the dictionary? (y/n)\n') == 'y':
                                new_key = input('New key: ')
                                new_value = smart_input('New value: ')
                                dictionary[k][new_key] = new_value
                                print('New key and value have been added.')
                            else:
                                break
                    else:
                        dictionary[k] = smart_input('New value: ')
                        if k == 'name' and Q_CATEGORIES:
                            # Check for correct question naming scheme
                            # and duplicates
                            collection_names = [q['name'] for q in QUESTIONS.find()]
                            while (dictionary[k][:-4] not in Q_CATEGORIES or
                                   dictionary[k] in collection_names):
                                dictionary[k] = input('Please input a valid ' +
                                                      'question name: ')
                        print('New value has been set.')
                else:
                    print('No changes made.')

    ## Only modify dictionary
    else:
        for k, v in dictionary.items():
            if not bool(re.compile(fixed_values).match(str(k))):
                pyperclip.copy(str(v))
                print('Current field: ' + str(k))
                # Check for lists and apply special procedure
                if type(v) == list:
                    counter = len(v)
                    for i in range(len(v)):
                        new_value = smart_input(
                            'New value of element %d: ' % (i+1)
                        )
                        dictionary[k][i] = new_value
                        print('New value has been set.')
                        counter -= 1
                    # Ask about adding values to empty or exhausted lists
                    while counter == 0:
                        new_value = smart_input(
                            'New value to add to list ' +
                            '(press Enter to add no value): '
                        )
                        if new_value != '':
                            dictionary[k].append(new_value)
                            print('New value has been added.')
                        else:
                            break
                # Check for dictionaries and apply special procedure
                elif type(v) == dict:
                    counter = len(v)
                    for kk, vv in v.items():
                        print('Current element: ' + str(kk))
                        new_value = smart_input(
                            'New value (press Enter to keep old value): '
                        )
                        if new_value != '':
                            dictionary[k][kk] = new_value
                            print('New value has been set.')
                        counter -= 1
                    # Ask about adding keys and values to empty
                    # or exhausted dictionaries
                    while counter == 0:
                        new_key = input(
                            'New key to add to dictionary ' +
                            '(press Enter to add no key): '
                        )
                        if new_key != '':
                            new_value = smart_input('New value: ')
                            dictionary[k][new_key] = new_value
                            print('New key and value have been added.')
                        else:
                            break
                else:
                    dictionary[k] = smart_input('New value: ')
                    if k == 'name' and Q_CATEGORIES:
                        # Check for correct question naming scheme
                        # and duplicates
                        collection_names = [q['name'] for q in QUESTIONS.find()]
                        while (dictionary[k][:-4] not in Q_CATEGORIES or
                               dictionary[k] in collection_names):
                            dictionary[k] = input('Please input a valid ' +
                                                  'question name: ')
                    print('New value has been set.')

    if add:
        n_of_keys = smart_input('How many fields do you want to add?\n')
        for i in range(n_of_keys):
            add_key = input("Please specify the new field's name.\n")
            add_value = smart_input("Please specify the field's content.\n")
            dictionary[add_key] = add_value
            print('Field added.')
    return dictionary


## Exam creation

class MoodleQuestion(ET.ElementBase):

    def _init(self):
        self.tag = 'question'
        self.name = ET.SubElement(self, 'name')
        self.name_text = ET.SubElement(self.name, 'text')
        self.qt = ET.SubElement(self, 'questiontext', {'format': 'html'})
        self.qt_text = ET.SubElement(self.qt, 'text')
        self.gf = ET.SubElement(self, 'generalfeedback', {'format': 'html'})
        self.gf_text = ET.SubElement(self.gf, 'text')
        self.gf_text.text = ''
        self.dg = ET.SubElement(self, 'defaultgrade')
        self.penalty = ET.SubElement(self, 'penalty')
        self.penalty.text = '0.3333333'
        self.hidden = ET.SubElement(self, 'hidden')
        self.hidden.text = '0'
        self.idnumber = ET.SubElement(self, 'idnumber')
        self.idnumber.text = ''

    @staticmethod
    def make_tables(q, el):
        for m in re.finditer(r'(?<=\[\[)tbl\d+(?=\]\])', el.text):
            tbl = q['tables'][m.group()]

            root = ET.Element('table')
            # Table head
            thead = ET.SubElement(root, 'thead')
            tr = ET.SubElement(thead, 'tr')
            for i in tbl[0]:
                th = ET.SubElement(
                    tr, 'th',
                    attrib={
                        'scope': 'col',
                        'style': 'border-width: 1px; border-style: solid;'
                    }
                )
                th.text = str(i)
            # Table body
            tbody = ET.SubElement(root, 'tbody')
            for i in tbl[1:]:
                tr = ET.SubElement(tbody, 'tr')
                for j in i:
                    td = ET.SubElement(
                        tr, 'td',
                        attrib={
                            'style': 'border-width: 1px; border-style: solid;'
                        }
                    )
                    td.text = str(j)

            # Replace in question text
            repl = ET.tostring(root, pretty_print=True).decode('utf-8')
            el.text = ET.CDATA(re.sub(r'\[\[%s\]\]' % (m.group()), repl, el.text))

    @staticmethod
    def encode_images(q, el):
        for m in re.finditer(r'(?<=\[\[file)\d+(?=\]\])', el.text):
            file_index = int(m.group()) - 1
            current_file = q['img_files'][file_index]
            file_format = re.search(r'(?<=\.)\D+$', current_file)
            file_format = file_format.group()
            with open(f'{BASE_PATH}/databases/{DB.name}/img/' + current_file, 'rb') as rf:
                b64 = base64.b64encode(rf.read()).decode('utf-8')
            repl = f'<img src="data:image/{file_format};base64,{b64}" alt="" />'
            el.text = ET.CDATA(re.sub(r'\[\[file%s\]\]' % (m.group()), repl, el.text))

    def set_defaults(self, q):
        self.name_text.text = q['name']
        self.qt_text.text = ET.CDATA(q['question'])
        self.__class__.make_tables(q, self.qt_text)
        self.__class__.encode_images(q, self.qt_text)
        self.dg.text = str(q['points'])
        self.loc = self.find('idnumber')

    def feedback(self):
        self.loc.addnext(ET.SubElement(self, 'correctfeedback', attrib={'format': 'html'}))
        self.loc = self.loc.getnext()
        child = ET.SubElement(self.loc, 'text')
        child.text = 'Die Antwort ist richtig.'

        self.loc.addnext(ET.SubElement(self, 'partiallycorrectfeedback', attrib={'format': 'html'}))
        self.loc = self.loc.getnext()
        child = ET.SubElement(self.loc, 'text')
        child.text = 'Die Antwort ist teilweise richtig.'

        self.loc.addnext(ET.SubElement(self, 'incorrectfeedback', attrib={'format': 'html'}))
        self.loc = self.loc.getnext()
        child = ET.SubElement(self.loc, 'text')
        child.text = 'Die Antwort ist falsch.'


class MultichoiceQuestion(MoodleQuestion):

    def set_additional(self, q):
        self.loc.addnext(ET.SubElement(self, 'single'))
        self.loc = self.loc.getnext()
        self.single = False
        if len(q['correct_answers']) == 1:
            self.single = True
        try:
            self.single = q['single']
        except KeyError:
            pass
        self.loc.text = str(bool(self.single)).lower()

        self.loc.addnext(ET.SubElement(self, 'shuffleanswers'))
        self.loc = self.loc.getnext()
        self.loc.text = str(bool(SHUFFLE)).lower()

        self.loc.addnext(ET.SubElement(self, 'answernumbering'))
        self.loc = self.loc.getnext()
        self.loc.text = 'abc'

        self.loc.addnext(ET.SubElement(self, 'showstandardinstruction'))
        self.loc = self.loc.getnext()
        self.loc.text = '1'

        self.feedback()

        self.loc.addnext(ET.SubElement(self, 'shownumcorrect'))
        self.loc = self.loc.getnext()

        for a in q['correct_answers']:
            fraction = '%f' % (100./len(q['correct_answers']))
            self.loc.addnext(ET.SubElement(self, 'answer', attrib={
                'fraction': fraction, 'format': 'html'
            }))
            self.loc = self.loc.getnext()
            child = ET.SubElement(self.loc, 'text')
            child.text = ET.CDATA(str(a))
            self.__class__.encode_images(q, child)
            child = ET.SubElement(self.loc, 'feedback', attrib={'format': 'html'})
            child = ET.SubElement(self.loc.find('feedback'), 'text')
            child.text = ''
        for a in q['false_answers']:
            if self.single:
                self.loc.addnext(ET.SubElement(self, 'answer', attrib={
                    'fraction': '0', 'format': 'html'
                }))
            else:
                self.loc.addnext(ET.SubElement(self, 'answer', attrib={
                    'fraction': '-%f' % (100./len(q['correct_answers'])),
                    'format': 'html'
                }))
            self.loc = self.loc.getnext()
            child = ET.SubElement(self.loc, 'text')
            child.text = ET.CDATA(str(a))
            self.__class__.encode_images(q, child)
            child = ET.SubElement(self.loc, 'feedback', attrib={'format': 'html'})
            child = ET.SubElement(self.loc.find('feedback'), 'text')
            child.text = ''


class NumericalQuestion(MoodleQuestion):

    def set_additional(self, q):
        for a in q['correct_answers']:
            self.loc.addnext(ET.SubElement(self, 'answer', attrib={
                'fraction': '100', 'format': 'moodle_auto_format'
            }))
            self.loc = self.loc.getnext()
            child = ET.SubElement(self.loc, 'text')
            child.text = str(a)
            child = ET.SubElement(self.loc, 'feedback', attrib={'format': 'html'})
            child = ET.SubElement(self.loc.find('feedback'), 'text')
            child.text = ''
            child = ET.SubElement(self.loc, 'tolerance')
            try:
                child.text = str(q['tolerance'])
            except Exception:
                child.text = '0'

        self.loc.addnext(ET.SubElement(self, 'unitgradingtype'))
        self.loc = self.loc.getnext()
        self.loc.text = '0'

        self.loc.addnext(ET.SubElement(self, 'unitpenalty'))
        self.loc = self.loc.getnext()
        self.loc.text = '0.1000000'

        self.loc.addnext(ET.SubElement(self, 'showunits'))
        self.loc = self.loc.getnext()
        self.loc.text = '3'

        self.loc.addnext(ET.SubElement(self, 'unitsleft'))
        self.loc = self.loc.getnext()
        self.loc.text = '0'


class ShortanswerQuestion(MoodleQuestion):

    def set_additional(self, q):
        self.loc.addnext(ET.SubElement(self, 'usecase'))
        self.loc = self.loc.getnext()
        try:
            self.loc.text = str(int(q['usecase']))
        except KeyError:
            self.loc.text = '0'

        for a in q['correct_answers']:
            self.loc.addnext(ET.SubElement(self, 'answer', attrib={
                'fraction': '100', 'format': 'moodle_auto_format'
            }))
            self.loc = self.loc.getnext()
            child = ET.SubElement(self.loc, 'text')
            child.text = str(a)
            child = ET.SubElement(self.loc, 'feedback', attrib={'format': 'html'})
            child = ET.SubElement(self.loc.find('feedback'), 'text')
            child.text = ''


class EssayQuestion(MoodleQuestion):

    def set_additional(self, q):
        self.loc.addnext(ET.SubElement(self, 'responseformat'))
        self.loc = self.loc.getnext()
        self.loc.text = 'noinline'

        self.loc.addnext(ET.SubElement(self, 'responserequired'))
        self.loc = self.loc.getnext()
        self.loc.text = '0'

        self.loc.addnext(ET.SubElement(self, 'responsefieldlines'))
        self.loc = self.loc.getnext()
        self.loc.text = '15'

        self.loc.addnext(ET.SubElement(self, 'attachments'))
        self.loc = self.loc.getnext()
        self.loc.text = str(q['answer_files'][0])

        self.loc.addnext(ET.SubElement(self, 'attachmentsrequired'))
        self.loc = self.loc.getnext()
        self.loc.text = str(q['answer_files'][1])

        self.loc.addnext(ET.SubElement(self, 'filetypeslist'))
        self.loc = self.loc.getnext()
        self.loc.text = ''

        self.loc.addnext(ET.SubElement(self, 'graderinfo', attrib={'format': 'html'}))
        self.loc = self.loc.getnext()
        child = ET.SubElement(self.loc, 'text')
        child.text = ''

        self.loc.addnext(ET.SubElement(self, 'responsetemplate', attrib={'format': 'html'}))
        self.loc = self.loc.getnext()
        child = ET.SubElement(self.loc, 'text')
        child.text = ''


class MatchingQuestion(MoodleQuestion):

    def set_additional(self, q):
        self.loc.addnext(ET.SubElement(self, 'shuffleanswers'))
        self.loc = self.loc.getnext()
        self.loc.text = str(bool(SHUFFLE)).lower()

        self.feedback()

        for k, v in q['correct_answers'].items():
            self.loc.addnext(ET.SubElement(self, 'subquestion', attrib={'format': 'html'}))
            self.loc = self.loc.getnext()
            child = ET.SubElement(self.loc, 'text')
            child.text = ET.CDATA(str(k))
            self.__class__.encode_images(q, child)
            child = ET.SubElement(self.loc, 'answer')
            child = ET.SubElement(child, 'text')
            child.text = ET.CDATA(str(v))
            self.__class__.encode_images(q, child)

        try:
            for a in q['false_answers']:
                self.loc.addnext(ET.SubElement(self, 'subquestion', attrib={'format': 'html'}))
                self.loc = self.loc.getnext()
                child = ET.SubElement(self.loc, 'text')
                child.text = ''
                child = ET.SubElement(self.loc, 'answer')
                child = ET.SubElement(child, 'text')
                child.text = ET.CDATA(str(a))
                self.__class__.encode_images(q, child)
        except Exception:
            pass


class GapselectQuestion(MoodleQuestion):

    @staticmethod
    def insert_indices(q, el):
        for k, v in q['correct_answers'].items():
            pattern = r'(?<=\[\[){value}(?=\]\])'.format(value=re.escape(str(v[0])))
            el.text = re.sub(pattern, str(k), el.text)

    def set_option(self, a, g):
        self.loc.addnext(ET.SubElement(self, 'selectoption'))
        self.loc = self.loc.getnext()
        child = ET.SubElement(self.loc, 'text')
        child.text = ET.CDATA(a)
        child = ET.SubElement(self.loc, 'group')
        child.text = g

    def set_additional(self, q):
        self.loc.addnext(ET.SubElement(self, 'shuffleanswers'))
        self.loc = self.loc.getnext()
        self.loc.text = str(bool(SHUFFLE)).lower()

        self.feedback()

        self.loc.addnext(ET.SubElement(self, 'shownumcorrect'))
        self.loc = self.loc.getnext()

        # Modify question text indices
        self.__class__.insert_indices(q, self.qt_text)

        # Add options
        for k, v in q['correct_answers'].items():
            self.set_option(str(v[0]), str(k))

        for k, v in q['false_answers'].items():
            for i in v:
                self.set_option(str(i), str(k))


class DdimageortextQuestion(MoodleQuestion):

    def set_additional(self, q):
        self.loc.addnext(ET.SubElement(self, 'shuffleanswers'))
        self.loc = self.loc.getnext()
        self.loc.text = str(bool(SHUFFLE)).lower()

        self.feedback()

        self.loc.addnext(ET.SubElement(self, 'shownumcorrect'))
        self.loc = self.loc.getnext()

        self.loc.addnext(ET.SubElement(self, 'file', attrib={'name': q['img_files'][0], 'encoding': 'base64'}))
        self.loc = self.loc.getnext()

        with open(f'{BASE_PATH}/databases/{DB.name}/img/' + q['img_files'][0], 'rb') as rf:
            b64 = base64.b64encode(rf.read())
        self.loc.text = b64.decode('utf-8')

        for a in q['correct_answers']:
            self.loc.addnext(ET.SubElement(self, 'drag'))
            self.loc = self.loc.getnext()
            child = ET.SubElement(self.loc, 'no')
            child.text = str(q['correct_answers'].index(a)+1)
            child = ET.SubElement(self.loc, 'text')
            child.text = ET.CDATA(a)
            child = ET.SubElement(self.loc, 'draggroup')
            child.text = '1'

        for k, v in q['drops'].items():
            self.loc.addnext(ET.SubElement(self, 'drop'))
            self.loc = self.loc.getnext()
            child = ET.SubElement(self.loc, 'text')
            child.text = ''
            child = ET.SubElement(self.loc, 'no')
            child.text = str(k)
            child = ET.SubElement(self.loc, 'choice')
            child.text = str(k)
            child = ET.SubElement(self.loc, 'xleft')
            child.text = str(v[0])
            child = ET.SubElement(self.loc, 'ytop')
            child.text = str(v[1])


class CalculatedQuestion(MoodleQuestion):

    @staticmethod
    def count_decimals(arr):
        pattern = r'(?<=\.)[0-9e+-]*'
        
        def get_len(n):
            if np.int0(n) == n:
                return 0
            elif not re.search(r'e', str(n)):
                return len(re.search(pattern, str(n)).group())
            elif re.search(r'e\+', str(n)):
                return 0
            elif re.search(r'e\-', str(n)):
                return int(re.search(r'(?<=e\-)[0-9]+', str(n)).group()) - 1
            else:
                raise ValueError
        get_lens = np.vectorize(get_len)
    
        lens = get_lens(arr)
        return np.max(lens)

    def set_additional(self, q):
        self.loc.addnext(ET.SubElement(self, 'synchronize'))
        self.loc = self.loc.getnext()
        self.loc.text = '0'

        self.loc.addnext(ET.SubElement(self, 'single'))
        self.loc = self.loc.getnext()
        self.loc.text = '0'

        self.loc.addnext(ET.SubElement(self, 'shuffleanswers'))
        self.loc = self.loc.getnext()
        self.loc.text = str(bool(SHUFFLE)).lower()

        self.loc.addnext(ET.SubElement(self, 'answernumbering'))
        self.loc = self.loc.getnext()
        self.loc.text = 'abc'

        self.feedback()

        self.loc.addnext(ET.SubElement(self, 'answer', attrib={
            'fraction': "100"
        }))
        self.loc = self.loc.getnext()
        child = ET.SubElement(self.loc, 'text')
        child.text = q['correct_answers'][0]
        child = ET.SubElement(self.loc, 'tolerance')
        child.text = str(q['tolerance'][0])
        child = ET.SubElement(self.loc, 'tolerancetype')
        if q['tolerance'][1] == 'relative':
            child.text = '1'
        elif q['tolerance'][1] == 'nominal':
            child.text = '2'
        elif q['tolerance'][1] == 'geometric':
            child.text = '3'
        child = ET.SubElement(self.loc, 'correctanswerformat')
        child.text = '1'
        child = ET.SubElement(self.loc, 'correctanswerlength')
        child.text = str(q['tolerance'][2])

        child = ET.SubElement(self.loc, 'feedback', attrib={
            'format': "html"
        })
        child = ET.SubElement(child, 'text')
        child.text = ''

        self.loc.addnext(ET.SubElement(self, 'unitgradingtype'))
        self.loc = self.loc.getnext()
        self.loc.text = '0'

        self.loc.addnext(ET.SubElement(self, 'unitpenalty'))
        self.loc = self.loc.getnext()
        self.loc.text = '0.1000000'

        self.loc.addnext(ET.SubElement(self, 'showunits'))
        self.loc = self.loc.getnext()
        self.loc.text = '3'

        self.loc.addnext(ET.SubElement(self, 'unitsleft'))
        self.loc = self.loc.getnext()
        self.loc.text = '0'

        self.loc.addnext(ET.SubElement(self, 'dataset_definitions'))
        self.loc = self.loc.getnext()
        
        # Create all vars
        code = f'from databases.{DB.name}.random_vars.rv_{q["name"]} import *'
        rvn = {}
        exec(code, rvn)
        for v in q['vars']:
            datadef = ET.SubElement(self.loc, 'dataset_definition')

            child = ET.SubElement(datadef, 'status')
            subchild = ET.SubElement(child, 'text')
            subchild.text = 'private'

            child = ET.SubElement(datadef, 'name')
            subchild = ET.SubElement(child, 'text')
            subchild.text = f'{v}'

            child = ET.SubElement(datadef, 'type')
            child.text = 'calculated'

            child = ET.SubElement(datadef, 'distribution')
            subchild = ET.SubElement(child, 'text')
            subchild.text = 'uniform'

            child = ET.SubElement(datadef, 'minimum')
            subchild = ET.SubElement(child, 'text')
            subchild.text = f'{np.floor(np.min(rvn[v]))}'

            child = ET.SubElement(datadef, 'maximum')
            subchild = ET.SubElement(child, 'text')
            subchild.text = f'{np.ceil(np.max(rvn[v]))}'

            child = ET.SubElement(datadef, 'decimals')
            subchild = ET.SubElement(child, 'text')
            decimals = self.__class__.count_decimals(rvn[v])
            subchild.text = str(decimals)

            child = ET.SubElement(datadef, 'itemcount')
            child.text = str(len(rvn[v]))

            d_items = ET.SubElement(datadef, 'dataset_items')

            for i, n in zip(rvn[v], range(len(rvn[v]))):
                child = ET.SubElement(d_items, 'dataset_item')
                subchild = ET.SubElement(child, 'number')
                subchild.text = str(n+1)
                subchild = ET.SubElement(child, 'value')
                if decimals == 0:
                    subchild.text = str(np.int0(i))
                else:
                    subchild.text = str(i)

            child = ET.SubElement(datadef, 'number_of_items')
            child.text = str(len(rvn[v]))


def create_xml(exam, filename='import.xml', mode='terminal', questions=None):
    # Create directory
    try:
        os.mkdir(f'{BASE_PATH}/databases/{DB.name}/exams/{exam}')
    except FileExistsError:
        pass
    # Possibly adjust filename
    if filename[-4:] != '.xml':
        filename += '.xml'
    # Don't overwrite existing files
    version = 0
    pattern = re.compile(r'^.+?(?=[-0-9]*\.xml)')
    while filename in os.listdir(f'{BASE_PATH}/databases/{DB.name}/exams/{exam}'):
        version += 1
        m = re.match(pattern, filename)
        filename = m.group() + f'-{version}.xml'

    # Create XML base document
    xml_string = (
        '<?xml version="1.0"?>\n'
        '<quiz>\n\n'
        '<!-- question: 0  -->\n'
        '  <question type="category">\n'
        '    <category>\n'
        f'      <text>$course$/top/{exam}</text>\n'
        '    </category>\n'
        '    <info format="moodle_auto_format">\n'
        '      <text></text>\n'
        '    </info>\n'
        '    <idnumber></idnumber>\n'
        '  </question>\n\n'
        '</quiz>'
    )
    root = ET.XML(xml_string)

    def gather_info(ql):
        time_est_total = sum([QUESTIONS.find_one({'name': q})['time_est']
                    for q in ql])
        difficulty_avg = np.round(np.mean(
            [QUESTIONS.find_one({'name': q})['difficulty'] for q in ql]), 2)
        max_points = sum([QUESTIONS.find_one({'name': q})['points'] for q in ql])

        return (time_est_total, difficulty_avg, max_points)

    def questionlist_delete(ql):
        if len(ql) == 0:
            print('No questions in question list!')

            return None

        else:
            del_choice = fast_input(ql,
                                    ('Please input the name of the question '
                                     'you wish to delete.\n')
                                    )
            while del_choice not in ql:
                del_choice = fast_input(ql,
                                        ('Input the name of a question which '
                                         'is in the question list.\n')
                                        )
            ql.remove(del_choice)
            print(f'Question {del_choice} removed from question list.')

            return None

    def questionlist_auto(questions=None):
        if questions == None:
            # Open question list file
            listfile = input(
                ('Please specify whitespace-separated file which '
                 'contains the list of questions.\n')
            )
            while os.path.isfile(listfile) == False:
                listfile = input('Please input correct path/filename: ')
            with open(listfile, 'r') as rf:
                questionlist = rf.read().split()
        else:
            questionlist = questions

        # Clean question list
        questionlist_copy = copy.copy(questionlist)
        for q in questionlist_copy:
            if QUESTIONS.find_one({'name': q}) == None:
                questionlist.remove(q)
                print(
                    (f'Question {q} not in database! '
                      'Question removed from question list.')
                )

        # Get exam info
        info = gather_info(questionlist)

        return questionlist, info

    def questionlist_manual():
        # Category patterns for separated output
        if Q_CATEGORIES:
            cat_patterns = []
            for c in Q_CATEGORIES:
                cat_patterns.append(re.compile(r'%s\d+' % (c)))

        # Create question list
        questionlist = []
        info = ()
        q_choice = ''
        while q_choice.lower() != 'done' and q_choice.lower() != 'd':
            q_choice = input(('\nPlease input the name of the next question '
                                   "you wish to add.\nInput 'done' if the question "
                                   "list is complete.\nInput 'delete' if you want "
                                   'to remove a question from the list.\n'))

            if q_choice in questionlist:
                print(f'Question {q_choice} already in question list!')
            elif q_choice.lower() == 'delete' or q_choice.lower() == 'del':
                questionlist_delete(questionlist)
            elif (QUESTIONS.find_one({'name': q_choice}) == None and
                  q_choice.lower() != 'done' and q_choice.lower() != 'd'):
                print(f'Question {q_choice} not in database!')
            elif QUESTIONS.find_one({'name': q_choice}) != None:
                questionlist.append(q_choice)

                # Question list status
                if Q_CATEGORIES:
                    for r in cat_patterns:
                        print(list(filter(r.match, questionlist)))
                else:
                    pprint(questionlist)

                # Print current exam info
                info = gather_info(questionlist)
                print('Current estimated time:', info[0],
                      '\nCurrent average difficulty:', info[1],
                      '\nCurrent maximum points:', info[2])
            
        return questionlist, info

    # Choose question list creation mode
    if mode == 'terminal':
        mode_choice = fast_input(['auto', 'manual'],
                                 ('Please select a mode for question list creation. '
                                  "(Available: 'auto' or 'manual')\n")
                                 )
        if mode_choice == 'auto':
            questionlist, info = questionlist_auto()
        elif mode_choice == 'manual':
            questionlist, info = questionlist_manual()
    elif mode == 'gui':
        questionlist, info = questionlist_auto(questions)

    # Append XML
    for q in questionlist:
        q_dict = QUESTIONS.find_one({'name': q})
        try:
            q_el = eval((
                f'{q_dict["moodle_type"].capitalize()}'
                f'Question(attrib={{"type": "{q_dict["moodle_type"]}"}})'
                        ))
            q_el.set_defaults(q_dict)
            q_el.set_additional(q_dict)
            root.append(q_el)
        except:
            print(f'Question {q} has errors!')

    with open(f'{BASE_PATH}/databases/{DB.name}/exams/{exam}/{filename}', 'w') as wf:
        wf.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        wf.write((f'<!-- Estimated time: {info[0]}, '
                  f'average difficulty: {info[1]}, '
                  f'maximum possible points: {info[2]} -->\n')
                 )
        wf.write(ET.tostring(root, pretty_print=True).decode('utf-8'))

    print('Import file successfully created.')

    return questionlist, info
