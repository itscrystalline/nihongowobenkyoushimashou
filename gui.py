import tkinter as tk
import time

class App(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        root.title("日本語を勉強しましょう")
        root.wm_resizable(True, True)
        self.canva = tk.Canvas(width=500,height=500,background="#123456")
        self.startButton = tk.Button(text="Start",command=self.startQuiz,anchor="center",compound="center",height=10,width=20,background="#123456")
        self.canva.pack()
        self.startButton.place(x=0,y=0)
        self.pack()


        self.entrythingy = tk.Entry()
        self.entrythingy.pack()

        # Create the application variable.
        self.contents = tk.StringVar()
        # Set it to some value.
        self.contents.set("this is a variable")
        # Tell the entry widget to watch this variable.
        self.entrythingy["textvariable"] = self.contents

        # Define a callback for when the user hits return.
        # It prints the current value of the variable.
        self.entrythingy.bind('<Key-Return>',
                             self.print_contents)

    def print_contents(self, event):
        print("Hi. The current entry content is:",
              self.contents.get())

    def startQuiz(self):
        self.startButton.destroy()

root = tk.Tk()
myapp = App(root)
myapp.mainloop()
