import tkinter as tk
from abc import ABC, abstractmethod
from tkinter import ttk


class Control(ABC):
    def __init__(self, label):
        self.label = label
        self.widget = None

    def place(self, parent, row):
        tk.Label(parent, text=self.label, anchor="w").grid(row=row, column=0, sticky="nw", pady=3)
        self.widget = self.create(parent)
        self.widget.grid(row=row, column=1, sticky="w", padx=(8, 0), pady=3)

    @abstractmethod
    def create(self, parent):
        raise NotImplementedError

    @abstractmethod
    def get(self):
        raise NotImplementedError

    @abstractmethod
    def set(self, value):
        raise NotImplementedError

    def focus(self):
        self.widget.focus_set()


class TextField(Control):
    def __init__(self, label, value="", width=25):
        super().__init__(label)
        self.width = width
        self.var = tk.StringVar(value=value)

    def create(self, parent):
        return tk.Entry(parent, textvariable=self.var, width=self.width)

    def get(self):
        return self.var.get().strip()

    def set(self, value):
        self.var.set(value)


class ComboField(Control):
    def __init__(self, label, values, width=23):
        super().__init__(label)
        self.values = list(values)
        self.width = width
        self.var = tk.StringVar(value=self.values[0] if self.values else "")
        self.on_change = None

    def create(self, parent):
        combo = ttk.Combobox(parent, textvariable=self.var, values=self.values,
                             width=self.width, state="readonly")
        combo.bind("<<ComboboxSelected>>", self._on_select)
        return combo

    def _on_select(self, event):
        if self.on_change:
            self.on_change(self.get())

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)

    def set_values(self, values):
        self.values = list(values)
        self.widget.config(values=self.values)
        if self.get() not in self.values:
            self.set(self.values[0] if self.values else "")


class CheckField(Control):
    def __init__(self, label, value=False):
        super().__init__(label)
        self.var = tk.BooleanVar(value=value)

    def place(self, parent, row):
        self.widget = self.create(parent)
        self.widget.grid(row=row, column=0, columnspan=2, sticky="w", pady=3)

    def create(self, parent):
        return tk.Checkbutton(parent, text=self.label, variable=self.var)

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)


class RadioField(Control):
    def __init__(self, label, options):
        super().__init__(label)
        self.options = options
        self.var = tk.StringVar(value=options[0][0])
        self.on_change = None

    def create(self, parent):
        frame = tk.Frame(parent)
        for key, text in self.options:
            tk.Radiobutton(frame, text=text, variable=self.var, value=key,
                           command=self._on_click).pack(side=tk.LEFT, padx=(0, 10))
        return frame

    def _on_click(self):
        if self.on_change:
            self.on_change(self.get())

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)


class ListField(Control):
    def __init__(self, label, items=(), height=8, width=25):
        super().__init__(label)
        self.items = list(items)
        self.height = height
        self.width = width
        self.listbox = None
        self.on_change = None

    def create(self, parent):
        frame = tk.Frame(parent)
        self.listbox = tk.Listbox(frame, height=self.height, width=self.width, exportselection=False)
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        scroll = tk.Scrollbar(frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scroll.set)
        self.listbox.pack(side=tk.LEFT)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.set_items(self.items)
        return frame

    def _on_select(self, event):
        if self.on_change:
            self.on_change(self.get())

    def set_items(self, items):
        self.items = list(items)
        self.listbox.delete(0, tk.END)
        for item in self.items:
            self.listbox.insert(tk.END, item)

    def get(self):
        sel = self.listbox.curselection()
        if not sel:
            return None
        return self.items[sel[0]]

    def set(self, value):
        self.listbox.selection_clear(0, tk.END)
        if value in self.items:
            i = self.items.index(value)
            self.listbox.selection_set(i)
            self.listbox.see(i)

    def focus(self):
        self.listbox.focus_set()


class LabelField(Control):
    def __init__(self, label, text=""):
        super().__init__(label)
        self.var = tk.StringVar(value=text)

    def create(self, parent):
        return tk.Label(parent, textvariable=self.var, anchor="w", justify=tk.LEFT)

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)
