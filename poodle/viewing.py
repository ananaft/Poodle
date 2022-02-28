from config import *

from pprint import pprint
import re
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter.font import Font
import threading
import pyperclip


def view(collection, search=None, field='name'):
    """
    Simple function to examine questions from the database. Pass 'any' to field
    argument to search all available question fields for (non-list) search
    argument.

    Arguments:
    ----------
    collection (var):
      Determines which collection is being searched.
    search (any/list):
      Search criterion that will be applied to the field. If passed as list,
      multiple criteria will be applied.
    field (str/list):
      Question field to look through with search argument. If passed as list,
      multiple fields will be looked through.

    --------------------
    Dependencies: config, pprint, re
    """

    if field == 'any':
        # Determine all existing question fields
        fields = {}
        for q in collection.find():
            fields |= q.keys()
        fields.discard('_id')
        for f in fields:
            try:
                for q in collection.find({f: re.compile(search)}):
                    pprint(q)
            except:
                for q in collection.find({f: search}):
                    pprint(q)
    elif not (type(search) == list or type(field) == list):
        if search==None:
            for q in collection.find():
                pprint(q)
        else:
            try:
                for q in collection.find({field: re.compile(search)}):
                    pprint(q)
            except:
                for q in collection.find({field: search}):
                    pprint(q)
    else:
        # Transform into list if needed
        if type(search) != list:
            search = [search] * len(field)
        elif type(field) != list:
            field = [field] * len(search)
        # Combine lists into dictionary
        dictionary = dict(zip(field, search))
        # Turn strings into compiled regular expressions
        for q in collection.find(
                {k: (re.compile(v) if type(v)==str else v)
                 for (k, v) in dictionary.items()}
        ):
            pprint(q)


def overview(candidates=None):
    """
    Simple function to receive an overview of which questions appear in which
    exams. '.' denotes questions which did not appear in the regarding exam.
    Missing values (NaN) denote questions which appeared in the regarding exam,
    but whose scores have not been captured.

    Arguments:
    ----------
    candidates (bool):
      If set to True, will only show possible candidates for inclusion in the
      next exam and will exclude questions that appeared in the last exam or in
      the mock exam.

    --------------------------------------------------------------------------
    Dependencies: config, numpy, pandas, tkinter, threading, pprint, pyperclip
    """

    # Generate dataframe
    exam_list = sorted([e['name'] for e in EXAMS.find()])
    data = pd.DataFrame(sorted(
        [
            [q['name'], q['difficulty'], q['time_est']] +
            [round(q['in_exams'][e] / q['points'], 2)
             if e in q['in_exams'] else '.' for e in exam_list
            ]
            for q in QUESTIONS.find() if q['name'][-2:] != '00'
        ]),
        columns = ['question', 'difficulty', 'time'] + exam_list
    )
    # Make exam appearance boolean
    transform = lambda x: int(type(x) == float)
    appearances = data[exam_list].applymap(transform).sum(axis=1)
    data.insert(1, 'appearances', appearances)

    if candidates:
        data = data[(data['mock'] == '.') & (data[exam_list[-2]] == '.')]
        data = data.drop(labels=[exam_list[-2], 'mock'], axis=1)

    # Create GUI
    def OverviewThread():

        class Overview:

            def __init__(self, master, dataframe):
                # Setup
                self.root = master
                self.root.minsize(width=800, height=600)
                self.root.title('Overview')
                self.main = tk.Frame(self.root)
                self.main.pack(fill='both', expand=1)

                # Data
                self.df = dataframe
                self.columns = np.array([list(self.df.columns)])
                self.str_data = np.array(self.df.applymap(str))
                self.str_data = np.vstack((self.columns, self.str_data))
                vfunc = np.vectorize(len)
                self.len_data = vfunc(self.str_data)
                self.len_max = [np.max(x) for x in self.len_data.T]
                vfunc = np.vectorize(str.rjust)
                self.str_data = np.array(
                    [vfunc(c, m) for c, m in zip(self.str_data.T, self.len_max)]
                ).T

                self._fill()

            def _fill(self):
                self.canvas = tk.Canvas(self.main)
                self.canvas.pack(fill='both', expand=1)

                self._init_scroll()
                self._init_lb()
                self._pack_config_scroll()
                self._fill_lb()

            # Scrollbars
            def _init_scroll(self):
                self.yscrollbar = tk.Scrollbar(self.canvas,
                                               orient='vertical')
                self.xscrollbar = tk.Scrollbar(self.canvas,
                                               orient='horizontal')

            def _pack_config_scroll(self):
                self.yscrollbar.config(command=self.lb.yview)
                self.xscrollbar.config(command=self.lb.xview)
                self.yscrollbar.pack(side=tk.RIGHT, fill='y')
                self.xscrollbar.pack(side='bottom', fill='x')

            # Listbox
            def _init_lb(self):
                self.lb = tk.Listbox(self.canvas, exportselection=0,
                                     yscrollcommand=self.yscrollbar.set,
                                     xscrollcommand=self.xscrollbar.set,
                                     font=Font(family='Droid Sans Mono', size=10))
                self.lb.bind('<Double-Button-1>', self.view_question)
                self.lb.bind('<Return>', self.view_question)
                self.lb.bind('<c>', self.copy_name)

            def _fill_lb(self):
                for line in self.str_data:
                    self.lb.insert(tk.END, " ".join(line))
                self.lb.pack(fill='both', expand=1)

            # Functions
            def view_question(self, x):
                self.row = int([i - 1 for i in self.lb.curselection()][0])
                try:
                    self.name = self.df.iloc[self.row,0]
                except:
                    return None
                self.window = tk.Toplevel(self.root)
                self.window.minsize(width=450, height=200)
                self.question = QUESTIONS.find_one({'name': self.name})
                self.infotext = self.name
                categories = ['question', 'moodle_type', 'correct_answers',
                              'tolerance', 'single', 'usecase', 'false_answers']
                for c in categories:
                    try:
                        if (type(self.question[c]) == list or
                            type(self.question[c]) == dict):
                                self.infotext = (
                                    self.infotext + '\n\n' + c + ':\n  ' +
                                    str(self.question[c])[1:-1].replace(', ', '\n  ')
                                )
                        else:
                            self.infotext = (
                                self.infotext + '\n\n' + c + ':\n' + self.question[c]
                            )
                    except:
                        pass
                self.info = tk.Label(self.window, wraplength=420, text=self.infotext)
                self.info['anchor'] = 'nw'
                self.info['justify'] = 'left'
                self.info.config(font=('Helvetica', 12))
                self.info.pack(fill='both', expand=1)

            def copy_name(self, x):
                self.row = int([i - 1 for i in self.lb.curselection()][0])
                try:
                    self.name = self.df.iloc[self.row,0]
                    pyperclip.copy(self.name)
                except:
                    return None

        root = tk.Tk()
        overview = Overview(root, data)
        root.mainloop()

    # Start GUI
    overview = threading.Thread(target=OverviewThread)
    overview.start()


def export_overview(path=BASE_PATH, filename='overview', candidates=None):
    """
    Export an overview of the database as a csv file. See overview() function's
    docstring for an explanation of cell values.

    Arguments:
    ----------
    path (str):
      Directory to which the output file will be saved.
    filename (str):
      Name of the output file.
    candidates (bool):
      If set to True, will only show possible candidates for inclusion in the
      next exam and will exclude questions that appeared in the last exam or in
      the mock exam.

    ---------------------------
    Dependencies: numpy, pandas
    """

    # Generate dataframe
    exam_list = sorted([e['name'] for e in EXAMS.find()])
    data = pd.DataFrame(sorted(
        [
            [q['name'], q['difficulty'], q['time_est']] +
            [np.round(q['in_exams'][e] / q['points'], 2)
             if e in q['in_exams'] else '.' for e in exam_list
            ]
            for q in QUESTIONS.find() if q['name'][-2:] != '00'
        ]),
        columns = ['question', 'difficulty', 'time'] + exam_list
    )
    appeared = pd.DataFrame(np.array(
        [[int(type(e) == float) for e in data[q]] for q in exam_list]).T
    )
    data.insert(1, 'appearances', appeared.sum(axis=1))

    if candidates:
        data = data[(data['mock'] == '.') & (data[exam_list[-2]] == '.')]
        data = data.drop(labels=[exam_list[-2], 'mock'], axis=1)

    # Export dataframe
    data.to_csv(f'{path}/{filename}.csv', na_rep='NaN')
    print(f'Overview saved as:\n{path}/{filename}.csv')
