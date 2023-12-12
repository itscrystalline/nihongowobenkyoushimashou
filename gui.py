import sys
from inspect import currentframe

import gi
import quiz

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk
from colorama import Fore, Style


def getLine():
    cf = currentframe()
    return cf.f_back.f_lineno


class MainWindow(Gtk.ApplicationWindow):
    def debugPrint(self, *args) -> None:
        if self.debug:
            print(f"{Fore.RED}[gui.py:{args[-1]}]{Fore.YELLOW}", *args[:-1], Style.RESET_ALL)

    def __init__(self, session: quiz.QuizSession, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session
        self.debug = session.debug

        self.progress = []
        self.currentQuestion = 0

        # populate progress
        for i in range(len(self.session.questions)):
            self.progress.append([False, self.session.questions[i]["score"]])

        css_provider = Gtk.CssProvider()
        css_provider.load_from_path('style.css')
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.set_default_size(600, 250)
        self.set_title(f"日本語を勉強しましょう! [{self.session.loadedFile}]")

        app = self.get_application()
        sm = app.get_style_manager()
        sm.set_color_scheme(Adw.ColorScheme.PREFER_DARK)

        header = Gtk.HeaderBar()
        self.set_titlebar(header)

        self.settingsButton = Gtk.Button()
        self.settingsButton.set_icon_name("preferences-system-symbolic")
        self.settingsButton.set_tooltip_text("Settings")
        header.pack_start(self.settingsButton)

        self.answerButton = Gtk.Button()
        self.answerButton.set_icon_name("dialog-question-symbolic")
        self.answerButton.set_tooltip_text("Don't know")
        header.pack_end(self.answerButton)

        toastOverlay = Adw.ToastOverlay()
        toastOverlay.set_hexpand(True)
        toastOverlay.set_vexpand(True)
        toastOverlay.add_toast(Adw.Toast(title=f"Using quiz {session.loadedFile}", timeout=1))
        self.set_child(toastOverlay)

        box = Gtk.Box()
        box.set_orientation(Gtk.Orientation.VERTICAL)
        box.set_hexpand(True)
        box.set_vexpand(True)
        toastOverlay.set_child(box)

        self.view = Adw.Carousel()
        box.append(self.view)

        carouselDots = Adw.CarouselIndicatorDots()
        carouselDots.set_carousel(self.view)

        self.buildViews()

        box.append(carouselDots)

    def buildViews(self):
        carousel = self.view

        for index, question in enumerate(self.session.questions):
            scoreText = Gtk.Label()
            scoreText.set_text(f"Score: {self.progress[index][1]}")
            scoreText.add_css_class("scoreText")
            self.progress[index].append(scoreText)

            questionText = Gtk.Label()
            questionText.set_text(question["question"])
            questionText.set_justify(Gtk.Justification.CENTER)
            questionText.set_hexpand(True)
            questionText.add_css_class("question-text")

            questionBox = Gtk.Box()
            questionBox.set_orientation(Gtk.Orientation.VERTICAL)
            questionBox.add_css_class("question-box")

            answerBox = Gtk.Box()
            answerBox.set_orientation(Gtk.Orientation.HORIZONTAL)
            answerBox.add_css_class("answer-box")

            answerGrid = Gtk.Grid()
            answerGrid.set_column_homogeneous(True)
            answerGrid.set_row_homogeneous(True)
            answerGrid.set_hexpand(True)
            answerGrid.set_vexpand(True)
            answerBox.add_css_class("answer-grid")

            for i in range(4):
                button = Gtk.Button()
                button.set_name(question["answers"][i])
                button.set_label(question["answers"][i])
                button.set_hexpand(True)
                button.set_vexpand(True)
                button.add_css_class("answer-button")
                button.connect("clicked", self.on_answer_button_clicked)
                answerGrid.attach(button, i % 2, i // 2, 1, 1)

            mainBox = Gtk.Box()
            mainBox.set_data()
            mainBox.set_orientation(Gtk.Orientation.VERTICAL)
            mainBox.set_hexpand(True)

            questionBox.append(scoreText)
            questionBox.append(questionText)

            answerBox.append(answerGrid)

            mainBox.append(questionBox)
            mainBox.append(answerBox)

            mainBox.set_name(f"{index}")

            carousel.append(mainBox)

    def on_answer_button_clicked(self, button: Gtk.Button):
        currentPage = self.view.get_position()
        if currentPage != self.currentQuestion:
            self.view.scroll_to(self.view.get_nth_page(self.currentQuestion), True)
            self.debugPrint("Scrolling to page", self.currentQuestion, getLine())
            return

        isDone = self.progress[self.currentQuestion][0]
        if isDone:
            self.advance()
            self.debugPrint("Already answered, advancing", getLine())
            return

        correctAnswer = self.session.questions[self.currentQuestion]["correct"]
        if button.get_name() == correctAnswer:
            self.progress[self.currentQuestion][0] = True
            self.progress[self.currentQuestion][1] += 1
            self.progress[self.currentQuestion][2].add_css_class("correct")
            button.add_css_class("correct")
        else:
            self.progress[self.currentQuestion][0] = True
            self.progress[self.currentQuestion][1] -= 1
            self.progress[self.currentQuestion][2].add_css_class("incorrect")
            button.add_css_class("incorrect")
            # show correct answer
            for correct in button.get_parent().get_child():
                if correct.get_name() == correctAnswer:
                    correct.add_css_class("correct")

        self.progress[self.currentQuestion][2].set_text(f"Score: {self.progress[self.currentQuestion][1]}")
        self.currentQuestion += 1

    def advance(self):
        self.view.scroll_to(self.view.get_nth_page(self.currentQuestion), True)


class MyApp(Adw.Application):
    def __init__(self, session: quiz.QuizSession, **kwargs):
        super().__init__(**kwargs)
        self.session = session
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        self.window = MainWindow(session=self.session, application=app)
        self.window.present()


if __name__ == '__main__':
    args = sys.argv[1:]
    session = quiz.QuizSession(args)

    app = MyApp(session=session, application_id="dev.iw2tryhard.nihongowobenkyoushimashou")
    app.run([])
