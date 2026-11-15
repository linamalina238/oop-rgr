import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import messagebox


class MyDialog(ABC):
    TITLE = "Діалог"
    OK_TEXT = "Так"
    CANCEL_TEXT = "Відміна"

    def __init__(self, master):
        self.master = master
        self.window = None
        self.body = None
        self.result = None
        self.controls = {}
        self.row = 0

    def show_modal(self):
        self.window = tk.Toplevel(self.master)
        self.window.title(self.TITLE)
        self.window.resizable(False, False)
        self.window.transient(self.master)
        self.window.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.window.bind("<Return>", lambda e: self.on_ok())
        self.window.bind("<Escape>", lambda e: self.on_cancel())

        self.body = tk.Frame(self.window, padx=12, pady=10)
        self.body.pack()
        self.build()

        buttons = tk.Frame(self.window, pady=8)
        buttons.pack()
        self.build_buttons(buttons)
        self.on_init()

        self.center()
        self.window.wait_visibility()
        self.window.grab_set()
        self.master.wait_window(self.window)

        if isinstance(self.master, tk.Toplevel):
            self.master.grab_set()
        return self.result

    def center(self):
        self.window.update_idletasks()
        w = self.window.winfo_width()
        h = self.window.winfo_height()
        x = self.master.winfo_rootx() + (self.master.winfo_width() - w) // 2
        y = self.master.winfo_rooty() + (self.master.winfo_height() - h) // 2
        self.window.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    @abstractmethod
    def build(self):
        raise NotImplementedError

    def build_buttons(self, frame):
        self.add_button(frame, self.OK_TEXT, self.on_ok)
        self.add_button(frame, self.CANCEL_TEXT, self.on_cancel)

    def add_button(self, frame, text, command):
        btn = tk.Button(frame, text=text, width=10, command=command)
        btn.pack(side=tk.LEFT, padx=5)
        return btn

    def on_init(self):
        pass

    def add(self, name, control):
        control.place(self.body, self.row)
        self.controls[name] = control
        self.row += 1
        return control

    def value(self, name):
        return self.controls[name].get()

    def set_value(self, name, value):
        self.controls[name].set(value)

    def check(self):
        return True

    def get_result(self):
        return {name: control.get() for name, control in self.controls.items()}

    def on_ok(self):
        if self.check():
            self.close(self.get_result())

    def on_cancel(self):
        self.close(None)

    def close(self, result):
        self.result = result
        self.window.grab_release()
        self.window.destroy()

    def error(self, text):
        messagebox.showerror("Помилка", text, parent=self.window)

    def ask(self, text):
        return messagebox.askyesno("Підтвердження", text, parent=self.window)
