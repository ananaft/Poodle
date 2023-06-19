# Gtk Modules
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
# Poodle modules
from poodle import config
import gui.windows
# Other modules
import re


class QuestionTreeview(Gtk.TreeView):
    """
    Dependencies: Gtk, Gdk, config, gui.windows, re
    """

    def __init__(self, parent):

        super().__init__()
        self.parent_window = parent

        self.build_table(*self.parent_window.load_data())

        self.connect('key-press-event', self.on_key_press)

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
            k: default_fill('general', k, v)
            for k, v in config.KEY_TYPES['general'].items()
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
        for mt in config.KEY_TYPES.keys():
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
                config.KEY_TYPES[question_content['moodle_type']].items()
            })
            new_window = gui.windows.QuestionWindow(self.parent_window, question_content)
            # Make certain fields editable
            new_window.notebook.question_grid.name_field.set_editable(True)
            new_window.notebook.question_grid.family_type_field.set_editable(True)
            new_window.show_all()
        elif response == Gtk.ResponseType.CANCEL:
            pass
        dialog.destroy()

    # Show selected question in new window
    def view_question(self) -> None:

        selected_row = self.get_selection()
        model, treeiter = selected_row.get_selected()
        question_name = model[treeiter][0]
        question_content = config.QUESTIONS.find_one({'name': question_name})
        question_content.pop('_id')

        new_window = gui.windows.QuestionWindow(self.parent_window, question_content)
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
                self.parent_window.exam_window = gui.windows.ExamWindow(
                    self.parent_window, exam_name
                )
                self.parent_window.exam_window.show_all()
                dialog.destroy()
            elif response == Gtk.ResponseType.CANCEL:
                dialog.destroy()
                delattr(self.parent_window, 'exam_window')
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
        elif field == 'appearances':
            # Check for allowed math expressions
            is_expression = bool(re.match(r'\s*([<>]=?|\!=)\s*\d+\.?\d*\s*$', search))
            if is_expression:
                return eval(str(model[iterator][1]) + search)
            else:
                return str(model[iterator][1]) == search
        elif field == 'difficulty':
            # Check for allowed math expressions
            is_expression = bool(re.match(r'\s*([<>]=?|\!=)\s*\d+\.?\d*\s*$', search))
            if is_expression:
                return eval(str(model[iterator][2]) + search)
            else:
                return str(model[iterator][2]) == search
        elif field == 'time_est':
            # Check for allowed math expressions
            is_expression = bool(re.match(r'\s*([<>]=?|\!=)\s*\d+\.?\d*\s*$', search))
            if is_expression:
                return eval(str(model[iterator][3]) + search)
            else:
                return str(model[iterator][3]) == search
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
            case 'Add to exam':
                self.add_to_exam()
            case 'Filter':
                self.filter.refilter()

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
            case 'f':
                self.filter.refilter()


class TableTreeView(Gtk.TreeView):
    """
    Dependencies: Gtk, Gdk, gui.grids
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

        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            message_type=Gtk.MessageType.OTHER,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text='Edit columns below:'
        )
        # Grid of column titles
        box = dialog.get_message_area()
        column_titles = [x.get_title() for x in self.get_columns()]
        column_grid = gui.grids.TableColumnGrid(self.parent_window, column_titles)
        box.pack_end(column_grid, True, True, 10)
        box.show_all()
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            # Create new table
            new_table = []
            # Columns
            new_table.append(
                list(reversed(
                    [x.get_text() for x in column_grid.get_children()
                     if type(x) == Gtk.Entry]
                     ))
                )
            # Rows
            self.liststore.foreach(self.insert_rows, new_table)
            # Fill in potentially missing values due to added columns
            max_cols = max([len(x) for x in new_table])
            new_table = [x + [''] * (max_cols - len(x)) for x in new_table]
            # Remove old table from parent window and rebuild
            self.parent_window.scroll_window.remove(self)
            for c in self.get_columns():
                self.remove_column(c)
            self.build_table(new_table)
            self.parent_window.scroll_window.add(self)
        elif response == Gtk.ResponseType.CANCEL:
            pass
        dialog.destroy()

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
