# Gtk modules
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, WebKit2
# Poodle modules
from poodle import config
from poodle import exam
import gui.treeviews
import gui.panels
import gui.notebooks
# Other modules
import numpy as np
import pandas as pd


class Overview(Gtk.Window):
    """
    Dependencies: Gtk, gui.treeviews, gui.panels, numpy, pandas, config
    """

    def __init__(self):

        super().__init__(title='Overview')
        self.set_size_request(1350, 900)
        self.connect('destroy', Gtk.main_quit)

        self.grid = Gtk.Grid()
        self.grid.set_column_homogeneous(True)
        self.add(self.grid)

        self.scroll_window = Gtk.ScrolledWindow()
        self.scroll_window.set_vexpand(True)
        self.table = gui.treeviews.QuestionTreeview(self)
        self.scroll_window.add(self.table)
        self.control = gui.panels.OverviewControlPanel(self)

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
        exam_list = sorted([e['name'] for e in config.EXAMS.find()])
        df = pd.DataFrame(sorted(
            [
                [q['name'], q['difficulty'], q['time_est']] +
                [round(q['in_exams'][e] / q['points'], 2)
                 if e in q['in_exams'] else '.' for e in exam_list
                ]
                for q in config.QUESTIONS.find() if q['name'][-2:] != '00'
            ]),
            columns = ['question', 'difficulty', 'time'] + exam_list
        )
        # Make exam appearance counter
        transform = lambda x: int(type(x) == float)
        appearances = df[exam_list].applymap(transform).sum(axis=1)
        df.insert(1, 'appearances', appearances)

        data = row_to_list(df)
        column_types = [numpy_to_native(x.type) for x in list(df.dtypes)]
        column_names = ['question', 'appearances', 'difficulty', 'time__est'] + list(df.columns)[4:]

        return data, column_types, column_names


class QuestionWindow(Gtk.Window):
    """
    Dependencies: Gtk, gui.notebooks
    """

    def __init__(self, parent, question_content: dict):

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

    def __init__(self, parent, table_name: str, table: list):

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

    def __init__(self, parent, question_name: str, variables: list):

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
    Dependencies: Gtk, gui.panels, config, exam
    """

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

        self.control = gui.panels.ExamControlPanel(self)

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
            dialog = Gtk.MessageDialog(
                transient_for=self.parent_window,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text='Marked questions could not be found in database!'
            )
            dialog.run()
            dialog.destroy()

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
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.YES_NO,
            text=('Are you sure you want to create ' +
                  f'{self.get_property("title")} with the current ' +
                  'question selection?')
        )
        response = dialog.run()
        if response == Gtk.ResponseType.YES:
            exam.create_exam(self.get_property('title'), mode='gui',
                        questions=question_list)
            dialog.destroy()
            self.destroy()
        elif response == Gtk.ResponseType.NO:
            dialog.destroy()

    def remove_parent_attribute(self, window):
        delattr(self.parent_window, 'exam_window')


class HTMLPreviewWindow(Gtk.Window):
    """
    Dependencies: Gtk, WebKit2
    """

    def __init__(self, parent, content):

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
