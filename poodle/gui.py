from config import *

import pandas as pd
import numpy as np
from pprint import pformat
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Gdk


class Overview(Gtk.Window):

    def __init__(self, data, list_store_cols, treeview_cols):

        super().__init__(title='Overview')
        self.set_size_request(800, 600)
        self.connect('destroy', Gtk.main_quit)

        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.add(self.grid)

        self.scroll_window = Gtk.ScrolledWindow()
        self.scroll_window.set_vexpand(True)
        self.table = QuestionTable(data, list_store_cols, treeview_cols)
        self.scroll_window.add(self.table)
    
        self.control = ControlPanel()

        self.grid.attach(self.scroll_window, 0, 0, 1, 1)
        self.grid.attach_next_to(self.control, self.scroll_window, Gtk.PositionType.BOTTOM, 1, 1)


class QuestionTable(Gtk.TreeView):

    def __init__(self, data, list_store_cols, treeview_cols):

        super().__init__()

        self.question_liststore = Gtk.ListStore(*list_store_cols)
        for row in data:
            self.question_liststore.append(row)
        self.set_model(self.question_liststore)

        for i, column_title in enumerate(treeview_cols):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            column.set_sort_column_id(i)
            self.append_column(column)

        self.connect('key-press-event', self.on_key_press)

    def on_key_press(self, treeview, event) -> None:

        keyname = Gdk.keyval_name(event.keyval)
        selected_row = treeview.get_selection()
        model, treeiter = selected_row.get_selected()
        question_name = model[treeiter][0]
        question_content = pformat(QUESTIONS.find_one({'name': question_name}))
        # question_content = question_name ## TESTING
        
        if keyname == 'Return':
            new_win = QuestionPreview(question_name, question_content)
            new_win.show_all()


class ControlPanel(Gtk.ActionBar):

    def __init__(self):
        super().__init__()

        self.button1 = Gtk.Button(label='Action 1')
        self.button2 = Gtk.Button(label='Action 2')

        self.pack_start(self.button1)
        self.pack_end(self.button2)


class QuestionPreview(Gtk.Window):

    def __init__(self, question_name, question_content):

        super().__init__(title=question_name)
        self.set_size_request(600, 400)
        self.base = Gtk.ScrolledWindow()
        self.add(self.base)
        
        self.textview = Gtk.TextView()
        self.textbuffer = self.textview.get_buffer()
        self.textbuffer.set_text(question_content)
        self.base.add(self.textview)


def gtk_overview():

    # Generate dataframe
    exam_list = sorted([e['name'] for e in EXAMS.find()])
    df = pd.DataFrame(sorted(
        [
            [q['name'], q['difficulty'], q['time_est']] +
            [round(q['in_exams'][e] / q['points'], 2)
             if e in q['in_exams'] else '.' for e in exam_list
            ]
            for q in QUESTIONS.find() if q['name'][-2:] != '00'
        ]),
        columns = ['question', 'difficulty', 'time'] + exam_list
    )
    # Make exam appearance counter
    transform = lambda x: int(type(x) == float)
    appearances = df[exam_list].applymap(transform).sum(axis=1)
    df.insert(1, 'appearances', appearances)
    # df = pd.read_csv('/home/lukas/Nextcloud/poodle/databases/testing/questions.csv') ## TESTING

    # Convert numpy data types to native Python types for Gtk.ListStore
    def numpy_to_native(numpy_type: type) -> type:
        if numpy_type == np.int64:
            return int
        elif numpy_type == np.object_:
            return str
        else:
            raise TypeError
    # Create data for Gtk.ListStore
    def row_to_list(dataframe):
        for row in dataframe.values.tolist():
            yield [x for x in row[:4]] + [str(x) for x in row[4:]]

    # Create arguments for Overview class
    column_types = [numpy_to_native(x.type) for x in list(df.dtypes)]
    column_names = ['question', 'appearances', 'difficulty', 'time_est'] +list(df.columns)[4:]
    data = row_to_list(df)

    # Initialize GUI
    win = Overview(data, column_types, column_names)
    win.show_all()
    Gtk.main()
