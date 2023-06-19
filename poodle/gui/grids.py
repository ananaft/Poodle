# Gtk modules
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
# Poodle modules
import gui.windows
from poodle import config


class GeneralQuestionGrid(Gtk.Grid):
    """
    Dependencies: Gtk, gui.windows, config
    """

    def __init__(self, parent, question_content: dict):

        super().__init__()
        self.set_column_spacing(100)
        self.set_row_spacing(20)
        self.parent_window = parent

        self.content = question_content
        self.grid_rows = 0

        self.name_label = Gtk.Label(label='name')
        self.attach(self.name_label, 0, 0, 1, 1)
        self.grid_rows += 1

        self.name_field = Gtk.Entry()
        self.name_field.set_property('name', 'name')
        self.name_field.set_hexpand(True)
        self.name_field.set_text(self.content['name'])
        self.name_field.set_editable(False)
        self.attach_next_to(self.name_field,
                            self.name_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.moodle_type_label = Gtk.Label(label='moodle_type')
        self.attach(self.moodle_type_label, 0, self.grid_rows, 1, 1)
        self.grid_rows += 1

        self.moodle_type_field = Gtk.Entry()
        self.moodle_type_field.set_property('name', 'moodle_type')
        self.moodle_type_field.set_hexpand(True)
        self.moodle_type_field.set_text(self.content['moodle_type'])
        self.moodle_type_field.set_editable(False)
        self.attach_next_to(self.moodle_type_field,
                            self.moodle_type_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.question_label = Gtk.Label(label='question')
        self.attach(self.question_label, 0, self.grid_rows, 1, 1)
        self.grid_rows += 1

        self.question_field = Gtk.TextView(wrap_mode=Gtk.WrapMode(3))
        self.question_field.set_property('name', 'question')
        self.question_field.set_hexpand(True)
        self.question_buffer = self.question_field.get_buffer()
        self.question_buffer.set_text(self.content['question'])
        self.attach_next_to(self.question_field,
                            self.question_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.points_label = Gtk.Label(label='points')
        self.attach(self.points_label, 0, self.grid_rows, 1, 1)
        self.grid_rows += 1

        self. points_field = Gtk.Entry()
        self.points_field.set_property('name', 'points')
        self.points_field.set_hexpand(True)
        self.points_field.set_text(str(self.content['points']))
        self.attach_next_to(self.points_field,
                            self.points_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.difficulty_label = Gtk.Label(label='difficulty')
        self.attach(self.difficulty_label, 0, self.grid_rows, 1, 1)
        self.grid_rows += 1

        self. difficulty_field = Gtk.Entry()
        self.difficulty_field.set_property('name', 'difficulty')
        self.difficulty_field.set_hexpand(True)
        self.difficulty_field.set_text(str(self.content['difficulty']))
        self.attach_next_to(self.difficulty_field,
                            self.difficulty_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.time_est_label = Gtk.Label(label='time_est')
        self.attach(self.time_est_label, 0, self.grid_rows, 1, 1)
        self.grid_rows += 1

        self. time_est_field = Gtk.Entry()
        self.time_est_field.set_property('name', 'time_est')
        self.time_est_field.set_hexpand(True)
        self.time_est_field.set_text(str(self.content['time_est']))
        self.attach_next_to(self.time_est_field,
                            self.time_est_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.family_type_label = Gtk.Label(label='family_type')
        self.attach(self.family_type_label, 0, self.grid_rows, 1, 1)
        self.grid_rows += 1

        self.family_type_field = Gtk.Entry()
        self.family_type_field.set_property('name', 'family_type')
        self.family_type_field.set_hexpand(True)
        self.family_type_field.set_text(self.content['family_type'])
        self.family_type_field.set_editable(False)
        self.attach_next_to(self.family_type_field,
                            self.family_type_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.in_exams_label = Gtk.Label(label='in_exams')
        self.attach(self.in_exams_label, 0, self.grid_rows, 1, 1)
        self.grid_rows += 1

        self.in_exams_field = SimpleDictGrid(
            self.content['in_exams'], editable=False, add=False,
            output_type=float
        )
        self.in_exams_field.set_property('name', 'in_exams')
        self.attach_next_to(self.in_exams_field,
                            self.in_exams_label,
                            Gtk.PositionType.RIGHT, 2, 1)


    def preview_html(self, button):

        content = self.question_buffer.get_text(
            self.question_buffer.get_start_iter(),
            self.question_buffer.get_end_iter(),
            include_hidden_chars=True
        )

        new_window = gui.windows.HTMLPreviewWindow(self, content)
        new_window.show_all()


    # will be called by sub-classes
    def check_optional(self):

        # Optional fields
        if 'img_files' not in self.content.keys():
            self.img_files_button = Gtk.Button(label='Add img_files')
            self.attach(self.img_files_button, 0, self.grid_rows, 1, 1)
            self.grid_rows += 1
            self.img_files_button.connect(
                'clicked', self.build_optional, 'img_files', ['']
            )
        else:
            self.build_optional(None, 'img_files', self.content['img_files'])

        if 'tables' not in self.content.keys():
            self.tables_button = Gtk.Button(label='Add tables')
            self.attach(self.tables_button, 0, self.grid_rows, 1, 1)
            self.grid_rows += 1
            self.tables_button.connect(
                'clicked', self.build_optional, 'tables', {}
            )
        else:
            self.build_optional(None, 'tables', self.content['tables'])

    def build_optional(self, button, field: str, content):
        
        if field == 'img_files':
            self.img_files_label = Gtk.Label(label='img_files')
            self.attach(self.img_files_label, 0, self.grid_rows, 1, 1)
            self.grid_rows += 1
            self.img_files_field = SimpleListGrid(content)
            self.img_files_field.set_property('name', 'img_files')
            self.attach_next_to(self.img_files_field,
                                self.img_files_label,
                                Gtk.PositionType.RIGHT, 2, 1)
            self.img_files_label.show()
            self.img_files_field.show_all()
            # Remove button from attributes and GUI
            if button:
                del self.img_files_button
                button.destroy()

        elif field == 'tables':
            self.tables_label = Gtk.Label(label='tables')
            self.attach(self.tables_label, 0, self.grid_rows, 1, 1)
            self.grid_rows += 1
            self.tables_field = DictButtonGrid(
                self, 'Show/edit', self.show_table, (), content, False, 'tbl'
            )
            self.tables_field.set_property('name', 'tables')
            self.attach_next_to(self.tables_field,
                                self.tables_label,
                                Gtk.PositionType.RIGHT, 2, 1)
            self.tables_label.show()
            self.tables_field.show_all()
            # Remove button from attributes and GUI
            if button:
                del self.tables_button
                button.destroy()

    def show_table(self, button, grid, data):

        # Get args for window
        tbl_name = grid.get_child_at(
            0, int(button.get_property('name'))
            ).get_text()
        tbl = data[tbl_name]
        # Initialize table window
        new_window = gui.windows.TableWindow(self.parent_window, tbl_name, tbl)
        new_window.show_all()

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
                case DictButtonGrid.__name__:
                    return field_child.get_content()
                case _:
                    raise Exception
        
        # Create label/field pairs from children
        child_pairs = list(zip(
            [x for x in self.get_children() if type(x) != Gtk.Button][1::2],
            [x for x in self.get_children() if type(x) != Gtk.Button][0::2]
        ))
        # Update self.content dict
        for i in child_pairs:
            # Preserve original data types of entry fields
            if type(i[1]) == Gtk.Entry:
                try:
                    original_type = config.KEY_TYPES['general'][i[0].get_property('label')]
                except KeyError:
                    try:
                        original_type = config.KEY_TYPES['optional'][i[0].get_property('label')]
                    except KeyError:
                        original_type = config.KEY_TYPES[
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
                case DictButtonGrid.__name__:
                    child.overwrite(v)
                case str.__name__:
                    pass
                case _:
                    raise Exception


class MultiChoiceQuestionGrid(GeneralQuestionGrid):
    """
    Dependencies: Gtk
    """

    def __init__(self, parent, question_content: dict):

        super().__init__(parent, question_content)

        self.insert_row(3)
        self.grid_rows += 1
        self.preview_button = Gtk.Button(label='Preview HTML')
        self.attach(self.preview_button, 0, 3, 1, 1)
        self.preview_button.connect('clicked', self.preview_html)

        self.insert_row(4)
        self.grid_rows += 1
        self.correct_answers_label = Gtk.Label(label='correct_answers')
        self.attach(self.correct_answers_label, 0, 4, 1, 1)
        self.correct_answers_field = SimpleListGrid(
            self.content['correct_answers']
        )
        self.correct_answers_field.set_property('name', 'correct_answers')
        self.attach_next_to(self.correct_answers_field,
                            self.correct_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.insert_row(5)
        self.grid_rows += 1
        self.false_answers_label = Gtk.Label(label='false_answers')
        self.attach(self.false_answers_label, 0, 5, 1, 1)
        self.false_answers_field = SimpleListGrid(
            self.content['false_answers']
        )
        self.false_answers_field.set_property('name', 'false_answers')
        self.attach_next_to(self.false_answers_field,
                            self.false_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.insert_row(6)
        self.grid_rows += 1
        self.single_label = Gtk.Label(label='single')
        self.attach(self.single_label, 0, 6, 1, 1)
        self.single_field = Gtk.Entry()
        self.single_field.set_property('name', 'single')
        self.single_field.set_hexpand(True)
        self.single_field.set_text(str(self.content['single']))
        self.attach_next_to(self.single_field,
                            self.single_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        # Optional question fields
        self.check_optional()


class NumericalQuestionGrid(GeneralQuestionGrid):
    """
    Dependencies: Gtk
    """

    def __init__(self, parent, question_content: dict):

        super().__init__(parent, question_content)

        self.insert_row(3)
        self.grid_rows += 1
        self.preview_button = Gtk.Button(label='Preview HTML')
        self.attach(self.preview_button, 0, 3, 1, 1)
        self.preview_button.connect('clicked', self.preview_html)

        self.insert_row(4)
        self.grid_rows += 1
        self.correct_answers_label = Gtk.Label(label='correct_answers')
        self.attach(self.correct_answers_label, 0, 4, 1, 1)
        self.correct_answers_field = SimpleListGrid(
            self.content['correct_answers'], add=False, output_type=float
        )
        self.correct_answers_field.set_property('name', 'correct_answers')
        self.attach_next_to(self.correct_answers_field,
                            self.correct_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.insert_row(5)
        self.grid_rows += 1
        self.tolerance_label = Gtk.Label(label='tolerance')
        self.attach(self.tolerance_label, 0, 5, 1, 1)
        self.tolerance_field = Gtk.Entry()
        self.tolerance_field.set_property('name', 'tolerance')
        self.tolerance_field.set_hexpand(True)
        self.tolerance_field.set_text(str(self.content['tolerance']))
        self.attach_next_to(self.tolerance_field,
                            self.tolerance_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        # Optional question fields
        self.check_optional()


class ShortanswerQuestionGrid(GeneralQuestionGrid):
    """
    Dependencies: Gtk
    """

    def __init__(self, parent, question_content: dict):

        super().__init__(parent, question_content)

        self.insert_row(3)
        self.grid_rows += 1
        self.preview_button = Gtk.Button(label='Preview HTML')
        self.attach(self.preview_button, 0, 3, 1, 1)
        self.preview_button.connect('clicked', self.preview_html)

        self.insert_row(4)
        self.grid_rows += 1
        self.correct_answers_label = Gtk.Label(label='correct_answers')
        self.attach(self.correct_answers_label, 0, 4, 1, 1)
        self.correct_answers_field = SimpleListGrid(
            self.content['correct_answers']
        )
        self.correct_answers_field.set_property('name', 'correct_answers')
        self.attach_next_to(self.correct_answers_field,
                            self.correct_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.insert_row(5)
        self.grid_rows += 1
        self.usecase_label = Gtk.Label(label='usecase')
        self.attach(self.usecase_label, 0, 5, 1, 1)
        self.usecase_field = Gtk.Entry()
        self.usecase_field.set_property('name', 'usecase')
        self.usecase_field.set_hexpand(True)
        self.usecase_field.set_text(str(self.content['usecase']))
        self.attach_next_to(self.usecase_field,
                            self.usecase_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        # Optional question fields
        self.check_optional()


class EssayQuestionGrid(GeneralQuestionGrid):
    """
    Dependencies: Gtk
    """

    def __init__(self, parent, question_content: dict):

        super().__init__(parent, question_content)

        self.insert_row(3)
        self.grid_rows += 1
        self.preview_button = Gtk.Button(label='Preview HTML')
        self.attach(self.preview_button, 0, 3, 1, 1)
        self.preview_button.connect('clicked', self.preview_html)

        self.insert_row(4)
        self.grid_rows += 1
        self.answer_files_label = Gtk.Label(label='answer_files')
        self.attach(self.answer_files_label, 0, 4, 1, 1)
        self.answer_files_field = SimpleListGrid(
            self.content['answer_files'], add=False, output_type=int
        )
        self.answer_files_field.set_property('name', 'answer_files')
        self.attach_next_to(self.answer_files_field,
                            self.answer_files_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        # Optional question fields
        self.check_optional()


class MatchingQuestionGrid(GeneralQuestionGrid):
    """
    Dependencies: Gtk
    """

    def __init__(self, parent, question_content: dict):

        super().__init__(parent, question_content)

        self.insert_row(3)
        self.grid_rows += 1
        self.preview_button = Gtk.Button(label='Preview HTML')
        self.attach(self.preview_button, 0, 3, 1, 1)
        self.preview_button.connect('clicked', self.preview_html)

        self.insert_row(4)
        self.grid_rows += 1
        self.correct_answers_label = Gtk.Label(label='correct_answers')
        self.attach(self.correct_answers_label, 0, 4, 1, 1)
        self.correct_answers_field = SimpleDictGrid(
            self.content['correct_answers']
        )
        self.correct_answers_field.set_property('name', 'correct_answers')
        self.attach_next_to(self.correct_answers_field,
                            self.correct_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.insert_row(5)
        self.grid_rows += 1
        self.false_answers_label = Gtk.Label(label='false_answers')
        self.attach(self.false_answers_label, 0, 5, 1, 1)
        self.false_answers_field = SimpleListGrid(
            self.content['false_answers']
        )
        self.false_answers_field.set_property('name', 'false_answers')
        self.attach_next_to(self.false_answers_field,
                            self.false_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        # Optional question fields
        self.check_optional()


class GapselectQuestionGrid(GeneralQuestionGrid):
    """
    Dependencies: Gtk
    """

    def __init__(self, parent, question_content: dict):

        super().__init__(parent, question_content)

        self.insert_row(3)
        self.grid_rows += 1
        self.preview_button = Gtk.Button(label='Preview HTML')
        self.attach(self.preview_button, 0, 3, 1, 1)
        self.preview_button.connect('clicked', self.preview_html)

        self.insert_row(4)
        self.grid_rows += 1
        self.correct_answers_label = Gtk.Label(label='correct_answers')
        self.attach(self.correct_answers_label, 0, 4, 1, 1)
        self.correct_answers_field = DictListGrid(
            self.content['correct_answers']
        )
        self.correct_answers_field.set_property('name', 'correct_answers')
        self.attach_next_to(self.correct_answers_field,
                            self.correct_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.insert_row(5)
        self.grid_rows += 1
        self.false_answers_label = Gtk.Label(label='false_answers')
        self.attach(self.false_answers_label, 0, 5, 1, 1)
        self.false_answers_field = DictListGrid(
            self.content['false_answers']
        )
        self.false_answers_field.set_property('name', 'false_answers')
        self.attach_next_to(self.false_answers_field,
                            self.false_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        # Optional question fields
        self.check_optional()


class DDImageOrTextQuestionGrid(GeneralQuestionGrid):
    """
    Dependencies: Gtk
    """

    def __init__(self, parent, question_content: dict):

        super().__init__(parent, question_content)

        self.insert_row(3)
        self.grid_rows += 1
        self.preview_button = Gtk.Button(label='Preview HTML')
        self.attach(self.preview_button, 0, 3, 1, 1)
        self.preview_button.connect('clicked', self.preview_html)

        self.insert_row(4)
        self.grid_rows += 1
        self.correct_answers_label = Gtk.Label(label='correct_answers')
        self.attach(self.correct_answers_label, 0, 4, 1, 1)
        self.correct_answers_field = SimpleListGrid(
            self.content['correct_answers']
        )
        self.correct_answers_field.set_property('name', 'correct_answers')
        self.attach_next_to(self.correct_answers_field,
                            self.correct_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.insert_row(5)
        self.grid_rows += 1
        self.drops_label = Gtk.Label(label='drops')
        self.attach(self.drops_label, 0, 5, 1, 1)
        self.drops_field = DictListGrid(
            self.content['drops'], list_add=False, new_list_length=2,
            output_type=int
        )
        self.drops_field.set_property('name', 'drops')
        self.attach_next_to(self.drops_field,
                            self.drops_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        # Optional question fields
        self.check_optional()


class CalculatedQuestionGrid(GeneralQuestionGrid):
    """
    Dependencies: Gtk, gui.windows
    """

    def __init__(self, parent, question_content: dict):

        super().__init__(parent, question_content)

        self.insert_row(3)
        self.grid_rows += 1
        self.preview_button = Gtk.Button(label='Preview HTML')
        self.attach(self.preview_button, 0, 3, 1, 1)
        self.preview_button.connect('clicked', self.preview_html)

        self.insert_row(4)
        self.grid_rows += 1
        self.correct_answers_label = Gtk.Label(label='correct_answers')
        self.attach(self.correct_answers_label, 0, 4, 1, 1)
        self.correct_answers_field = SimpleListGrid(
            self.content['correct_answers'], add=False
        )
        self.correct_answers_field.set_property('name', 'correct_answers')
        self.attach_next_to(self.correct_answers_field,
                            self.correct_answers_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.insert_row(5)
        self.grid_rows += 1
        self.vars_label = Gtk.Label(label='vars')
        self.attach(self.vars_label, 0, 5, 1, 1)
        self.vars_field = SimpleListGrid(
            self.content['vars']
        )
        self.vars_field.set_property('name', 'vars')
        self.attach_next_to(self.vars_field,
                            self.vars_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        self.insert_row(6)
        self.grid_rows += 1
        self.tolerance_label = Gtk.Label(label='tolerance')
        self.attach(self.tolerance_label, 0, 6, 1, 1)
        self.tolerance_field = SimpleListGrid(
            self.content['tolerance'], add=False, output_type=[float, str, int]
        )
        self.tolerance_field.set_property('name', 'tolerance')
        self.attach_next_to(self.tolerance_field,
                            self.tolerance_label,
                            Gtk.PositionType.RIGHT, 2, 1)

        # Optional question fields
        self.check_optional()

        # Connection to variable creation file
        self.file_button = Gtk.Button(label='Edit variable creation')
        self.file_button.connect('clicked', self.edit_var_file)
        self.attach(self.file_button, 0, self.grid_rows, 1, 1)
        self.grid_rows += 1

    def edit_var_file(self, button):

        new_window = gui.windows.VariableFileWindow(
            self.parent_window,
            self.content['name'],
            self.vars_field.get_content()
        )
        new_window.show_all()


class SimpleListGrid(Gtk.Grid):
    """
    Dependencies: Gtk
    """

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
    """
    Dependencies: Gtk
    """

    def __init__(self, dict_field: dict,
                 editable: bool = True,
                 add: bool = True,
                 output_type: type = str):

        super().__init__()
        self.set_column_spacing(50)
        self.set_row_spacing(10)

        for n, key in enumerate(dict_field.keys()):
            key_entry = Gtk.Entry()
            key_entry.set_hexpand(True)
            key_entry.set_text(key)
            key_entry.set_editable(editable)
            self.attach(key_entry, 0, n, 1, 1)

        for n, value in enumerate(dict_field.values()):
            value_entry = Gtk.Entry()
            value_entry.set_hexpand(True)
            value_entry.set_text(str(value))
            value_entry.set_editable(editable)
            self.attach(value_entry, 1, n, 1, 1)

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
            child_list = list(reversed(self.get_children()[1:]))
        else:
            child_list = list(reversed(self.get_children()))
        content = dict(zip(
            # First half is keys
            [x.get_text() for x in child_list[:len(child_list)//2]],
            # Second half is values
            [x.get_text() for x in child_list[len(child_list)//2:]]
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
    """
    Dependencies: Gtk
    """

    def __init__(
            self, dict_field: dict, dict_editable: bool = True,
            dict_add: bool = True, list_editable: bool = True,
            list_add: bool = True, new_list_length: int = 1,
            output_type: tuple[type, list] = str
    ):

        super().__init__()
        self.set_column_spacing(50)
        self.set_row_spacing(10)

        self.output_type = output_type
        self.n_rows = len(dict_field.keys())
        self.new_list_length = new_list_length
        self.list_editable = list_editable
        self.list_add = list_add

        for n, key in enumerate(dict_field.keys()):
            key_entry = Gtk.Entry()
            key_entry.set_hexpand(True)
            key_entry.set_text(key)
            key_entry.set_editable(dict_editable)
            self.attach(key_entry, 0, n, 1, 1)
            self.attach_next_to(
                SimpleListGrid(
                    dict_field[key], self.list_editable,
                    self.list_add, self.output_type
                ),
                key_entry, Gtk.PositionType.RIGHT, 1, 1
            )

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
            child_list = list(reversed(self.get_children()[1:]))
        else:
            child_list = list(reversed(self.get_children()))
        content = dict(zip(
            [x.get_text() for x in child_list[::2]],
            [x.get_content() if isinstance(x, SimpleListGrid)
             else x.get_text() for x in child_list[1::2]]
        ))

        return content

    def overwrite(self, input_dict: dict):

        child_list = list(reversed(self.get_children()[1:]))
        key_pairs = zip(
            input_dict.keys(),
            child_list[::2]
        )
        value_pairs = zip(
            input_dict.values(),
            child_list[1::2]
        )

        for i, j in key_pairs:
            j.set_text(str(i))

        for i, j in value_pairs:
            if type(j) == Gtk.Entry:
                j.set_text(str(i))
            elif type(j) == SimpleListGrid:
                j.overwrite(i)


class DictButtonGrid(Gtk.Grid):
    """
    Dependencies: Gtk
    """

    def __init__(
        self, parent, button_label: str, fn, arguments: tuple,
        dict_field: dict, dict_editable: bool = True, key_default: str = '',
        dict_add: bool = True,
    ):

        super().__init__()
        self.set_column_spacing(50)
        self.set_row_spacing(10)

        self.parent = parent
        self.button_label = button_label
        self.fn = fn
        self.arguments = arguments
        self.data = dict_field
        self.dict_editable = dict_editable
        self.key_default = key_default
        self.n_rows = len(dict_field.keys())

        for n, key in enumerate(self.data.keys()):
            key_entry = Gtk.Entry()
            key_entry.set_hexpand(True)
            key_entry.set_text(key)
            key_entry.set_editable(self.dict_editable)
            self.attach(key_entry, 0, n, 1, 1)
            button = Gtk.Button(label=self.button_label, name=str(n))
            button.connect('clicked', self.fn, self, self.data)
            self.attach_next_to(
                button, key_entry,
                Gtk.PositionType.RIGHT, 1, 1
            )

        if dict_add:
            self.add_button = Gtk.Button(label='+')
            self.add_button.connect('clicked', self.add_row)
            self.attach(self.add_button, 0, self.n_rows, 1, 1)

    def add_row(self, button):

        key_entry = Gtk.Entry()
        key_entry.set_hexpand(True)
        if self.key_default:
            key_entry.set_text(self.key_default + f'{self.n_rows + 1:02d}')
            key_entry.set_editable(self.dict_editable)
        self.insert_row(self.n_rows)
        self.attach(key_entry, 0, self.n_rows, 1, 1)
        key_entry.show()

        button = Gtk.Button(label=self.button_label, name=str(self.n_rows))
        button.connect('clicked', self.fn, self, self.data)
        self.attach_next_to(
            button, key_entry,
            Gtk.PositionType.RIGHT, 1, 1
        )
        button.show()

        self.n_rows += 1
        self.data[key_entry.get_text()] = [[''],['']]

    def get_content(self) -> dict:

        return self.data

    def overwrite(self, input_dict: dict):

        self.data = input_dict
        # Reconnect buttons to updated self.data
        for c in self.get_children():
            if type(c) == Gtk.Button and c.get_property('label') != '+':
                c.disconnect_by_func(self.fn)
                c.connect('clicked', self.fn, self, self.data)


class TableColumnGrid(Gtk.Grid):
    """
    Dependencies: Gtk
    """

    def __init__(self, parent, column_titles: list):

        super().__init__()
        self.parent_window = parent
        self.n_rows = 0

        # Fill grid
        for i in column_titles:
            entry = Gtk.Entry()
            entry.set_hexpand(True)
            entry.set_text(i)
            self.attach(entry, 0, self.n_rows, 2, 1)
            self.n_rows += 1

        self.add_button = Gtk.Button(label='+')
        self.add_button.connect('clicked', self.add_row)
        self.attach(self.add_button, 0, self.n_rows, 1, 1)

        self.remove_button = Gtk.Button(label='-')
        self.remove_button.connect('clicked', self.remove_row)
        self.attach(self.remove_button, 1, self.n_rows, 1, 1)

    def add_row(self, button):

        entry = Gtk.Entry()
        entry.set_hexpand(True)
        self.insert_row(self.n_rows)
        self.attach(entry, 0, self.n_rows, 2, 1)
        self.show_all()
        self.n_rows += 1

    def remove_row(self, button):

        if self.n_rows > 1:
            child = self.get_child_at(0, self.n_rows - 1)
            self.remove(child)
            self.n_rows -= 1
