# Gtk modules
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
# Other modules
import json


class RawQuestionText(Gtk.TextView):
    """
    Dependencies: Gtk, json
    """

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
