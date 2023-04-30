from config import *
from question import check_question

import pandas as pd
import numpy as np
import json
import time
import threading
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Gdk


class Overview(Gtk.Window):

    def __init__(self):

        super().__init__(title='Overview')
        self.set_size_request(800, 600)
        self.connect('destroy', Gtk.main_quit)

        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.add(self.grid)

        self.scroll_window = Gtk.ScrolledWindow()
        self.scroll_window.set_vexpand(True)
        self.table = QuestionTable(self)
        self.scroll_window.add(self.table)

        self.control = OverviewControlPanel(self)

        self.grid.attach(self.scroll_window, 0, 0, 1, 1)
        self.grid.attach_next_to(self.control, self.scroll_window,
                                 Gtk.PositionType.BOTTOM, 1, 1)

    def load_data(self):

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

        data = row_to_list(df)
        column_types = [numpy_to_native(x.type) for x in list(df.dtypes)]
        column_names = ['question', 'appearances', 'difficulty', 'time_est'] + list(df.columns)[4:]

        return data, column_types, column_names


class QuestionTable(Gtk.TreeView):

    def __init__(self, parent):

        super().__init__()
        self.parent_window = parent

        self.build_table(*self.parent_window.load_data())

        self.connect('key-press-event', self.on_key_press)

    def build_table(self, data, list_store_cols, treeview_cols) -> None:

        self.question_liststore = Gtk.ListStore(*list_store_cols)
        for row in data:
            self.question_liststore.append(row)
        self.set_model(self.question_liststore)

        for i, column_title in enumerate(treeview_cols):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(column_title, renderer, text=i)
            column.set_sort_column_id(i)
            self.append_column(column)

    # Create window for new question
    def new_question(self) -> None:

        # Fill question_content with default values for data types
        def default_fill(moodle_type: str, field_name: str, output_type: type):
            if output_type == str:
                return ''
            elif output_type == int:
                return 0
            elif output_type == float:
                return 0.0
            elif output_type == list:
                # Some SimpleListGrid fields without add button
                # need to be handled separately
                if moodle_type == 'essay' and field_name == 'answer_files':
                    return ['', '']
                elif moodle_type == 'calculated' and field_name == 'tolerance':
                    return ['', '', '']
                else:
                    return ['']
            elif output_type == dict:
                return {}

        question_content = {
            k: default_fill('general', k, v) for k, v in KEY_TYPES['general'].items()
        }
        question_content['name'] = 'New question'
        # Ask for moodle_type
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            message_type=Gtk.MessageType.OTHER,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=f'Please pick a Moodle type for the new question:'
        )
        # Add list of moodle types to dialog
        box = dialog.get_message_area()
        moodle_types = Gtk.ComboBoxText()
        for mt in KEY_TYPES.keys():
            if mt != 'general' and mt != 'optional':
                moodle_types.append_text(mt)
        moodle_types.set_active(0)
        box.pack_end(moodle_types, True, True, 10)
        box.show_all()
        # Create new question or cancel
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            # Set remaining fields based on moodle_type
            question_content['moodle_type'] = moodle_types.get_active_text()
            question_content.update({
                k: default_fill(question_content['moodle_type'], k, v) for k, v in
                KEY_TYPES[question_content['moodle_type']].items()
            })
            new_window = QuestionWindow(self.parent_window, question_content)
            # Make certain fields editable
            new_window.notebook.question_grid.name_field.set_editable(True)
            new_window.notebook.question_grid.family_type_field.set_editable(True)
            new_window.show_all()
        elif response == Gtk.ResponseType.CANCEL:
            pass
        dialog.destroy()

    # Show existing question
    def view_question(self) -> None:

        selected_row = self.get_selection()
        model, treeiter = selected_row.get_selected()
        question_name = model[treeiter][0]
        question_content = QUESTIONS.find_one({'name': question_name})
        question_content.pop('_id')

        new_window = QuestionWindow(self.parent_window, question_content)
        new_window.show_all()

    # Add questions to exam
    def add_to_exam(self) -> None:

        # Create ExamWindow if it doesn't exist already
        if not hasattr(self.parent_window, 'exam_window'):
            # Placeholder attribute so that ExamWindow __init__ throws no error
            self.parent_window.exam_window = None
            # Ask for exam name
            dialog = Gtk.MessageDialog(
                transient_for=self.parent_window,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK_CANCEL,
                text='Please enter exam name:'
            )
            box = dialog.get_message_area()
            name_entry = Gtk.Entry()
            box.pack_end(name_entry, True, True, 10)
            box.show_all()
            # Create exam or cancel
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                exam_name = name_entry.get_text()
                self.parent_window.exam_window = ExamWindow(
                    self.parent_window, exam_name
                )
                self.parent_window.exam_window.show_all()
            elif response == Gtk.ResponseType.CANCEL:
                pass
            dialog.destroy()
        # Add question name to exam window
        selected_row = self.get_selection()
        model, treeiter = selected_row.get_selected()
        question_name = model[treeiter][0]

        self.parent_window.exam_window.add_question(question_name)

    # Handle button presses
    def on_button_press(self, button) -> None:

        button_name = button.get_property('label')

        match button_name:
            case 'New':
                self.new_question()
            case 'View':
                self.view_question()
            case 'Add to exam':
                self.add_to_exam()

    # Handle key presses
    def on_key_press(self, treeview, event) -> None:

        key_name = Gdk.keyval_name(event.keyval)

        match key_name:
            case 'v':
                self.view_question()
            case 'Return':
                self.view_question()
            case 'n':
                self.new_question()
            case 'a':
                self.add_to_exam()


class OverviewControlPanel(Gtk.ActionBar):

    def __init__(self, parent):

        super().__init__()
        self.parent_window = parent
        self.table = self.parent_window.table

        self.new_button = Gtk.Button(label='New')
        self.new_button.connect('clicked', self.table.on_button_press)
        self.pack_start(self.new_button)

        self.view_button = Gtk.Button(label='View')
        self.view_button.connect('clicked', self.table.on_button_press)
        self.pack_start(self.view_button)

        self.add_to_exam_button = Gtk.Button(label='Add to exam')
        self.add_to_exam_button.connect('clicked', self.table.on_button_press)
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

    def __init__(self, parent, question_content: dict):

        super().__init__(title=question_content['name'])
        self.set_size_request(600, 400)
        self.parent_window = parent

        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.add(self.grid)

        self.scroll_window = Gtk.ScrolledWindow()
        self.scroll_window.set_vexpand(True)
        self.notebook = QuestionNotebook(question_content)
        self.scroll_window.add(self.notebook)

        self.control = QuestionControlPanel(self)

        self.grid.attach(self.scroll_window, 0, 0, 1, 1)
        self.grid.attach_next_to(self.control, self.scroll_window,
                                 Gtk.PositionType.BOTTOM, 1, 1)


class QuestionNotebook(Gtk.Notebook):

    def __init__(self, question_content: dict):

        super().__init__()

        match question_content['moodle_type']:
            case 'multichoice':
                self.question_grid = MultiChoiceQuestionGrid(question_content)
            case 'numerical':
                self.question_grid = NumericalQuestionGrid(question_content)
            case 'shortanswer':
                self.question_grid = ShortanswerQuestionGrid(question_content)
            case 'essay':
                self.question_grid = EssayQuestionGrid(question_content)
            case 'matching':
                self.question_grid = MatchingQuestionGrid(question_content)
            case 'gapselect':
                self.question_grid = GapselectQuestionGrid(question_content)
            case 'ddimageortext':
                self.question_grid = DDImageOrTextQuestionGrid(question_content)
            case 'calculated':
                self.question_grid = CalculatedQuestionGrid(question_content)
            case _:
                raise Exception
        self.append_page(self.question_grid, Gtk.Label(label='Question'))

        self.raw_page = RawQuestionText(question_content)
        self.append_page(self.raw_page, Gtk.Label(label='Raw'))

        self.connect('switch-page', self.on_switch_page)
        self.switch_counter = 0

    # Passing data between pages on switch
    def on_switch_page(self, notebook, page, page_num):

        page_titles = ['Question', 'Raw']

        if self.switch_counter > 0:

            # Update content of previous page and pass to new page
            new_content = self.get_nth_page(int(not page_num)).update_content()
            page.overwrite(new_content)

        self.switch_counter += 1


class QuestionControlPanel(Gtk.ActionBar):

    def __init__(self, parent):

        super().__init__()
        self.parent_window = parent
        self.overview = self.parent_window.parent_window
        self.table = self.overview.table

        self.save_button = Gtk.Button(label='Save')
        self.save_button.connect('clicked', self.on_save_clicked)
        self.pack_start(self.save_button)

        self.delete_button = Gtk.Button(label='Delete')
        self.delete_button.connect('clicked', self.on_delete_clicked)
        self.pack_end(self.delete_button)

    # Initialized every time save button is clicked
    def check_question_dialog(self, question_content: dict):

        check_result = check_question(json.dumps(
            self.page.content, ensure_ascii=False
        ), ignore_duplicates=True)
        if check_result:
            check_result.pop('__question_name__')
            dialog = Gtk.MessageDialog(
                transient_for=self.parent_window,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=f'{self.page.content["name"]} has formatting errors:'
            )
            dialog.format_secondary_text(
                json.dumps(check_result, ensure_ascii=False, indent=4)
            )
            dialog.run()
            dialog.destroy()
            return check_result
        else:
            return None

    def on_save_clicked(self, button) -> None:

        def save_question() -> None:
            dialog = Gtk.MessageDialog(
                transient_for=self.parent_window,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.YES_NO,
                text=f'Are you sure you want to save {self.page.content["name"]}?'
            )
            dialog.format_secondary_text('')
            response = dialog.run()
            if response == Gtk.ResponseType.YES:
                # Check question for correct formatting
                check_result = self.check_question_dialog(self.page.content)
                # Update database if question contains no errors
                if not check_result:
                    QUESTIONS.insert_one(self.page.content)
                    # Update QuestionTable
                    self.table.question_liststore.clear()
                    self.table.build_table(*self.overview.load_data())
            elif response == Gtk.ResponseType.NO:
                pass
            dialog.destroy()

        def overwrite_question() -> None:
            dialog = Gtk.MessageDialog(
                transient_for=self.parent_window,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.YES_NO,
                text=f'Are you sure you want to overwrite {self.page.content["name"]}?'
            )
            dialog.format_secondary_text('Changes are irreversible!')
            response = dialog.run()
            if response == Gtk.ResponseType.YES:
                # Check question for correct formatting
                check_result = self.check_question_dialog(self.page.content)
                # Update database if question contains no errors
                if not check_result:
                    for k, v in self.page.content.items():
                        QUESTIONS.find_one_and_update(
                            {'name': self.page.content['name']},
                            {'$set': {k: v}}
                        )
                    # Update QuestionTable
                    self.table.question_liststore.clear()
                    self.table.build_table(*self.overview.load_data())
            elif response == Gtk.ResponseType.NO:
                pass
            dialog.destroy()

        self.page = self.parent_window.notebook.get_nth_page(
            self.parent_window.notebook.get_current_page()
        )
        new_content = self.page.update_content()
        self.page.overwrite(new_content)
        question_name = self.page.content['name']
        # Check if any changes were made to question
        db_question = QUESTIONS.find_one({'name': question_name})
        try:
            db_question.pop('_id')
            if self.page.content == db_question:
                dialog = Gtk.MessageDialog(
                    transient_for=self.parent_window,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text=f'Nothing to save.'
                )
                dialog.format_secondary_text('No changes were made to ' +
                                             f'{question_name}.')
                dialog.run()
                dialog.destroy()
                return None
        # When db_question == None
        except AttributeError:
            pass
        # Check if question already exists in database
        if not db_question:
            save_question()
        else:
            overwrite_question()

    def on_delete_clicked(self, button) -> None:

        self.page = self.parent_window.notebook.get_nth_page(
            self.parent_window.notebook.get_current_page()
        )
        new_content = self.page.update_content()
        self.page.overwrite(new_content)
        question_name = self.page.content['name']
        db_question = QUESTIONS.find_one({'name': question_name})

        # Check if question is in DB
        if not db_question:
            dialog = Gtk.MessageDialog(
                    transient_for=self.parent_window,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text=f'Nothing to delete.'
                )
            dialog.format_secondary_text(f'{question_name} ' +
                                         "doesn't exist in database!")
            dialog.run()
            dialog.destroy()
            return None
        else:
            dialog = Gtk.MessageDialog(
                transient_for=self.parent_window,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.YES_NO,
                text=f'Are you sure you want to delete {question_name}?'
            )
            dialog.format_secondary_text('Changes are irreversible!')
            response = dialog.run()
            if response == Gtk.ResponseType.YES:
                QUESTIONS.delete_one({'name': question_name})
                # Update QuestionTable
                self.table.question_liststore.clear()
                self.table.build_table(*self.overview.load_data())
                # Close question window
                dialog.destroy()
                self.parent_window.destroy()
            elif response == Gtk.ResponseType.NO:
                dialog.destroy()


class GeneralQuestionGrid(Gtk.Grid):

    def __init__(self, question_content: dict):

        super().__init__()
        self.set_column_spacing(100)
        self.set_row_spacing(20)

        self.content = question_content

        self.name_label = Gtk.Label(label='name')
        self.attach(self.name_label, 0, 0, 1, 1)

        self.name_field = Gtk.Entry()
        self.name_field.set_property('name', 'name')
        self.name_field.set_hexpand(True)
        self.name_field.set_text(self.content['name'])
        self.name_field.set_editable(False)
        self.attach_next_to(self.name_field,
                            self.name_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.moodle_type_label = Gtk.Label(label='moodle_type')
        self.attach_next_to(self.moodle_type_label,
                            self.name_label,
                            Gtk.PositionType.BOTTOM, 1, 1)

        self.moodle_type_field = Gtk.Entry()
        self.moodle_type_field.set_property('name', 'moodle_type')
        self.moodle_type_field.set_hexpand(True)
        self.moodle_type_field.set_text(self.content['moodle_type'])
        self.moodle_type_field.set_editable(False)
        self.attach_next_to(self.moodle_type_field,
                            self.moodle_type_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.question_label = Gtk.Label(label='question')
        self.attach_next_to(self.question_label,
                            self.moodle_type_label,
                            Gtk.PositionType.BOTTOM, 1, 1)

        self.question_field = Gtk.TextView(wrap_mode=Gtk.WrapMode(3))
        self.question_field.set_property('name', 'question')
        self.question_field.set_hexpand(True)
        self.question_buffer = self.question_field.get_buffer()
        self.question_buffer.set_text(self.content['question'])
        self.attach_next_to(self.question_field,
                            self.question_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.points_label = Gtk.Label(label='points')
        self.attach_next_to(self.points_label,
                            self.question_label,
                            Gtk.PositionType.BOTTOM, 1, 1)

        self. points_field = Gtk.Entry()
        self.points_field.set_property('name', 'points')
        self.points_field.set_hexpand(True)
        self.points_field.set_text(str(self.content['points']))
        self.attach_next_to(self.points_field,
                            self.points_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.difficulty_label = Gtk.Label(label='difficulty')
        self.attach_next_to(self.difficulty_label,
                            self.points_label,
                            Gtk.PositionType.BOTTOM, 1, 1)

        self. difficulty_field = Gtk.Entry()
        self.difficulty_field.set_property('name', 'difficulty')
        self.difficulty_field.set_hexpand(True)
        self.difficulty_field.set_text(str(self.content['difficulty']))
        self.attach_next_to(self.difficulty_field,
                            self.difficulty_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.time_est_label = Gtk.Label(label='time_est')
        self.attach_next_to(self.time_est_label,
                            self.difficulty_label,
                            Gtk.PositionType.BOTTOM, 1, 1)

        self. time_est_field = Gtk.Entry()
        self.time_est_field.set_property('name', 'time_est')
        self.time_est_field.set_hexpand(True)
        self.time_est_field.set_text(str(self.content['time_est']))
        self.attach_next_to(self.time_est_field,
                            self.time_est_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.family_type_label = Gtk.Label(label='family_type')
        self.attach_next_to(self.family_type_label,
                            self.time_est_label,
                            Gtk.PositionType.BOTTOM, 1, 1)

        self.family_type_field = Gtk.Entry()
        self.family_type_field.set_property('name', 'family_type')
        self.family_type_field.set_hexpand(True)
        self.family_type_field.set_text(self.content['family_type'])
        self.family_type_field.set_editable(False)
        self.attach_next_to(self.family_type_field,
                            self.family_type_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.in_exams_label = Gtk.Label(label='in_exams')
        self.attach_next_to(self.in_exams_label,
                            self.family_type_label,
                            Gtk.PositionType.BOTTOM, 1, 1)

        self.in_exams_field = SimpleDictGrid(
            self.content['in_exams'], editable=False, add=False,
            output_type=float
        )
        self.in_exams_field.set_property('name', 'in_exams')
        self.attach_next_to(self.in_exams_field,
                            self.in_exams_label,
                            Gtk.PositionType.RIGHT, 2, 1)

    # self.content needs to be updated when page is switched
    def update_content(self) -> dict:

        def get_field_content(field_child):

            match field_child.__class__.__name__:
                case Gtk.TextView.__name__:
                    textbuffer = field_child.get_buffer()
                    text = textbuffer.get_text(
                        textbuffer.get_start_iter(),
                        textbuffer.get_end_iter(),
                        include_hidden_chars=True
                    )
                    return text
                case SimpleListGrid.__name__:
                    return field_child.get_content()
                case SimpleDictGrid.__name__:
                    return field_child.get_content()
                case DictListGrid.__name__:
                    return field_child.get_content()
                case _:
                    raise Exception
        
        # Create label/field pairs from children
        child_pairs = list(zip(
            self.get_children()[1::2], self.get_children()[0::2]
        ))
        # Update self.content dict
        for i in child_pairs:
            # Preserve original data types of entry fields
            if type(i[1]) == Gtk.Entry:
                try:
                    original_type = KEY_TYPES['general'][i[0].get_property('label')]
                except KeyError:
                    original_type = KEY_TYPES[
                        self.moodle_type_field.get_text()
                    ][i[0].get_property('label')]
                self.content[i[0].get_property('label')] = original_type(i[1].get_text())
            else:
                self.content[i[0].get_property('label')] = get_field_content(i[1])

        return self.content

    def overwrite(self, question_content: dict):

        self.content = question_content

        for k, v in question_content.items():

            # Get each child according to passed dictionary
            try:
                child = list(filter(
                    lambda x: (x.get_property('name') == k), self.get_children()
                ))[0]
            except IndexError:
                child = 'Ignore key'

            # Overwrite child according to class
            match child.__class__.__name__:
                case Gtk.Entry.__name__:
                    child.set_text(str(v))
                case Gtk.TextView.__name__:
                    child.get_buffer().set_text(str(v))
                case SimpleListGrid.__name__:
                    child.overwrite(v)
                case SimpleDictGrid.__name__:
                    child.overwrite(v)
                case DictListGrid.__name__:
                    child.overwrite(v)
                case str.__name__:
                    pass
                case _:
                    raise Exception


class MultiChoiceQuestionGrid(GeneralQuestionGrid):

    def __init__(self, question_content: dict):

        super().__init__(question_content)

        self.insert_row(3)
        self.correct_answers_label = Gtk.Label(label='correct_answers')
        self.attach(self.correct_answers_label, 0, 3, 1, 1)
        self.correct_answers_field = SimpleListGrid(
            self.content['correct_answers']
        )
        self.correct_answers_field.set_property('name', 'correct_answers')
        self.attach_next_to(self.correct_answers_field,
                            self.correct_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.insert_row(4)
        self.false_answers_label = Gtk.Label(label='false_answers')
        self.attach(self.false_answers_label, 0, 4, 1, 1)
        self.false_answers_field = SimpleListGrid(
            self.content['false_answers']
        )
        self.false_answers_field.set_property('name', 'false_answers')
        self.attach_next_to(self.false_answers_field,
                            self.false_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.insert_row(5)
        self.single_label = Gtk.Label(label='single')
        self.attach(self.single_label, 0, 5, 1, 1)
        self.single_field = Gtk.Entry()
        self.single_field.set_property('name', 'single')
        self.single_field.set_hexpand(True)
        self.single_field.set_text(str(self.content['single']))
        self.attach_next_to(self.single_field,
                            self.single_label,
                            Gtk.PositionType.RIGHT, 2, 1)


class NumericalQuestionGrid(GeneralQuestionGrid):

    def __init__(self, question_content: dict):

        super().__init__(question_content)

        self.insert_row(3)
        self.correct_answers_label = Gtk.Label(label='correct_answers')
        self.attach(self.correct_answers_label, 0, 3, 1, 1)
        self.correct_answers_field = SimpleListGrid(
            self.content['correct_answers'], add=False, output_type=float
        )
        self.correct_answers_field.set_property('name', 'correct_answers')
        self.attach_next_to(self.correct_answers_field,
                            self.correct_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.insert_row(4)
        self.tolerance_label = Gtk.Label(label='tolerance')
        self.attach(self.tolerance_label, 0, 4, 1, 1)
        self.tolerance_field = Gtk.Entry()
        self.tolerance_field.set_property('name', 'tolerance')
        self.tolerance_field.set_hexpand(True)
        self.tolerance_field.set_text(str(self.content['tolerance']))
        self.attach_next_to(self.tolerance_field,
                            self.tolerance_label,
                            Gtk.PositionType.RIGHT, 2, 1)


class ShortanswerQuestionGrid(GeneralQuestionGrid):

    def __init__(self, question_content: dict):

        super().__init__(question_content)

        self.insert_row(3)
        self.correct_answers_label = Gtk.Label(label='correct_answers')
        self.attach(self.correct_answers_label, 0, 3, 1, 1)
        self.correct_answers_field = SimpleListGrid(
            self.content['correct_answers']
        )
        self.correct_answers_field.set_property('name', 'correct_answers')
        self.attach_next_to(self.correct_answers_field,
                            self.correct_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.insert_row(4)
        self.usecase_label = Gtk.Label(label='usecase')
        self.attach(self.usecase_label, 0, 4, 1, 1)
        self.usecase_field = Gtk.Entry()
        self.usecase_field.set_property('name', 'usecase')
        self.usecase_field.set_hexpand(True)
        self.usecase_field.set_text(str(self.content['usecase']))
        self.attach_next_to(self.usecase_field,
                            self.usecase_label,
                            Gtk.PositionType.RIGHT, 2, 1)


class EssayQuestionGrid(GeneralQuestionGrid):

    def __init__(self, question_content: dict):

        super().__init__(question_content)

        self.insert_row(3)
        self.answer_files_label = Gtk.Label(label='answer_files')
        self.attach(self.answer_files_label, 0, 3, 1, 1)
        self.answer_files_field = SimpleListGrid(
            self.content['answer_files'], add=False, output_type=int
        )
        self.answer_files_field.set_property('name', 'answer_files')
        self.attach_next_to(self.answer_files_field,
                            self.answer_files_label,
                            Gtk.PositionType.RIGHT, 2, 1)


class MatchingQuestionGrid(GeneralQuestionGrid):

    def __init__(self, question_content: dict):

        super().__init__(question_content)

        self.insert_row(3)
        self.correct_answers_label = Gtk.Label(label='correct_answers')
        self.attach(self.correct_answers_label, 0, 3, 1, 1)
        self.correct_answers_field = SimpleDictGrid(
            self.content['correct_answers']
        )
        self.correct_answers_field.set_property('name', 'correct_answers')
        self.attach_next_to(self.correct_answers_field,
                            self.correct_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.insert_row(4)
        self.false_answers_label = Gtk.Label(label='false_answers')
        self.attach(self.false_answers_label, 0, 4, 1, 1)
        self.false_answers_field = SimpleListGrid(
            self.content['false_answers']
        )
        self.false_answers_field.set_property('name', 'false_answers')
        self.attach_next_to(self.false_answers_field,
                            self.false_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)


class GapselectQuestionGrid(GeneralQuestionGrid):

    def __init__(self, question_content: dict):

        super().__init__(question_content)

        self.insert_row(3)
        self.correct_answers_label = Gtk.Label(label='correct_answers')
        self.attach(self.correct_answers_label, 0, 3, 1, 1)
        self.correct_answers_field = DictListGrid(
            self.content['correct_answers']
        )
        self.correct_answers_field.set_property('name', 'correct_answers')
        self.attach_next_to(self.correct_answers_field,
                            self.correct_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.insert_row(4)
        self.false_answers_label = Gtk.Label(label='false_answers')
        self.attach(self.false_answers_label, 0, 4, 1, 1)
        self.false_answers_field = DictListGrid(
            self.content['false_answers']
        )
        self.false_answers_field.set_property('name', 'false_answers')
        self.attach_next_to(self.false_answers_field,
                            self.false_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)


class DDImageOrTextQuestionGrid(GeneralQuestionGrid):

    def __init__(self, question_content: dict):

        super().__init__(question_content)

        self.insert_row(3)
        self.correct_answers_label = Gtk.Label(label='correct_answers')
        self.attach(self.correct_answers_label, 0, 3, 1, 1)
        self.correct_answers_field = SimpleListGrid(
            self.content['correct_answers']
        )
        self.correct_answers_field.set_property('name', 'correct_answers')
        self.attach_next_to(self.correct_answers_field,
                            self.correct_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.insert_row(4)
        self.drops_label = Gtk.Label(label='drops')
        self.attach(self.drops_label, 0, 4, 1, 1)
        self.drops_field = DictListGrid(
            self.content['drops'], list_add=False, new_list_length=2,
            output_type=int
        )
        self.drops_field.set_property('name', 'drops')
        self.attach_next_to(self.drops_field,
                            self.drops_label,
                            Gtk.PositionType.RIGHT, 2, 1)


class CalculatedQuestionGrid(GeneralQuestionGrid):

    def __init__(self, question_content: dict):

        super().__init__(question_content)

        self.insert_row(3)
        self.correct_answers_label = Gtk.Label(label='correct_answers')
        self.attach(self.correct_answers_label, 0, 3, 1, 1)
        self.correct_answers_field = SimpleListGrid(
            self.content['correct_answers'], add=False
        )
        self.correct_answers_field.set_property('name', 'correct_answers')
        self.attach_next_to(self.correct_answers_field,
                            self.correct_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.insert_row(4)
        self.vars_label = Gtk.Label(label='vars')
        self.attach(self.vars_label, 0, 4, 1, 1)
        self.vars_field = SimpleListGrid(
            self.content['vars']
        )
        self.vars_field.set_property('name', 'vars')
        self.attach_next_to(self.vars_field,
                            self.vars_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.insert_row(5)
        self.tolerance_label = Gtk.Label(label='tolerance')
        self.attach(self.tolerance_label, 0, 5, 1, 1)
        self.tolerance_field = SimpleListGrid(
            self.content['tolerance'], add=False, output_type=[float, str, int]
        )
        self.tolerance_field.set_property('name', 'tolerance')
        self.attach_next_to(self.tolerance_field,
                            self.tolerance_label,
                            Gtk.PositionType.RIGHT, 2, 1)


class SimpleListGrid(Gtk.Grid):

    def __init__(self, list_field: list,
                 editable: bool = True,
                 add: bool = True,
                 output_type: tuple[type, list] = str):

        super().__init__()
        self.set_row_spacing(10)

        for n, i in enumerate(list_field):
            entry = Gtk.Entry()
            entry.set_hexpand(True)
            entry.set_text(str(i))
            entry.set_editable(editable)
            self.attach(entry, 0, n, 1, 1)

        self.output_type = output_type
        self.n_rows = len(list_field)

        if add:
            self.add_button = Gtk.Button(label='+')
            self.add_button.connect('clicked', self.add_row)
            self.attach(self.add_button, 0, self.n_rows, 1, 1)

    def add_row(self, button):

        self.n_rows = len(
            [x for x in self.get_children() if type(x) != Gtk.Button]
        )
        entry = Gtk.Entry()
        entry.set_hexpand(True)
        self.insert_row(self.n_rows)
        self.attach(entry, 0, self.n_rows, 1, 1)
        entry.show()

        self.n_rows += 1

    def get_content(self) -> list:

        content = list(reversed([
            x.get_text() for x in self.get_children() if
            type(x) != Gtk.Button
        ]))
        # Remove empty strings from list
        content = [x for x in content if x != '']

        if type(self.output_type) == list: # calculated tolerance field needs different types
            return [x[0](x[1]) for x in zip(self.output_type, content)]
        else:
            return [self.output_type(x) for x in content]

    def overwrite(self, input_list: list) -> None:

        # Delete old entries
        for c in self.get_children():
            if type(c) != Gtk.Button:
                self.remove(c)
        # Add new values as new entries
        for n, x in enumerate(input_list):
            entry = Gtk.Entry()
            entry.set_hexpand(True)
            entry.set_text(str(x))
            self.attach(entry, 0, n, 1, 1)
            entry.show()


class SimpleDictGrid(Gtk.Grid):

    def __init__(self, dict_field: dict,
                 editable: bool = True,
                 add: bool = True,
                 output_type: type = str):

        super().__init__()
        self.set_column_spacing(50)
        self.set_row_spacing(10)

        for n, key in enumerate(dict_field.keys()):
            entry = Gtk.Entry()
            entry.set_hexpand(True)
            entry.set_text(key)
            entry.set_editable(editable)
            self.attach(entry, 0, n, 1, 1)

        for n, value in enumerate(dict_field.values()):
            entry = Gtk.Entry()
            entry.set_hexpand(True)
            entry.set_text(str(value))
            entry.set_editable(editable)
            self.attach(entry, 1, n, 1, 1)

        self.output_type = output_type
        self.n_rows = len(dict_field.keys())

        if add:
            self.add_button = Gtk.Button(label='+')
            self.add_button.connect('clicked', self.add_row)
            self.attach(self.add_button, 0, self.n_rows, 1, 1)

    def add_row(self, button):

        key_entry = Gtk.Entry()
        key_entry.set_hexpand(True)
        self.insert_row(self.n_rows)
        self.attach(key_entry, 0, self.n_rows, 1, 1)
        key_entry.show()

        value_entry = Gtk.Entry()
        value_entry.set_hexpand(True)
        self.attach_next_to(value_entry,
                            key_entry,
                            Gtk.PositionType.RIGHT, 1, 1)
        value_entry.show()

        self.n_rows += 1

    def get_content(self) -> dict:

        if hasattr(self, 'add_button'):
            child_list = self.get_children()[1:]
        else:
            child_list = self.get_children()
        content = dict(zip(
            reversed([x.get_text() for x in child_list][len(child_list)//2:]),
            reversed([x.get_text() for x in child_list][:len(child_list)//2])
        ))

        return {k: self.output_type(v) for k, v in content.items()}

    def overwrite(self, input_dict: dict):

        child_list = self.get_children()[1:]
        key_pairs = zip(
            input_dict.keys(),
            reversed(child_list[len(child_list)//2:])
        )
        value_pairs = zip(
            input_dict.values(),
            reversed(child_list[:len(child_list)//2])
        )

        for i, j in key_pairs:
            j.set_text(str(i))

        for i, j in value_pairs:
            j.set_text(str(i))


class DictListGrid(Gtk.Grid):

    def __init__(self, dict_field: dict,
                 dict_editable: bool = True, dict_add: bool = True,
                 list_editable: bool = True, list_add: bool = True,
                 new_list_length: int = 1, output_type: tuple[type, list] = str):

        super().__init__()
        self.set_column_spacing(50)
        self.set_row_spacing(10)

        for n, key in enumerate(dict_field.keys()):
            entry = Gtk.Entry()
            entry.set_hexpand(True)
            entry.set_text(key)
            entry.set_editable(dict_editable)
            self.attach(entry, 0, n, 1, 1)
            self.attach_next_to(SimpleListGrid(dict_field[key], list_editable, list_add),
                                entry,
                                Gtk.PositionType.RIGHT, 1, 1)
        
        self.output_type = output_type
        self.n_rows = len(dict_field.keys())
        self.new_list_length = new_list_length
        self.list_editable = list_editable
        self.list_add = list_add

        if dict_add:
            self.add_button = Gtk.Button(label='+')
            self.add_button.connect('clicked', self.add_row)
            self.attach(self.add_button, 0, self.n_rows, 1, 1)

    def add_row(self, button):

        key_entry = Gtk.Entry()
        key_entry.set_hexpand(True)
        self.insert_row(self.n_rows)
        self.attach(key_entry, 0, self.n_rows, 1, 1)
        key_entry.show()

        list_entry = SimpleListGrid(self.new_list_length * [''],
                                    self.list_editable, self.list_add)
        self.attach_next_to(list_entry,
                            key_entry,
                            Gtk.PositionType.RIGHT, 1, 1)
        list_entry.show_all()

        self.n_rows += 1

    def get_content(self) -> dict:

        if hasattr(self, 'add_button'):
            child_list = self.get_children()[1:]
        else:
            child_list = self.get_children()
        content = dict(zip(
            reversed([x.get_text() for x in child_list][len(child_list)//2:]),
            reversed([x.get_content(self.output_type) if isinstance(x, SimpleListGrid)
                      else x.get_text() for x in child_list][:len(child_list)//2])
        ))

        return content

    def overwrite(self, input_dict: dict):

        child_list = self.get_children()[1:]
        key_pairs = zip(
            input_dict.keys(),
            reversed(child_list[len(child_list)//2:])
        )
        value_pairs = zip(
            input_dict.values(),
            reversed(child_list[:len(child_list)//2])
        )

        for i, j in key_pairs:
            j.set_text(str(i))

        for i, j in value_pairs:
            if type(j) == Gtk.Entry:
                j.set_text(str(i))
            elif type(j) == SimpleListGrid:
                j.overwrite(i)


class RawQuestionText(Gtk.TextView):

    def __init__(self, question_content: dict):

        super().__init__(wrap_mode=Gtk.WrapMode(3))

        self.content = question_content

        self.textbuffer = self.get_buffer()
        self.textbuffer.set_text(json.dumps(self.content,
                                 ensure_ascii=False, indent=4))

    def update_content(self) -> dict:

        self.content = json.loads(
            self.textbuffer.get_text(
            self.textbuffer.get_start_iter(),
            self.textbuffer.get_end_iter(),
            include_hidden_chars=True
            )
        )

        return self.content

    def overwrite(self, question_content: dict):

        self.content = question_content

        self.textbuffer.set_text(
            json.dumps(question_content, ensure_ascii=False, indent=4)
        )


class ExamWindow(Gtk.Window):

    def __init__(self, parent, exam_name: str):
        super().__init__(title=exam_name)
        self.set_size_request(700, 600)
        self.parent_window = parent
        self.connect('destroy', self.remove_parent_attribute)

        self.panes = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.panes.set_position(350)
        self.add(self.panes)

        # Left pane
        self.left_grid = Gtk.Grid()
        self.left_grid.set_column_homogeneous(True)
        self.panes.add1(self.left_grid)

        self.scroll_window = Gtk.ScrolledWindow()
        self.scroll_window.set_vexpand(True)

        self.text_view = Gtk.TextView(wrap_mode=Gtk.WrapMode(3))
        self.text_view.set_hexpand(True)
        self.textbuffer = self.text_view.get_buffer()
        self.scroll_window.add(self.text_view)

        self.control = ExamControlPanel(self)

        self.left_grid.attach(self.scroll_window, 0, 0, 1, 1)
        self.left_grid.attach_next_to(self.control, self.scroll_window,
                                 Gtk.PositionType.BOTTOM, 1, 1)

        # Right pane
        self.right_grid = Gtk.Grid()
        self.right_grid.set_column_spacing(50)
        self.right_grid.set_row_spacing(10)
        self.panes.add2(self.right_grid)

        self.time_label = Gtk.Label(label='Estimated exam time: ')
        self.right_grid.attach(self.time_label, 0, 0, 2, 1)
        self.time_value = Gtk.Label()
        self.time_value.set_property('name', 'time')
        self.right_grid.attach_next_to(self.time_value, self.time_label,
                                       Gtk.PositionType.RIGHT, 1, 1)

        self.difficulty_label = Gtk.Label(label='Average estimated difficulty: ')
        self.right_grid.attach_next_to(self.difficulty_label, self.time_label,
                                       Gtk.PositionType.BOTTOM, 2, 1)
        self.difficulty_value = Gtk.Label()
        self.difficulty_value.set_property('name', 'difficulty')
        self.right_grid.attach_next_to(self.difficulty_value, self.difficulty_label,
                                       Gtk.PositionType.RIGHT, 1, 1)

        self.points_label = Gtk.Label(label='Maximum achievable points: ')
        self.right_grid.attach_next_to(self.points_label, self.difficulty_label,
                                       Gtk.PositionType.BOTTOM, 2, 1)
        self.points_value = Gtk.Label()
        self.points_value.set_property('name', 'points')
        self.right_grid.attach_next_to(self.points_value, self.points_label,
                                       Gtk.PositionType.RIGHT, 1, 1)
    
    def add_question(self, question_name: str) -> None:
        previous_text = self.textbuffer.get_text(
            self.textbuffer.get_start_iter(),
            self.textbuffer.get_end_iter(),
            include_hidden_chars=True
        )
        # First question doesn't need newline
        if previous_text == '':
            self.textbuffer.set_text(f'{question_name}')
        else:
            self.textbuffer.set_text(previous_text + f'\n{question_name}')

        self.update_report(None)

    def update_report(self, button) -> None:

        question_list = self.textbuffer.get_text(
            self.textbuffer.get_start_iter(),
            self.textbuffer.get_end_iter(),
            include_hidden_chars=True
        ).split()
        # Calculate estimated time
        time_value = list(filter(
            lambda x: (x.get_property('name') == 'time'),
            self.right_grid.get_children()
        ))[0]
        time_est = sum([QUESTIONS.find_one({'name': q})['time_est']
                        for q in question_list])
        time_value.set_label(str(time_est))
        # Calculate average difficulty
        difficulty_value = list(filter(
            lambda x: (x.get_property('name') == 'difficulty'),
            self.right_grid.get_children()
        ))[0]
        difficulty_avg = np.round(np.mean(
            [QUESTIONS.find_one({'name': q})['difficulty'] for q in question_list]
        ), 2)
        difficulty_value.set_label(str(difficulty_avg))
        # Calculate max points
        points_value = list(filter(
            lambda x: (x.get_property('name') == 'points'),
            self.right_grid.get_children()
        ))[0]
        max_points = sum(
            [QUESTIONS.find_one({'name': q})['points'] for q in question_list]
        )
        points_value.set_label(str(max_points))

    def create_exam(self, button) -> None:
        return 0

    def remove_parent_attribute(self, window):
        delattr(self.parent_window, 'exam_window')


class ExamControlPanel(Gtk.ActionBar):

    def __init__(self, parent):

        super().__init__()
        self.parent_window = parent

        self.create_button = Gtk.Button(label='Create exam')
        self.create_button.connect('clicked', self.parent_window.create_exam)
        self.pack_start(self.create_button)

        self.update_report_button = Gtk.Button(label='Update report')
        self.update_report_button.connect('clicked', self.parent_window.update_report)
        self.pack_end(self.update_report_button)


# Function to initialize overview
def gtk_overview() -> None:

    def run_overview() -> None:
        win = Overview()
        win.show_all()
        Gtk.main()

    thread = threading.Thread(target=run_overview)
    thread.daemon = True
    thread.start()
