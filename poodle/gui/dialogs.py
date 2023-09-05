# Gtk Modules
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
# Poodle modules
from poodle import exam
from poodle import config
import gui.windows
import gui.grids
# Other modules
import json


class OKDialog(Gtk.MessageDialog):
    """
    Multi-purpose dialog.

    Dependencies: Gtk
    """

    def __init__(self, parent: Gtk.Window, text: str, secondary_text: str = ''):

        super().__init__(
            transient_for=parent,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=text
        )
        if secondary_text:
            self.format_secondary_text(secondary_text)

    def _run(self):
        self.run()
        self.destroy()


class YesNoDialog(Gtk.MessageDialog):
    """
    Multi-purpose dialog.

    Dependencies: Gtk
    """

    def __init__(self, parent: Gtk.Window, text: str, secondary_text: str = ''):

        super().__init__(
            transient_for=parent,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.YES_NO,
            text=text
        )
        if secondary_text:
            self.format_secondary_text(secondary_text)

    def _run(self):
        response = self.run()
        if response == Gtk.ResponseType.YES:
            self.destroy()
            return True
        elif response == Gtk.ResponseType.NO:
            self.destroy()
            return False
        


class QuestionSelectionDialog(Gtk.MessageDialog):
    """
    Called by: ExamWindow.create_exam()

    Dependencies: Gtk, exam
    """

    def __init__(self, parent: Gtk.Window, exam_window: Gtk.Window):

        super().__init__(
            transient_for=parent,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.YES_NO,
            text=(
                'Are you sure you want to create ' +
                f'{self.exam_window.get_property("title")} with the current ' +
                'question selection?'
            )
        )
        self.parent_window = parent
        self.exam_window = exam_window

    def _run(self, questions: list):
        # React to button presses
        response = self.run()
        if response == Gtk.ResponseType.YES:
            exam.create_exam(
                self.exam_window.get_property('title'), mode='gui', questions=questions
            )
            self.parent_window.update_tables()
            self.destroy()
            self.exam_window.destroy()
        elif response == Gtk.ResponseType.NO:
            self.destroy()


class NewQuestionDialog(Gtk.MessageDialog):
    """
    Called by: QuestionTreeview.new_question()

    Dependencies: Gtk, config
    """

    def __init__(self, parent):

        super().__init__(
            transient_for=parent,
            message_type=Gtk.MessageType.OTHER,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text='Please pick a Moodle type for the new question:'
        )
        # Set up ComboBox
        self.box = self.get_message_area()
        self.moodle_types = Gtk.ComboBoxText()
        for mt in config.KEY_TYPES.keys():
            if mt != 'general' and mt != 'optional':
                self.moodle_types.append_text(mt)
        self.moodle_types.set_active(0)
        self.box.pack_end(self.moodle_types, True, True, 10)
        self.box.show_all()

    def _run(self):
        # React to button presses
        response = self.run()
        if response == Gtk.ResponseType.OK:
            # Generate question_content
            question_content = {
                k: self.default_fill('general', k, v)
                for k, v in config.KEY_TYPES['general'].items()
            }
            question_content['name'] = 'New question'
            # Set remaining fields based on moodle_type
            question_content['moodle_type'] = self.moodle_types.get_active_text()
            question_content.update({
                k: self.default_fill(question_content['moodle_type'], k, v) for k, v in
                config.KEY_TYPES[question_content['moodle_type']].items()
            })
            self.destroy()
            return question_content
        elif response == Gtk.ResponseType.CANCEL:
            self.destroy()
            return None

    # Fill question_content with default values for data types
    def default_fill(self, moodle_type: str, field_name: str, output_type: type):
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


class NewExamDialog(Gtk.MessageDialog):
    """
    Called by: QuestionTreeview.add_to_exam()

    Dependencies: Gtk, gui.windows
    """

    def __init__(self, parent: Gtk.Window):

        super().__init__(
            transient_for=parent,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text='Please enter exam name:'
        )
        self.parent_window = parent
        # Exam name entry
        self.box = self.get_message_area()
        self.name_entry = Gtk.Entry()
        self.box.pack_end(self.name_entry, True, True, 10)
        self.box.show_all()

    def _run(self):
        # Placeholder attribute so that ExamWindow __init__ throws no error
        self.parent_window.exam_window = None
        # Create exam or cancel
        response = self.run()
        if response == Gtk.ResponseType.OK:
            self.exam_name = self.name_entry.get_text()
            self.parent_window.exam_window = gui.windows.ExamWindow(
                self.parent_window, self.exam_name
            )
            self.parent_window.exam_window.show_all()
            self.destroy()
            return True
        elif response == Gtk.ResponseType.CANCEL:
            try:
                delattr(self.parent_window, 'exam_window')
            except AttributeError:
                pass
            self.destroy()
            return False


class EditColumnsDialog(Gtk.MessageDialog):
    """
    Called by: TableTreeView.edit_columns()

    Dependencies: Gtk, gui.grids
    """

    def __init__(self, parent: Gtk.Window, table: Gtk.TreeView):

        super().__init__(
            transient_for=parent,
            message_type=Gtk.MessageType.OTHER,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text='Edit columns below:'
        )
        self.parent_window = parent
        self.table = table
        # Grid of column titles
        self.box = self.get_message_area()
        self.column_titles = [x.get_title() for x in self.table.get_columns()]
        self.column_grid = gui.grids.TableColumnGrid(
            self.parent_window, self.column_titles
        )
        self.box.pack_end(self.column_grid, True, True, 10)
        self.box.show_all()

    def _run(self):

        response = self.run()
        if response == Gtk.ResponseType.OK:
            # Create new table
            self.new_table = []
            # Columns
            self.new_table.append(
                list(reversed(
                    [x.get_text() for x in self.column_grid.get_children()
                     if type(x) == Gtk.Entry]
                ))
            )
            # Rows
            self.table.liststore.foreach(self.table.insert_rows, self.new_table)
            # Fill in potentially missing values due to added columns
            max_cols = max([len(x) for x in self.new_table])
            self.new_table = [x + [''] * (max_cols - len(x)) for x in self.new_table]
            # Remove old table from parent window and rebuild
            self.parent_window.scroll_window.remove(self.table)
            for c in self.table.get_columns():
                self.table.remove_column(c)
            self.table.build_table(self.new_table)
            self.parent_window.scroll_window.add(self.table)
        elif response == Gtk.ResponseType.CANCEL:
            pass
        self.destroy()


class CheckQuestionDialog(Gtk.MessageDialog):
    """
    Called by: QuestionControlPanel.check_question_dialog()

    Dependencies: Gtk, json
    """

    def __init__(self, parent: Gtk.Window, page, check_result):

        super().__init__(
            transient_for=parent,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=f'{page.content["name"]} has formatting errors:'
        )
        self.format_secondary_text(
            json.dumps(check_result, ensure_ascii=False, indent=4)
        )
        self.check_result = check_result

    def _run(self):
        self.run()
        self.destroy()
        return self.check_result
