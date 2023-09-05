# Gtk Modules
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
# Poodle modules
from poodle import config
import gui.windows
# Other modules
import re
import numpy as np
import pandas as pd


class QuestionTreeview(Gtk.TreeView):
    """
    Dependencies: Gtk, Gdk, config, gui.windows, gui.dialogs, re, numpy, pandas
    """

    def __init__(self, parent):

        super().__init__()
        self.parent_window = parent

        self.build_table(*self.load_data())

        self.connect('key-press-event', self.on_key_press)

    def load_data(self):

        # Convert numpy data types to native Python types for Gtk.ListStore
        def numpy_to_native_types(df) -> list:
            native_types = []
            for c in df.columns:
                if df[c].isna().all():
                    native_types.append(str)
                elif df[c].dtype == np.dtypes.ObjectDType:
                    native_types.append(str)
                elif df[c].dtype == np.float64:
                    native_types.append(float)
                elif df[c].dtype == np.int64:
                    native_types.append(int)
                else:
                    raise TypeError

            return native_types
        # Create data for Gtk.ListStore
        def row_to_list(df):
            for row in df.values.tolist():
                yield [x for x in row[:4]] + [str(x) for x in row[4:]]

        # Generate dataframe
        exam_list = sorted([e['name'] for e in config.EXAMS.find()])
        df = pd.DataFrame(
            sorted(
            [
             [q['name'], q['difficulty'], q['time_est']] +
             [round(q['in_exams'][e] / q['points'], 2)
              if e in q['in_exams'] else '.' for e in exam_list
             ]
             for q in config.QUESTIONS.find() if q['name'][-2:] != '00'
            ]),
            columns = ['question', 'difficulty', 'time_est'] + exam_list
        )
        # Make exam appearance counter
        transform = lambda x: int(type(x) == float)
        appearances = df[exam_list].applymap(transform).sum(axis=1)
        df.insert(1, 'appearances', appearances.astype('int64'))

        data = row_to_list(df)
        # Empty QUESTIONS collection would raise TypeError in numpy_to_native_types
        if df.empty:
            column_types = [str, int, int, int]
        else:
            column_types = numpy_to_native_types(df)
        column_names = [
            'question', 'appearances', 'difficulty', 'time__est'
            ] + list(df.columns)[4:]

        return data, column_types, column_names

    def build_table(self, data, list_store_cols, treeview_cols) -> None:

        self.question_liststore = Gtk.ListStore(*list_store_cols)
        for row in data:
            self.question_liststore.append(row)
        # Create filter
        self.filter = self.question_liststore.filter_new()
        self.filter.set_visible_func(self.filter_questions)
        # Set filter as model for treeview
        self.set_model(self.filter)

        for i, column_title in enumerate(treeview_cols):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            self.append_column(column)

    # Create window for new question
    def new_question(self) -> None:

        dialog = gui.dialogs.NewQuestionDialog(self.parent_window)
        question_content = dialog._run()
        if question_content:
            # Open new window with empty question of chosen Moodle type
            new_window = gui.windows.QuestionWindow(self.parent_window, question_content)
            # Make certain fields editable
            new_window.notebook.question_grid.name_field.set_editable(True)
            new_window.notebook.question_grid.family_type_field.set_editable(True)
            new_window.show_all()

    # Show selected question in new window
    def view_question(self) -> None:

        selected_row = self.get_selection()
        model, treeiter = selected_row.get_selected()
        question_name = model[treeiter][0]
        question_content = config.QUESTIONS.find_one({'name': question_name})
        question_content.pop('_id')

        new_window = gui.windows.QuestionWindow(self.parent_window, question_content)
        new_window.show_all()

    # Remove selected question from database
    def delete_question(self) -> None:

        return 0

    # Add questions to exam
    def add_to_exam(self) -> None:

        # Create ExamWindow if it doesn't exist already
        if not hasattr(self.parent_window, 'exam_window'):
            dialog = gui.dialogs.NewExamDialog(self.parent_window)
            exam_started = dialog._run()
            # Exit function if CANCEL is pressed
            if not exam_started:
                return None

        # Add question name to exam window
        selected_row = self.get_selection()
        model, treeiter = selected_row.get_selected()
        question_name = model[treeiter][0]
        self.parent_window.exam_window.add_question(question_name)

    # Filter questions based on search defined in control panel
    def filter_questions(self, model, iterator, data):

        try:
            search = self.parent_window.control.search_entry.get_text()
            field = self.parent_window.control.fields_combo.get_active_text()
        # Control panel doesn't exist when treeview is initialized
        except AttributeError:
            search = None
            field = None

        # Apply different filters depending on field choice
        # Numeric fields all follow the same filter routine
        numeric = [
            0, 'appearances', 'difficulty', 'time_est'
        ]
        if search is None and field is None:
            return True
        elif search == '':
            return True
        elif field == 'name':
            return bool(re.search(search, model[iterator][0]))
        elif (
            field == 'question' or
            field == 'moodle_type' or
            field == 'family_type'
        ):
            question = config.QUESTIONS.find_one({'name': model[iterator][0]})
            return bool(re.search(search, question[field]))
        elif field in numeric:
            # Check for allowed math expressions
            is_expression = bool(re.match(r'\s*([<>]=?|\!=)\s*\d+\.?\d*\s*$', search))
            if is_expression:
                return eval(str(model[iterator][numeric.index(field)]) + search)
            else:
                return str(model[iterator][numeric.index(field)]) == search
        else:
            return True

    # Handle button presses
    def on_button_press(self, button) -> None:

        button_name = button.get_property('label')

        match button_name:
            case 'New':
                self.new_question()
            case 'View':
                self.view_question()
            case 'Delete':
                self.delete_question()
            case 'Add to exam':
                self.add_to_exam()
            case 'Filter':
                self.filter.refilter()

    # Handle key presses
    def on_key_press(self, treeview, event) -> None:

        key_name = Gdk.keyval_name(event.keyval)

        match key_name:
            case 'n':
                self.new_question()
            case 'v':
                self.view_question()
            case 'Return':
                self.view_question()
            case 'd':
                self.delete_question()
            case 'a':
                self.add_to_exam()
            case 'f':
                self.filter.refilter()


class ExamTreeview(Gtk.TreeView):
    """
    Dependencies: Gtk, Gdk, config, gui.windows, re, numpy, pandas
    """

    def __init__(self, parent):

        super().__init__()
        self.parent_window = parent

        self.build_table(*self.load_data())

        self.connect('key-press-event', self.on_key_press)

    def load_data(self):

        # Convert numpy data types to native Python types for Gtk.ListStore
        def numpy_to_native_types(df) -> list:
            native_types = []
            for c in df.columns:
                if df[c].isna().all():
                    native_types.append(str)
                elif df[c].dtype == np.dtypes.ObjectDType:
                    native_types.append(str)
                elif df[c].dtype == np.float64:
                    native_types.append(float)
                elif df[c].dtype == np.int64:
                    native_types.append(int)
                else:
                    raise TypeError

            return native_types
        # Create data for Gtk.ListStore
        def row_to_list(df):
            for row in df.values.tolist():
                yield [x for x in row]

        # Generate dataframe
        df = pd.DataFrame(
            sorted(
            [
             [
              e['name'], e['points_max'], len(e['questions']),
              e['difficulty_avg'], e['time_est']
             ] for e in config.EXAMS.find()
            ]),
            columns = [
                'exam', 'points_max', 'questions', 'difficulty', 'time_est'
            ]
        )
        # Insert column for average achieved points
        points_avg = []
        for e in df['exam']:
            try:
                exam = config.EXAMS.find_one({'name': e})
                # print(exam)
                # print(exam['question_avgs'].values())
                exam_avg = np.nansum(list(exam['question_avgs'].values()))
                points_avg.append(exam_avg)
            except KeyError:
                exam_avg = 0.0
                points_avg.append(exam_avg)
        df.insert(2, 'points_avg', np.float64(points_avg))
        df = df.round(2)

        data = row_to_list(df)
        # Empty EXAMS collection would raise TypeError in numpy_to_native_types
        if df.empty:
            column_types = [str, float, float, int, float, float]
        else:
            column_types = numpy_to_native_types(df)
        column_names = [
            'name', 'points__max', 'points__avg', 'questions',
            'difficulty', 'time__est'
        ]

        return data, column_types, column_names

    def build_table(self, data, list_store_cols, treeview_cols) -> None:

        self.exam_liststore = Gtk.ListStore(*list_store_cols)
        for row in data:
            self.exam_liststore.append(row)
        # Create filter
        self.filter = self.exam_liststore.filter_new()
        self.filter.set_visible_func(self.filter_exams)
        # Set filter as model for treeview
        self.set_model(self.filter)

        for i, column_title in enumerate(treeview_cols):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            # Format float numbers
            # if column_title == 'points_max':
                # column.set_cell_data_func(
                    # renderer,
                    # lambda col, cell, model, iter, unused:
                    # cell.set_property("text", "%g" % model.get(iter, 0)[0])
                # )
            ## CURRENTLY NOT WORKING
            self.append_column(column)

    # Create window for new exam
    def new_exam(self) -> None:

        return 0

    # Show selected exam in new window
    def view_exam(self) -> None:

        return 0

    # Remove selected exam from database
    def delete_exam(self) -> None:

        return 0

    # Evaluate selected exam
    def evaluate_exam(self) -> None:

        return 0

    # Filter questions based on search defined in control panel
    def filter_exams(self, model, iterator, data):

        try:
            search = self.parent_window.control.search_entry.get_text()
            field = self.parent_window.control.fields_combo.get_active_text()
        # Control panel doesn't exist when treeview is initialized
        except AttributeError:
            search = None
            field = None

        # Apply different filters depending on field choice
        # Numeric fields all follow the same filter routine
        numeric = [
            0, 'points_max', 'points_avg', 'questions', 'difficulty', 'time_est'
        ]
        if search is None and field is None:
            return True
        elif search == '':
            return True
        elif field == 'name':
            return bool(re.search(search, model[iterator][0]))
        elif field in numeric:
            # Check for allowed math expressions
            is_expression = bool(re.match(r'\s*([<>]=?|\!=)\s*\d+\.?\d*\s*$', search))
            if is_expression:
                return eval(str(model[iterator][numeric.index(field)]) + search)
            else:
                return str(model[iterator][numeric.index(field)]) == search
        else:
            return True

    # Handle button presses
    def on_button_press(self, button) -> None:

        button_name = button.get_property('label')

        match button_name:
            case 'New':
                self.new_exam()
            case 'View':
                self.view_exam()
            case 'Delete':
                self.delete_exam()
            case 'Evaluate':
                self.evaluate_exam()
            case 'Filter':
                self.filter.refilter()

        return 0

    # Handle key presses
    def on_key_press(self, treeview, event) -> None:

        key_name = Gdk.keyval_name(event.keyval)

        match key_name:
            case 'n':
                self.new_exam()
            case 'v':
                self.view_exam()
            case 'Return':
                self.view_exam()
            case 'd':
                self.delete_exam()
            case 'e':
                self.evaluate_exam()
            case 'f':
                self.filter.refilter()


class TableTreeView(Gtk.TreeView):
    """
    Dependencies: Gtk, Gdk, gui.grids, gui.dialogs
    """

    def __init__(self, parent, table: list):

        super().__init__()
        self.parent_window = parent
        self.build_table(table)

        self.connect('key-press-event', self.on_key_press)

    def build_table(self, table: list):
        self.liststore = Gtk.ListStore(*([str] * len(table[0])))
        for row in table[1:]:
            self.liststore.append(row)
        self.set_model(self.liststore)

        for i, column_title in enumerate(table[0]):
            renderer = Gtk.CellRendererText(editable=True)
            renderer.connect('edited', self.cell_edited, self.liststore, i)
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            self.append_column(column)

    def cell_edited(self, widget, row, text, model, column):

        model[row][column] = text

    # use with Gtk.ListStore.foreach()
    @staticmethod
    def insert_rows(model, row, iterator, table):
        table.append(model[row][:])

    def save_table(self, button):

        output_table = []
        # Columns
        columns = [x.get_property('title') for x in self.get_columns()]
        output_table.append(columns)
        # Rows
        self.liststore.foreach(self.insert_rows, output_table)

        key = self.parent_window.table_key
        notebook = self.parent_window.parent_window.notebook
        question_grid = notebook.question_grid
        # Update data
        question_grid.tables_field.data[key] = output_table
        # Ask whether entire question should be saved
        self.parent_window.parent_window.control.on_save_clicked(button)

    def edit_columns(self, button):

        dialog = gui.dialogs.EditColumnsDialog(self.parent_window, self)
        dialog._run()

    def add_row(self, button):

        columns = self.liststore.get_n_columns()
        self.liststore.append([''] * columns)

    def remove_row(self, button):

        n_rows = self.liststore.iter_n_children()
        if n_rows > 1:
            last_row = self.liststore.get_iter(n_rows-1)
            self.liststore.remove(last_row)

    # Keyboard shortcuts
    def on_key_press(self, treeview, event):

        key_name = Gdk.keyval_name(event.keyval)

        match key_name:
            case 'e':
                self.edit_columns(None)
            case 'a':
                self.add_row(None)
            case 'r':
                self.remove_row(None)
