from config import *
import gui.windows

from pprint import pprint
import re
import numpy as np
import pandas as pd
import threading
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


def view(collection, search=None, field='name'):
    """
    Simple function to examine questions from the database. Pass 'any' to field
    argument to search all available question fields for (non-list) search
    argument.

    Arguments:
    ----------
    collection (var):
      Determines which collection is being searched (QUESTIONS and EXAMS are standard).
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


def gtk_overview() -> None:
    """
    Dependencies: threading, gui.windows, Gtk
    """

    def run_overview() -> None:
        win = gui.windows.Overview()
        win.show_all()
        Gtk.main()

    thread = threading.Thread(target=run_overview)
    thread.daemon = True
    thread.start()


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
