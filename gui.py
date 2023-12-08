import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Things will go here
        self.set_default_size(600, 250)
        self.set_title("日本語を勉強しましょう")

        app = self.get_application()
        sm = app.get_style_manager()
        sm.set_color_scheme(Adw.ColorScheme.PREFER_DARK)

        self.header = Gtk.HeaderBar()
        self.set_titlebar(self.header)


class MyApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.win = MainWindow(application=app)
        self.win.present()


app = MyApp(application_id="dev.iw2tryhard.nihongowobenkyoushimashou")
app.run(sys.argv)
