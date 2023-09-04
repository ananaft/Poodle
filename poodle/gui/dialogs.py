# Gtk Modules
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
# Poodle modules
from poodle import exam
from poodle import config


class OKDialog(Gtk.MessageDialog):
    """
    Multi-purpose dialog.

    Dependencies: Gtk
    """

    def __init__(self, parent: Gtk.Window, text: str):

        super().__init__(
            transient_for=parent,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=text
        )

    def _run(self):
        self.run()
        self.destroy()


class QuestionSelectionDialog(Gtk.MessageDialog):
    """
    Called by ExamWindow().create_exam()

    Dependencies: Gtk, exam
    """

    def __init__(self, parent: Gtk.Window, exam_window: Gtk.Window):

        self.parent_window = parent
        self.exam_window = exam_window
        super().__init__(
            transient_for=self.parent_window,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.YES_NO,
            text=(
                'Are you sure you want to create ' +
                f'{self.exam_window.get_property("title")} with the current ' +
                'question selection?'
            )
        )

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
    Called by QuestionTreeview().new_question()

    Dependencies: Gtk, config
    """

    def __init__(self, parent):

        super().__init__(
            transient_for=parent,
            message_type=Gtk.MessageType.OTHER,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text='Please pick a Moodle type for the new question:'
        )

    def _run(self):
        # Set up ComboBox
        self.box = self.get_message_area()
        self.moodle_types = Gtk.ComboBoxText()
        for mt in config.KEY_TYPES.keys():
            if mt != 'general' and mt != 'optional':
                self.moodle_types.append_text(mt)
        self.moodle_types.set_active(0)
        self.box.pack_end(self.moodle_types, True, True, 10)
        self.box.show_all()
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
