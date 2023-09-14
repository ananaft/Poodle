# Gtk modules
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
# Other modules
import json


class RawText(Gtk.TextView):
    """
    Dependencies: Gtk, json
    """

    def __init__(self, content: dict):

        super().__init__(wrap_mode=Gtk.WrapMode(3))

        self.content = content

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

    def overwrite(self, content: dict):

        self.content = content

        self.textbuffer.set_text(
            json.dumps(content, ensure_ascii=False, indent=4)
        )
