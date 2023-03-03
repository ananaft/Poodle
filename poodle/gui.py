# from config import *

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
        self.grid.attach_next_to(self.control, self.scroll_window,
                                 Gtk.PositionType.BOTTOM, 1, 1)


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
        # question_content = QUESTIONS.find_one({'name': question_name})
        question_content = {
            'name': 'mytest0199',
            'moodle_type': 'multichoice',
            'question': 'Setzen Sie die Einkommensvariable in Fällen, in denen sie 0 ist, auf Missing. Sortieren Sie den Datensatz aufsteigend nach Einkommen. Ermitteln Sie das <i>Haushaltseinkommen</i> der Person mit dem fünftniedrigsten Einkommen.',
            'correct_answers': ['Richtig'],
            'false_answers': ['Falsch'],
            'single': 1,
            'points': 4,
            'difficulty': 1,
            'time_est': 1,
            'family_type': 'single',
            'in_exams': {'20190212': 3.5,
                         '20201108': 2}
        } ## TESTING
        
        if keyname == 'Return':
            new_window = QuestionWindow(question_content)
            new_window.show_all()


class ControlPanel(Gtk.ActionBar):

    def __init__(self):

        super().__init__()

        self.new_button = Gtk.Button(label='New')
        self.pack_start(self.new_button)

        self.view_button = Gtk.Button(label='View')
        self.pack_start(self.view_button)
        
        self.add_to_exam_button = Gtk.Button(label='Add to exam')
        self.pack_start(self.add_to_exam_button)

        # Filter functionality
        self.filter_button = Gtk.Button(label='Filter')
        self.pack_end(self.filter_button)

        question_fields = [
            'name',
            'question',
            'correct_answers'
        ] ## CHANGE TO DYNAMIC (maybe global var [maybe in config.json])
        self.fields_combo = Gtk.ComboBoxText()
        for f in question_fields:
            self.fields_combo.append_text(f)
        self.fields_combo.set_active(0)
        self.pack_end(self.fields_combo)
            
        self.search_entry = Gtk.Entry()
        self.pack_end(self.search_entry)


class QuestionWindow(Gtk.Window):

    def __init__(self, question_content: dict):

        super().__init__(title=question_content['name'])
        self.set_size_request(600, 400)

        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.add(self.grid)

        self.scroll_window = Gtk.ScrolledWindow()
        self.scroll_window.set_vexpand(True)
        self.notebook = QuestionView(question_content)
        self.scroll_window.add(self.notebook)

        self.control = ControlPanel()

        self.grid.attach(self.scroll_window, 0, 0, 1, 1)
        self.grid.attach_next_to(self.control, self.scroll_window,
                                 Gtk.PositionType.BOTTOM, 1, 1)


class QuestionView(Gtk.Notebook):

    def __init__(self, question_content: dict):

        super().__init__()

        match question_content['moodle_type']:
            case 'multichoice':
                self.question_grid = MultiChoiceQuestionGrid(question_content)
            case _:
                raise Exception
        self.append_page(self.question_grid, Gtk.Label(label='Question'))

        self.textview = Gtk.TextView()
        self.textbuffer = self.textview.get_buffer()
        self.textbuffer.set_text(pformat(question_content, indent=4))
        self.append_page(self.textview, Gtk.Label(label='Raw'))


class GeneralQuestionGrid(Gtk.Grid):

    def __init__(self, question_content: dict):

        super().__init__()
        self.set_column_spacing(100)
        self.set_row_spacing(20)

        self.name_label = Gtk.Label(label='name')
        self.attach(self.name_label, 0, 0, 1, 1)

        self.name_field = Gtk.Entry()
        self.name_field.set_hexpand(True)
        self.name_field.set_text(question_content['name'])
        self.name_field.set_editable(False) ## ~"free edit" button changes this
        self.attach_next_to(self.name_field, self.name_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.question_label = Gtk.Label(label='question')
        self.attach_next_to(self.question_label, self.name_label,
                            Gtk.PositionType.BOTTOM, 1, 1)

        self.question_field = Gtk.TextView(wrap_mode=Gtk.WrapMode(3))
        self.question_field.set_hexpand(True)
        self.question_buffer = self.question_field.get_buffer()
        self.question_buffer.set_text(question_content['question'])
        self.attach_next_to(self.question_field, self.question_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.points_label = Gtk.Label(label='points')
        self.attach_next_to(self.points_label, self.question_label,
                            Gtk.PositionType.BOTTOM, 1, 1)

        self. points_field = Gtk.Entry()
        self.points_field.set_hexpand(True)
        self.points_field.set_text(str(question_content['points']))
        self.attach_next_to(self.points_field, self.points_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.difficulty_label = Gtk.Label(label='difficulty')
        self.attach_next_to(self.difficulty_label, self.points_label,
                            Gtk.PositionType.BOTTOM, 1, 1)

        self. difficulty_field = Gtk.Entry()
        self.difficulty_field.set_hexpand(True)
        self.difficulty_field.set_text(str(question_content['difficulty']))
        self.attach_next_to(self.difficulty_field, self.difficulty_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.time_est_label = Gtk.Label(label='time_est')
        self.attach_next_to(self.time_est_label, self.difficulty_label,
                            Gtk.PositionType.BOTTOM, 1, 1)

        self. time_est_field = Gtk.Entry()
        self.time_est_field.set_hexpand(True)
        self.time_est_field.set_text(str(question_content['time_est']))
        self.attach_next_to(self.time_est_field, self.time_est_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.family_type_label = Gtk.Label(label='family_type')
        self.attach_next_to(self.family_type_label, self.time_est_label,
                            Gtk.PositionType.BOTTOM, 1, 1)

        self.family_type_field = Gtk.Entry()
        self.family_type_field.set_hexpand(True)
        self.family_type_field.set_text(question_content['family_type'])
        self.family_type_field.set_editable(False)
        self.attach_next_to(self.family_type_field, self.family_type_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.in_exams_label = Gtk.Label(label='in_exams')
        self.attach_next_to(self.in_exams_label, self.family_type_label,
                            Gtk.PositionType.BOTTOM, 1, 1)

        self.in_exams_field = SimpleDictGrid(question_content['in_exams'])
        self.attach_next_to(self.in_exams_field, self.in_exams_label,
                            Gtk.PositionType.RIGHT, 2, 1)


class MultiChoiceQuestionGrid(GeneralQuestionGrid):

    def __init__(self, question_content: dict):

        super().__init__(question_content)

        self.insert_row(2)
        self.correct_answers_label = Gtk.Label(label='correct_answers')
        self.attach(self.correct_answers_label, 0, 2, 1, 1)
        self.correct_answers_field = SimpleListGrid(question_content['correct_answers'])
        self.attach_next_to(self.correct_answers_field, self.correct_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.insert_row(3)
        self.false_answers_label = Gtk.Label(label='false_answers')
        self.attach(self.false_answers_label, 0, 3, 1, 1)
        self.false_answers_field = SimpleListGrid(question_content['false_answers'])
        self.attach_next_to(self.false_answers_field, self.false_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.insert_row(4)
        self.single_label = Gtk.Label(label='single')
        self.attach(self.single_label, 0, 4, 1, 1)
        self.single_field = Gtk.Entry()
        self.single_field.set_hexpand(True)
        self.single_field.set_text(str(question_content['single']))
        self.attach_next_to(self.single_field, self.single_label,
                            Gtk.PositionType.RIGHT, 2, 1)


class SimpleListGrid(Gtk.Grid):

    def __init__(self, list_field: list):

        super().__init__()
        self.set_row_spacing(10)

        for n, i in enumerate(list_field):
            entry = Gtk.Entry()
            entry.set_hexpand(True)
            entry.set_text(str(i))
            self.attach(entry, 0, n, 1, 1)

        self.n_rows = len(list_field)

        self.add_button = Gtk.Button(label='+')
        self.add_button.connect('clicked', self.add_row)
        self.attach_next_to(self.add_button, self.get_children()[-1],
                            Gtk.PositionType.BOTTOM, 1, 1)

    def add_row(self, button):

        entry = Gtk.Entry()
        entry.set_hexpand(True)
        self.insert_row(self.n_rows)
        self.attach(entry, 0, self.n_rows, 1, 1)
        entry.show()

        self.n_rows += 1


class SimpleDictGrid(Gtk.Grid):

    def __init__(self, dict_field: dict):

        super().__init__()
        self.set_column_spacing(50)
        self.set_row_spacing(10)

        for n, key in enumerate(dict_field.keys()):
            entry = Gtk.Entry()
            entry.set_hexpand(True)
            entry.set_text(key)
            self.attach(entry, 0, n, 1, 1)

        for n, value in enumerate(dict_field.values()):
            entry = Gtk.Entry()
            entry.set_hexpand(True)
            entry.set_text(str(value))
            self.attach(entry, 1, n, 1, 1)

        self.n_rows = len(dict_field.keys())

        self.add_button = Gtk.Button(label='+')
        self.add_button.connect('clicked', self.add_row)
        self.attach_next_to(self.add_button, self.get_children()[-2],
                            Gtk.PositionType.BOTTOM, 1, 1)

    def add_row(self, button):

        key_entry = Gtk.Entry()
        key_entry.set_hexpand(True)
        self.insert_row(self.n_rows)
        self.attach(key_entry, 0, self.n_rows, 1, 1)
        key_entry.show()

        value_entry = Gtk.Entry()
        value_entry.set_hexpand(True)
        self.attach_next_to(value_entry, key_entry,
                            Gtk.PositionType.RIGHT, 1, 1)
        value_entry.show()

        self.n_rows += 1


def gtk_overview() -> None:

    # # Generate dataframe
    # exam_list = sorted([e['name'] for e in EXAMS.find()])
    # df = pd.DataFrame(sorted(
    #     [
    #         [q['name'], q['difficulty'], q['time_est']] +
    #         [round(q['in_exams'][e] / q['points'], 2)
    #          if e in q['in_exams'] else '.' for e in exam_list
    #         ]
    #         for q in QUESTIONS.find() if q['name'][-2:] != '00'
    #     ]),
    #     columns = ['question', 'difficulty', 'time'] + exam_list
    # )
    # # Make exam appearance counter
    # transform = lambda x: int(type(x) == float)
    # appearances = df[exam_list].applymap(transform).sum(axis=1)
    # df.insert(1, 'appearances', appearances)
    df = pd.read_csv('/home/lukas/Nextcloud/poodle/databases/testing/questions.csv') ## TESTING

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
