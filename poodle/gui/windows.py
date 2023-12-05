# Gtk modules
import gi
gi.require_version('Gtk', '3.0')
try:
    gi.require_version('WebKit2', '4.1')
except ValueError:
    gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, WebKit2
# Poodle modules
from poodle import config
from poodle import exam
import gui.treeviews
import gui.panels
import gui.dialogs
import gui.notebooks
# Other modules
import numpy as np
import pandas as pd


class MainWindow(Gtk.Window):
    """
    Dependencies: Gtk, gui.treeviews, gui.panels
    """

    def __init__(self):

        super().__init__(title='Overview')
        self.set_size_request(1350, 900)
        self.connect('destroy', Gtk.main_quit)

        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.add(self.grid)

        self.notebook = gui.notebooks.MainNotebook(self)
        self.control = gui.panels.MainQuestionControlPanel(self)

        self.grid.attach(self.notebook, 0, 0, 1, 1)
        self.grid.attach_next_to(self.control, self.notebook,
                                 Gtk.PositionType.BOTTOM, 1, 1)

    def update_tables(self) -> None:

        questions = self.notebook.question_table
        exams = self.notebook.exam_table

        # Update questions
        questions.question_liststore.clear()
        for c in questions.get_columns():
            questions.remove_column(c)
        questions.build_table(*questions.load_data())
        # Update exams
        exams.exam_liststore.clear()
        for c in exams.get_columns():
            exams.remove_column(c)
        exams.build_table(*exams.load_data())


class QuestionWindow(Gtk.Window):
    """
    Dependencies: Gtk, gui.notebooks, gui.panels
    """

    def __init__(self, parent: Gtk.Window, question_content: dict):

        super().__init__(title=question_content['name'])
        self.set_size_request(1200, 800)
        self.parent_window = parent

        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.add(self.grid)

        self.scroll_window = Gtk.ScrolledWindow()
        self.scroll_window.set_vexpand(True)
        self.notebook = gui.notebooks.QuestionNotebook(self, question_content)
        self.scroll_window.add(self.notebook)

        self.control = gui.panels.QuestionControlPanel(self)

        self.grid.attach(self.scroll_window, 0, 0, 1, 1)
        self.grid.attach_next_to(self.control, self.scroll_window,
                                 Gtk.PositionType.BOTTOM, 1, 1)


class TableWindow(Gtk.Window):
    """
    Dependencies: Gtk, gui.treeviews, gui.panels
    """

    def __init__(self, parent: Gtk.Window, table_name: str, table: list):

        super().__init__(title=table_name)
        self.set_size_request(800, 600)
        self.parent_window = parent
        self.table_key = table_name

        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.add(self.grid)

        self.scroll_window = Gtk.ScrolledWindow()
        self.scroll_window.set_vexpand(True)
        self.table = gui.treeviews.TableTreeView(self, table)
        self.scroll_window.add(self.table)

        self.control = gui.panels.TableControlPanel(self)

        self.grid.attach(self.scroll_window, 0, 0, 1, 1)
        self.grid.attach_next_to(self.control, self.scroll_window,
                                 Gtk.PositionType.BOTTOM, 1, 1)


class VariableFileWindow(Gtk.Window):
    """
    Dependencies: Gtk, gui.panels
    """

    def __init__(self, parent: Gtk.Window, question_name: str, variables: list):

        super().__init__(title=question_name)
        self.set_size_request(800, 600)
        self.parent_window = parent
        self.question_name = question_name
        self.variables = variables

        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.add(self.grid)

        self.scroll_window = Gtk.ScrolledWindow()
        self.scroll_window.set_vexpand(True)
        self.textview = Gtk.TextView(wrap_mode=Gtk.WrapMode(3))
        self.textview.textbuffer = self.textview.get_buffer()
        self.scroll_window.add(self.textview)

        self.control = gui.panels.VariableControlPanel(self)
        self.control.load_file()

        self.grid.attach(self.scroll_window, 0, 0, 1, 1)
        self.grid.attach_next_to(self.control, self.scroll_window,
                                 Gtk.PositionType.BOTTOM, 1, 1)


class ExamWindow(Gtk.Window):
    """
    Dependencies: Gtk, gui.notebooks, gui.panels
    """

    def __init__(self, parent: Gtk.Window, exam_content: dict):

        super().__init__(title=exam_content['name'])
        self.set_size_request(1200, 800)
        self.parent_window = parent

        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.add(self.grid)

        self.scroll_window = Gtk.ScrolledWindow()
        self.scroll_window.set_vexpand(True)
        self.notebook = gui.notebooks.ExamNotebook(self, exam_content)
        self.scroll_window.add(self.notebook)

        self.control = gui.panels.ExamControlPanel(self)

        self.grid.attach(self.scroll_window, 0, 0, 1, 1)
        self.grid.attach_next_to(self.control, self.scroll_window,
                                 Gtk.PositionType.BOTTOM, 1, 1)


class ExamCreationWindow(Gtk.Window):
    """
    Dependencies: Gtk, gui.panels, gui.dialogs, config, exam
    """

    def __init__(self, parent: Gtk.Window, exam_name: str):

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

        self.control = gui.panels.ExamCreationControlPanel(self)

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
        # Check if all questions are in database
        wrong_questions = [
            q for q in question_list if
            config.QUESTIONS.find_one({'name': q}) == None
        ]
        if wrong_questions:
            # Color wrong questions red
            for q in wrong_questions:
                search_match = self.textbuffer.get_start_iter().forward_search(
                    q, 0, None
                )
                self.textbuffer.delete(search_match[0], search_match[1])
                self.textbuffer.insert_markup(
                    search_match[0],
                    f'<span color="red">{q}</span>',
                    -1
                )
            # Message user
            dialog = gui.dialogs.OKDialog(
                self.parent_window,
                'Marked questions could not be found in database!'
            )
            dialog._run()

            return 1
        # Calculate estimated time
        time_value = list(filter(
            lambda x: (x.get_property('name') == 'time'),
            self.right_grid.get_children()
        ))[0]
        time_est = sum([config.QUESTIONS.find_one({'name': q})['time_est']
                        for q in question_list])
        time_value.set_label(str(time_est))
        # Calculate average difficulty
        difficulty_value = list(filter(
            lambda x: (x.get_property('name') == 'difficulty'),
            self.right_grid.get_children()
        ))[0]
        difficulty_avg = np.round(np.mean(
            [config.QUESTIONS.find_one({'name': q})['difficulty'] for q in question_list]
        ), 2)
        difficulty_value.set_label(str(difficulty_avg))
        # Calculate max points
        points_value = list(filter(
            lambda x: (x.get_property('name') == 'points'),
            self.right_grid.get_children()
        ))[0]
        max_points = sum(
            [config.QUESTIONS.find_one({'name': q})['points'] for q in question_list]
        )
        points_value.set_label(str(max_points))

    def create_exam(self, button) -> None:

        if self.update_report(None) == 1:
            return None

        question_list = self.textbuffer.get_text(
            self.textbuffer.get_start_iter(),
            self.textbuffer.get_end_iter(),
            include_hidden_chars=True
        ).split()
        # Ask if selected questions are correct
        dialog = gui.dialogs.QuestionSelectionDialog(
            self.parent_window, self
        )
        dialog._run(question_list)

    def remove_parent_attribute(self, window):
        delattr(self.parent_window, 'exam_window')


class ExamEvaluationWindow(Gtk.Window):
    """
    Dependencies: Gtk, gui.dialogs, exam.evaluate_exam
    """

    def __init__(self, parent: Gtk.Window, exam_name: str):

        super().__init__()
        self.set_size_request(555, 170)
        self.parent_window = parent
        self.exam_name = exam_name
        # Top level grid
        self.top_grid = Gtk.Grid()
        self.top_grid.set_row_spacing(10)
        self.add(self.top_grid)
        # Lower level grid
        self.grid = Gtk.Grid()
        self.grid.set_column_spacing(10)
        self.grid.set_row_spacing(10)
        self.grid.set_column_homogeneous(False)

        self.name_label = Gtk.Label(label='Exam name')
        self.grid.attach(self.name_label, 0, 0, 1, 1)

        self.name_field = Gtk.Entry()
        self.name_field.set_text(exam_name)
        self.name_field.set_editable(False)
        self.grid.attach_next_to(self.name_field,
                            self.name_label,
                            Gtk.PositionType.RIGHT, 1, 1)

        self.stats_label = Gtk.Label(label='Statistics')
        self.grid.attach(self.stats_label, 0, 1, 1, 1)
        
        self.stats_field = Gtk.Entry()
        self.grid.attach_next_to(self.stats_field,
                                 self.stats_label,
                                 Gtk.PositionType.RIGHT, 20, 1)

        self.stats_button = Gtk.Button(label='Choose file')
        self.stats_button.connect('clicked', self.on_choose_clicked,
                                  self.stats_field)
        self.grid.attach_next_to(self.stats_button,
                                 self.stats_field,
                                 Gtk.PositionType.RIGHT, 1, 1)

        self.grades_label = Gtk.Label(label='Grades')
        self.grid.attach(self.grades_label, 0, 2, 1, 1)
        
        self.grades_field = Gtk.Entry()
        self.grid.attach_next_to(self.grades_field,
                                 self.grades_label,
                                 Gtk.PositionType.RIGHT, 20, 1)

        self.grades_button = Gtk.Button(label='Choose file')
        self.grades_button.connect('clicked', self.on_choose_clicked,
                                  self.grades_field)
        self.grid.attach_next_to(self.grades_button,
                                 self.grades_field,
                                 Gtk.PositionType.RIGHT, 1, 1)

        self.control = gui.panels.ExamEvaluationControlPanel(self)

        # Arrange top level grid
        self.top_grid.attach(self.grid, 0, 0, 1, 1)
        self.top_grid.attach(self.control, 0, 1, 1, 1)

    def on_choose_clicked(self, button, entry: Gtk.Entry) -> None:

        dialog = gui.dialogs.EvaluationFilesDialog(self)
        selected_file = dialog._run()
        entry.set_text(selected_file)

    def evaluate(self, button) -> None:

        stats_file = self.stats_field.get_text()
        grades_file = self.grades_field.get_text()

        exam.evaluate_exam(self.exam_name, stats_file, grades_file)
        self.destroy()


class HTMLPreviewWindow(Gtk.Window):
    """
    Dependencies: Gtk, WebKit2
    """

    def __init__(self, parent: Gtk.Window, content):

        super().__init__(title='HTML Preview')
        self.set_size_request(1050, 700)
        self.parent_window = parent
        self.content = content

        self.webview = WebKit2.WebView()
        self.add(self.webview)
        self.connect('destroy', self.close_webview)

        self.webview.load_html(content, None)

    def close_webview(self, widget):

        self.webview.terminate_web_process()
