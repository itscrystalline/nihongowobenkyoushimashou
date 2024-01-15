import sys
from inspect import currentframe

import gi
import quiz

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk, GdkPixbuf
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

        self.scoreDisplayTracker = []
        self.currentQuestion = 0
        self.correctAnswers = 0

        # populate progress
        for i in range(len(self.session.questions)):
            self.scoreDisplayTracker.append([self.session.questions[i]["score"]])

        css_provider = Gtk.CssProvider()
        css_provider.load_from_path('style.css')
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.set_default_size(800, 475)
        self.set_title(f"日本語を勉強しましょう! [{self.session.loadedFile}]")

        app = self.get_application()
        sm = app.get_style_manager()
        sm.set_color_scheme(Adw.ColorScheme.PREFER_DARK)

        header = Gtk.HeaderBar()
        self.set_titlebar(header)

        self.answerButton = Gtk.Button()
        self.answerButton.set_icon_name("dialog-question-symbolic")
        self.answerButton.set_tooltip_text("Don't know")
        self.answerButton.connect("clicked", self.dontKnow)
        header.pack_start(self.answerButton)

        returnButton = Gtk.Button()
        returnButton.set_icon_name("view-refresh-symbolic")
        returnButton.set_tooltip_text("Return to current question")
        returnButton.connect("clicked", lambda _: self.scrollToCurrent())
        header.pack_start(returnButton)

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

        # question screens
        self.buildViews()

        # end screen
        self.endBox = Adw.StatusPage()
        self.endBox.set_title("Quiz not done!")
        self.endBox.set_description(f"Finish the quiz to see your score!")
        self.endBox.set_icon_name("dialog-warning-symbolic")

        self.endButton = Gtk.Button()
        self.endButton.set_label("Return to quiz")
        self.endButton.set_css_classes(["suggested-action", "pill", "endButton"])
        self.endButton.connect("clicked", lambda _: self.scrollToCurrent())
        self.endButton.set_halign(Gtk.Align.CENTER)

        self.endBox.set_child(self.endButton)
        self.view.append(self.endBox)

        box.append(carouselDots)

        self.connect('close-request', lambda _: session.saveSet())

    def buildViews(self):
        carousel = self.view

        for index, question in enumerate(self.session.questions):
            scoreText = Gtk.Label()
            scoreText.set_text(f"Score: {self.scoreDisplayTracker[index][0]}")
            scoreText.add_css_class("scoreText")
            self.scoreDisplayTracker[index].append(scoreText)

            questionText = Gtk.Label()
            questionText.set_text(question["question"])
            questionText.set_justify(Gtk.Justification.CENTER)
            questionText.set_hexpand(True)
            questionText.add_css_class("question-text")

            questionBox = Gtk.Box()
            questionBox.set_orientation(Gtk.Orientation.VERTICAL)
            questionBox.add_css_class("question-box")
            questionBox.set_vexpand(True)
            questionBox.set_valign(Gtk.Align.CENTER)

            answerBox = Gtk.Box()
            answerBox.set_orientation(Gtk.Orientation.HORIZONTAL)
            answerBox.add_css_class("answer-box")
            answerBox.set_vexpand(True)

            answerGrid = Gtk.Grid()
            answerGrid.set_column_homogeneous(True)
            answerGrid.set_row_homogeneous(True)
            answerGrid.set_hexpand(True)
            answerGrid.set_vexpand(True)
            answerGrid.add_css_class("answer-grid")

            for i in range(4):
                button = Gtk.Button()
                button.set_name(question["answers"][i][0] + "|" + question["answers"][i][1])
                button.set_hexpand(True)
                button.set_vexpand(True)
                button.add_css_class("answer-button")
                button.connect("clicked", self.onAnswerButtonClicked)

                if question["answers"][i] == question["correct"]:
                    button.add_css_class("correct")

                if not question["answers"][i][0] == "":
                    button.set_label(question["answers"][i][0])

                if not question["answers"][i][1] == "":
                    img = Gtk.Image().new_from_file(question["answers"][i][1])
                    button.set_child(img)

                answerGrid.attach(button, i % 2, i // 2, 1, 1)

            mainBox = Gtk.Box()
            mainBox.set_orientation(Gtk.Orientation.VERTICAL)
            mainBox.set_hexpand(True)

            questionBox.append(scoreText)
            questionBox.append(questionText)

            answerBox.append(answerGrid)

            mainBox.append(questionBox)
            mainBox.append(answerBox)

            mainBox.set_name(f"{index}")

            carousel.append(mainBox)

            self.debugPrint("progress", self.scoreDisplayTracker, getLine())

    def onAnswerButtonClicked(self, button: Gtk.Button):
        currentPage = self.view.get_position()
        if currentPage != self.currentQuestion:
            self.scrollToCurrent()
            self.debugPrint("Scrolling to page", self.currentQuestion, getLine())
            return

        correctAnswer = self.session.questions[self.currentQuestion]["correct"]
        if button.get_name().split("|") == correctAnswer:
            self.scoreDisplayTracker[self.currentQuestion][0] += 1
            self.scoreDisplayTracker[self.currentQuestion][1].add_css_class("correct")
            self.correctAnswers += 1
        else:
            self.scoreDisplayTracker[self.currentQuestion][0] -= 1
            self.scoreDisplayTracker[self.currentQuestion][1].add_css_class("incorrect")
            button.add_css_class("incorrect")

        self.session.setCardScore(self.session.questions[self.currentQuestion]["global_index"],
                                  self.scoreDisplayTracker[self.currentQuestion][0])

        button.get_parent().add_css_class("answered")

        self.scoreDisplayTracker[self.currentQuestion][1].set_text(
            f"Score: {self.scoreDisplayTracker[self.currentQuestion][0]}")
        self.currentQuestion += 1

        self.tryUpdateEndScreen()

    def dontKnow(self, button: Gtk.Button):
        self.scrollToCurrent()
        currentPage = self.view.get_nth_page(self.currentQuestion)
        self.scoreDisplayTracker[self.currentQuestion][0] -= 1
        self.scoreDisplayTracker[self.currentQuestion][1].add_css_class("incorrect")
        currentPage.get_last_child().get_last_child().add_css_class("answered")
        self.scoreDisplayTracker[self.currentQuestion][1].set_text(
            f"Score: {self.scoreDisplayTracker[self.currentQuestion][0]}")
        self.currentQuestion += 1

        self.tryUpdateEndScreen()

    def scrollToCurrent(self):
        self.view.scroll_to(self.view.get_nth_page(self.currentQuestion), True)

    def tryUpdateEndScreen(self):
        if self.currentQuestion == len(self.session.questions):
            self.endBox.set_description(f"You got {self.correctAnswers} out of {len(self.session.questions)} correct!")
            self.endBox.set_title("Quiz done!")
            self.endBox.set_icon_name("dialog-information-symbolic")
            self.endButton.set_label("Exit")
            self.endButton.connect("clicked", self.saveAndQuit)

    def saveAndQuit(self, button: Gtk.Button):
        self.session.saveSet()
        self.get_application().quit()


class NihongoWoBenkyoushimashouApplication(Adw.Application):
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

    app = NihongoWoBenkyoushimashouApplication(session=session,
                                               application_id="dev.iw2tryhard.nihongowobenkyoushimashou")
    app.run([])
