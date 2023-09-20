# Gtk modules
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
# Poodle modules
import gui.treeviews
import gui.panels
import gui.grids
import gui.textviews
# Other modules
import json
import re


class MainNotebook(Gtk.Notebook):
    """
    Dependencies: Gtk, gui.treeviews, gui.panels
    """

    def __init__(self, parent: Gtk.Window):

        super().__init__()
        self.parent_window = parent

        # Question tab
        self.question_window = Gtk.ScrolledWindow()
        self.question_window.set_vexpand(True)
        self.question_table = gui.treeviews.QuestionTreeview(self.parent_window)
        self.question_window.add(self.question_table)
        self.append_page(self.question_window, Gtk.Label(label='Questions'))

        # Exam tab
        self.exam_window = Gtk.ScrolledWindow()
        self.exam_window.set_vexpand(True)
        self.exam_table = gui.treeviews.ExamTreeview(self.parent_window)
        self.exam_window.add(self.exam_table)
        self.append_page(self.exam_window, Gtk.Label(label='Exams'))

        self.connect('switch-page', self.on_switch_page)

    # Switch between ControlPanels in MainWindow when page is switched
    def on_switch_page(self, notebook, page, page_num) -> None:
        # Remove old panel from main window grid
        old_panel = [
            x for x in self.parent_window.grid.get_children()
            if isinstance(x, Gtk.ActionBar)
        ][0]
        self.parent_window.grid.remove(old_panel)
        # Replace with updated panel class
        if self.get_current_page() % 2 == 1:
            self.parent_window.control = gui.panels.MainQuestionControlPanel(self.parent_window)
        else:
            self.parent_window.control = gui.panels.MainExamControlPanel(self.parent_window)
        self.parent_window.grid.attach_next_to(self.parent_window.control,
                                               self, Gtk.PositionType.BOTTOM,
                                               1, 1)
        self.parent_window.show_all()


class QuestionNotebook(Gtk.Notebook):
    """
    Dependencies: Gtk, gui.grids, gui.textviews, gui.dialogs, json, re
    """

    def __init__(self, parent: Gtk.Window, question_content: dict):

        super().__init__()
        self.parent_window = parent

        # Normal tab
        self.question_window = Gtk.ScrolledWindow()
        self.question_window.set_vexpand(True)

        match question_content['moodle_type']:
            case 'multichoice':
                self.question_grid = gui.grids.MultiChoiceQuestionGrid(
                    self.parent_window, question_content
                    )
            case 'numerical':
                self.question_grid = gui.grids.NumericalQuestionGrid(
                    self.parent_window, question_content
                    )
            case 'shortanswer':
                self.question_grid = gui.grids.ShortanswerQuestionGrid(
                    self.parent_window, question_content
                    )
            case 'essay':
                self.question_grid = gui.grids.EssayQuestionGrid(
                    self.parent_window, question_content
                    )
            case 'matching':
                self.question_grid = gui.grids.MatchingQuestionGrid(
                    self.parent_window, question_content
                    )
            case 'gapselect':
                self.question_grid = gui.grids.GapselectQuestionGrid(
                    self.parent_window, question_content
                    )
            case 'ddimageortext':
                self.question_grid = gui.grids.DDImageOrTextQuestionGrid(
                    self.parent_window, question_content
                    )
            case 'calculated':
                self.question_grid = gui.grids.CalculatedQuestionGrid(
                    self.parent_window, question_content
                    )
            case _:
                raise Exception

        self.question_window.add(self.question_grid)
        self.append_page(self.question_window, Gtk.Label(label='Question'))

        # Raw tab
        self.raw_window = Gtk.ScrolledWindow()
        self.raw_window.set_vexpand(True)
        self.raw_page = gui.textviews.RawText(question_content)
        self.raw_window.add(self.raw_page)
        self.append_page(self.raw_window, Gtk.Label(label='Raw'))

        self.connect('switch-page', self.on_switch_page)
        self.switch_counter = 0

    # Passing data between pages on switch
    def on_switch_page(self, notebook, page, page_num):

        page_titles = ['Question', 'Raw']

        if self.switch_counter > 0:

            # Update content of previous page and pass to new page
            # Gtk.ScrolledWindow inserts Gtk.ViewPort as parent of Gtk.Grid
            if page_titles[self.switch_counter % 2] == 'Question':
                previous_page = self.get_nth_page(
                    int(not page_num)
                ).get_children()[0]
                new_page = page.get_children()[0].get_children()[0]
                # If Raw is edited in a way that invalidates JSON
                # warn user and abort page switch
                try:
                    new_content = previous_page.update_content()
                except json.decoder.JSONDecodeError as e:
                    error_msg = e.args[0]
                    dialog = gui.dialogs.OKDialog(
                        self.parent_window,
                        'Aborted switching page due to following error:',
                        error_msg
                    )
                    dialog._run()
                    self.stop_emission_by_name('switch-page')
                    # Mark line that caused error
                    if re.match("Expecting ',' delimiter", error_msg):
                        error_chars = e.doc.splitlines()[e.lineno - 2]
                    else:
                        error_chars = e.doc.splitlines()[e.lineno - 1]
                    textbuffer = previous_page.get_buffer()
                    search_match = textbuffer.get_start_iter().forward_search(
                        error_chars, 0, None
                    )
                    textbuffer.delete(search_match[0], search_match[1])
                    textbuffer.insert_markup(
                        search_match[0],
                        f'<span color="red">{error_chars}</span>',
                        -1
                    )
                    return 1
                new_page.overwrite(new_content)
            else:
                previous_page = self.get_nth_page(
                    int(not page_num)
                ).get_children()[0].get_children()[0]
                new_page = page.get_children()[0]
                new_content = previous_page.update_content()
                new_page.overwrite(new_content)

        self.switch_counter += 1


class ExamNotebook(Gtk.Notebook):
    """
    Dependencies: Gtk, gui.grids, gui.textviews, gui.dialogs, json, re
    """

    def __init__(self, parent: Gtk.Window, exam_content: dict):

        super().__init__()
        self.parent_window = parent

        # Normal tab
        self.exam_window = Gtk.ScrolledWindow()
        self.exam_window.set_vexpand(True)

        self.exam_grid = gui.grids.ExamGrid(self.parent_window, exam_content)

        self.exam_window.add(self.exam_grid)
        self.append_page(self.exam_window, Gtk.Label(label='Exam'))

        # Raw tab
        self.raw_window = Gtk.ScrolledWindow()
        self.raw_window.set_vexpand(True)
        self.raw_page = gui.textviews.RawText(exam_content)
        self.raw_window.add(self.raw_page)
        self.append_page(self.raw_window, Gtk.Label(label='Raw'))

        self.connect('switch-page', self.on_switch_page)
        self.switch_counter = 0

    # Passing data between pages on switch
    def on_switch_page(self, notebook, page, page_num):

        page_titles = ['Exam', 'Raw']

        if self.switch_counter > 0:

            # Update content of previous page and pass to new page
            # Gtk.ScrolledWindow inserts Gtk.ViewPort as parent of Gtk.Grid
            if page_titles[self.switch_counter % 2] == 'Exam':
                previous_page = self.get_nth_page(
                    int(not page_num)
                ).get_children()[0]
                new_page = page.get_children()[0].get_children()[0]
                # If Raw is edited in a way that invalidates JSON
                # warn user and abort page switch
                try:
                    new_content = previous_page.update_content()
                except json.decoder.JSONDecodeError as e:
                    error_msg = e.args[0]
                    dialog = gui.dialogs.OKDialog(
                        self.parent_window,
                        'Aborted switching page due to following error:',
                        error_msg
                    )
                    dialog._run()
                    self.stop_emission_by_name('switch-page')
                    # Mark line that caused error
                    if re.match("Expecting ',' delimiter", error_msg):
                        error_chars = e.doc.splitlines()[e.lineno - 2]
                    else:
                        error_chars = e.doc.splitlines()[e.lineno - 1]
                    textbuffer = previous_page.get_buffer()
                    search_match = textbuffer.get_start_iter().forward_search(
                        error_chars, 0, None
                    )
                    textbuffer.delete(search_match[0], search_match[1])
                    textbuffer.insert_markup(
                        search_match[0],
                        f'<span color="red">{error_chars}</span>',
                        -1
                    )
                    return 1
                new_page.overwrite(new_content)
            else:
                previous_page = self.get_nth_page(
                    int(not page_num)
                ).get_children()[0].get_children()[0]
                new_page = page.get_children()[0]
                new_content = previous_page.update_content()
                new_page.overwrite(new_content)

        self.switch_counter += 1
