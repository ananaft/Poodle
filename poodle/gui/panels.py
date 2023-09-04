# Gtk Modules
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
# Poodle Modules
from poodle import question
from poodle import config
# Other modules
import json
import ast
import re


class MainQuestionControlPanel(Gtk.ActionBar):
    """
    Dependencies: Gtk
    """

    def __init__(self, parent):

        super().__init__()
        self.parent_window = parent
        self.table = self.parent_window.notebook.question_table

        self.new_button = Gtk.Button(label='New')
        self.new_button.connect('clicked', self.table.on_button_press)
        self.pack_start(self.new_button)

        self.view_button = Gtk.Button(label='View')
        self.view_button.connect('clicked', self.table.on_button_press)
        self.pack_start(self.view_button)

        self.delete_button = Gtk.Button(label='Delete')
        self.delete_button.connect('clicked', self.table.on_button_press)
        self.pack_start(self.delete_button)

        self.add_to_exam_button = Gtk.Button(label='Add to exam')
        self.add_to_exam_button.connect('clicked', self.table.on_button_press)
        self.pack_start(self.add_to_exam_button)

        # Filter functionality
        self.filter_button = Gtk.Button(label='Filter')
        self.filter_button.connect('clicked', self.table.on_button_press)
        self.pack_end(self.filter_button)

        question_fields = [
            'name',
            'question',
            'moodle_type',
            'family_type',
            'appearances',
            'difficulty',
            'time_est'
        ]
        self.fields_combo = Gtk.ComboBoxText()
        for f in question_fields:
            self.fields_combo.append_text(f)
        self.fields_combo.set_active(0)
        self.pack_end(self.fields_combo)
            
        self.search_entry = Gtk.Entry()
        self.pack_end(self.search_entry)


class MainExamControlPanel(Gtk.ActionBar):
    """
    Dependencies: Gtk
    """

    def __init__(self, parent):

        super().__init__()
        self.parent_window = parent
        self.table = self.parent_window.notebook.exam_table

        self.new_button = Gtk.Button(label='New')
        self.new_button.connect('clicked', self.table.on_button_press)
        self.pack_start(self.new_button)

        self.view_button = Gtk.Button(label='View')
        self.view_button.connect('clicked', self.table.on_button_press)
        self.pack_start(self.view_button)

        self.delete_button = Gtk.Button(label='Delete')
        self.delete_button.connect('clicked', self.table.on_button_press)
        self.pack_start(self.delete_button)

        self.eval_button = Gtk.Button(label='Evaluate')
        self.eval_button.connect('clicked', self.table.on_button_press)
        self.pack_start(self.eval_button)

        # Filter functionality
        self.filter_button = Gtk.Button(label='Filter')
        self.filter_button.connect('clicked', self.table.on_button_press)
        self.pack_end(self.filter_button)

        exam_fields = [
            'name',
            'points_max',
            'points_avg',
            'questions',
            'difficulty',
            'time_est'
        ]
        self.fields_combo = Gtk.ComboBoxText()
        for f in exam_fields:
            self.fields_combo.append_text(f)
        self.fields_combo.set_active(0)
        self.pack_end(self.fields_combo)

        self.search_entry = Gtk.Entry()
        self.pack_end(self.search_entry)


class QuestionControlPanel(Gtk.ActionBar):
    """
    Dependencies: Gtk, json, question, config
    """

    def __init__(self, parent):

        super().__init__()
        self.parent_window = parent
        self.overview = self.parent_window.parent_window
        self.table = self.overview.notebook.question_table

        self.save_button = Gtk.Button(label='Save')
        self.save_button.connect('clicked', self.on_save_clicked)
        self.pack_start(self.save_button)

        self.delete_button = Gtk.Button(label='Delete')
        self.delete_button.connect('clicked', self.on_delete_clicked)
        self.pack_end(self.delete_button)

    # Initialized every time save button is clicked
    def check_question_dialog(self, question_content: dict):

        check_result = question.check_question(json.dumps(
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
                    config.QUESTIONS.insert_one(self.page.content)
                    # Update QuestionTreeview
                    self.table.question_liststore.clear()
                    for c in self.table.get_columns():
                        self.table.remove_column(c)
                    self.table.build_table(*self.table.load_data())
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
                        config.QUESTIONS.find_one_and_update(
                            {'name': self.page.content['name']},
                            {'$set': {k: v}}
                        )
                    # Update QuestionTreeview
                    self.table.question_liststore.clear()
                    for c in self.table.get_columns():
                        self.table.remove_column(c)
                    self.table.build_table(*self.table.load_data())
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
        db_question = config.QUESTIONS.find_one({'name': question_name})
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
        db_question = config.QUESTIONS.find_one({'name': question_name})

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
                config.QUESTIONS.delete_one({'name': question_name})
                # Update QuestionTreeview
                self.table.question_liststore.clear()
                for c in self.table.get_columns():
                    self.table.remove_column(c)
                self.table.build_table(*self.table.load_data())
                # Close question window
                dialog.destroy()
                self.parent_window.destroy()
            elif response == Gtk.ResponseType.NO:
                dialog.destroy()


class TableControlPanel(Gtk.ActionBar):
    """
    Dependencies: Gtk
    """

    def __init__(self, parent):

        super().__init__()
        self.parent_window = parent
        self.table = self.parent_window.table

        self.save_button = Gtk.Button(label='Save')
        self.save_button.connect('clicked', self.table.save_table)
        self.pack_start(self.save_button)

        self.remove_row_button = Gtk.Button(label='Remove row')
        self.remove_row_button.connect('clicked', self.table.remove_row)
        self.pack_end(self.remove_row_button)

        self.add_row_button = Gtk.Button(label='Add row')
        self.add_row_button.connect('clicked', self.table.add_row)
        self.pack_end(self.add_row_button)

        self.edit_columns_button = Gtk.Button(label='Edit columns')
        self.edit_columns_button.connect('clicked', self.table.edit_columns)
        self.pack_end(self.edit_columns_button)


class VariableControlPanel(Gtk.ActionBar):
    """
    Dependencies: Gtk, config, ast, re
    """

    def __init__(self, parent):

        super().__init__()
        self.parent_window = parent
        self.textview = self.parent_window.textview
        self.path = (
            f'{config.BASE_PATH}/databases/{config.DB.name}/random_vars/' +
            f'rv_{self.parent_window.question_name}.py'
        )

        self.save_button = Gtk.Button(label='Save')
        self.save_button.connect('clicked', self.save_file)
        self.pack_start(self.save_button)

        self.check_button = Gtk.Button(label='Check code')
        self.check_button.connect('clicked', self.parse_file, False)
        self.pack_end(self.check_button)

    def load_file(self):

        try:
            with open(self.path, 'r') as rf:
                text = rf.read()
                self.textview.textbuffer.set_text(text)
        except FileNotFoundError:
            # Get vars from question
            variables = self.parent_window.variables
            # Create template
            template = (
                'from config import RANDOM_ARR_SIZE\n' +
                'import numpy as np\n\n' +
                ' = \n'.join(variables) + ' = '
            )
            self.textview.textbuffer.set_text(template)

    def save_file(self, button):

        # Check syntax before saving
        code = self.textview.textbuffer.get_text(
            self.textview.textbuffer.get_start_iter(),
            self.textview.textbuffer.get_end_iter(),
            include_hidden_chars=True
        )
        passed = self.parse_file(button)
        # Write to file if code passed syntax check
        if passed:
            with open(self.path, 'w') as wf:
                wf.write(code)
            dialog = Gtk.MessageDialog(
                transient_for=self.parent_window,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text='File successfully saved.'
            )
            dialog.run()
            dialog.destroy()

    def parse_file(self, button, silent: bool = True) -> bool:

        # Passing this check does not guarantee working code!
        code = self.textview.textbuffer.get_text(
            self.textview.textbuffer.get_start_iter(),
            self.textview.textbuffer.get_end_iter(),
            include_hidden_chars=True
        )
        # Run check
        try:
            ast.parse(code)
        except SyntaxError as e:
            line_number = re.search(r'\d+(?=\))', str(e)).group(0)
            dialog = Gtk.MessageDialog(
                transient_for=self.parent_window,
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text=f'Syntax error found at line {line_number}!'
            )
            dialog.run()
            dialog.destroy()

            return False

        # Display success message
        if not silent:
            dialog = Gtk.MessageDialog(
                transient_for=self.parent_window,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text='Syntax check successfully passed.'
            )
            dialog.format_secondary_text(
                '(This does not guarantee succesful compilation!)'
            )
            dialog.run()
            dialog.destroy()

        return True


class ExamControlPanel(Gtk.ActionBar):
    """
    Dependencies: Gtk
    """

    def __init__(self, parent):

        super().__init__()
        self.parent_window = parent

        self.create_button = Gtk.Button(label='Create exam')
        self.create_button.connect('clicked', self.parent_window.create_exam)
        self.pack_start(self.create_button)

        self.update_report_button = Gtk.Button(label='Update report')
        self.update_report_button.connect('clicked', self.parent_window.update_report)
        self.pack_end(self.update_report_button)
