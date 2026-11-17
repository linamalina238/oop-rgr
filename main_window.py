import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from dialogs import (AboutDialog, AddDialog, BudgetDialog, CategoriesDialog, EditDialog,
                     FilterDialog, StatsDialog)
from model import EXPENSE, INCOME, KIND_NAMES, FinanceBook

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")


class MainWindow:
    COLUMNS = ("№", "Дата", "Тип", "Категорія", "Сума", "Коментар")
    WIDTHS = (40, 90, 80, 120, 90, 230)

    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("720x450+80+60")
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

        self.path = DATA_FILE
        self.filter = None
        self.book = FinanceBook()
        if os.path.exists(self.path):
            try:
                self.book = FinanceBook.load(self.path)
            except (OSError, ValueError, KeyError):
                messagebox.showerror("Помилка", "Не вдалося прочитати data.json")

        self._build_menu()
        self._build_table()
        self._build_status()
        self.root.bind("<Control-n>", lambda e: self.on_add())
        self.root.bind("<Control-s>", lambda e: self.on_save())
        self.refresh()

    def run(self):
        self.root.mainloop()

    def _build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Відкрити...", command=self.on_open)
        file_menu.add_command(label="Зберегти", command=self.on_save)
        file_menu.add_command(label="Зберегти як...", command=self.on_save_as)
        file_menu.add_command(label="Експорт у CSV...", command=self.on_export)
        file_menu.add_separator()
        file_menu.add_command(label="Вихід", command=self.on_exit)
        menubar.add_cascade(label="Файл", menu=file_menu)

        window_menu = tk.Menu(menubar, tearoff=0)
        window_menu.add_command(label="Нова операція...", command=self.on_add)
        window_menu.add_command(label="Редагувати операцію...", command=self.on_edit)
        window_menu.add_command(label="Категорії...", command=self.on_categories)
        window_menu.add_command(label="Фільтр...", command=self.on_filter)
        window_menu.add_command(label="Статистика...", command=self.on_stats)
        window_menu.add_command(label="Бюджет...", command=self.on_budget)
        window_menu.add_separator()
        window_menu.add_command(label="Про програму...", command=self.on_about)
        menubar.add_cascade(label="Вікно", menu=window_menu)

        self.root.config(menu=menubar)

    def _build_table(self):
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tree = ttk.Treeview(frame, columns=self.COLUMNS, show="headings", selectmode="browse")
        for name, width in zip(self.COLUMNS, self.WIDTHS):
            self.tree.heading(name, text=name)
            self.tree.column(name, width=width, anchor=tk.CENTER)
        self.tree.column("Коментар", anchor=tk.W)
        self.tree.tag_configure(INCOME, foreground="darkgreen")
        self.tree.tag_configure(EXPENSE, foreground="firebrick")

        scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<Double-1>", lambda e: self.on_edit())
        self.tree.bind("<Delete>", lambda e: self.on_delete())

    def _build_status(self):
        self.filter_label = tk.Label(self.root, anchor="w", fg="gray30", padx=8)
        self.filter_label.pack(fill=tk.X)
        self.status = tk.Label(self.root, anchor="w", font=("Arial", 10, "bold"), padx=8, pady=4)
        self.status.pack(fill=tk.X)

    def shown(self):
        items = []
        for t in self.book.sorted_list():
            if self.filter is None or self.filter.match(t):
                items.append(t)
        return items

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        income = 0
        expense = 0
        for t in self.shown():
            self.tree.insert("", tk.END, iid=str(t.id), tags=(t.kind,), values=(
                t.id, t.day.strftime("%d.%m.%Y"), KIND_NAMES[t.kind],
                t.category, f"{t.signed():.2f}", t.note,
            ))
            if t.kind == INCOME:
                income += t.amount
            else:
                expense += t.amount
        self.status.config(text=f"Доходи: {income:.2f}    Витрати: {expense:.2f}    "
                                f"Баланс: {income - expense:.2f} грн")
        if self.filter:
            self.filter_label.config(text="Фільтр: " + self.filter.text())
        else:
            self.filter_label.config(text="Показано всі операції")
        mark = "*" if self.book.changed else ""
        self.root.title(f"Облік фінансів - {os.path.basename(self.path)}{mark}")

    def selected(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self.book.find(int(sel[0]))

    def check_budget(self, t):
        if t.kind != EXPENSE or t.category not in self.book.budget:
            return
        limit = self.book.budget[t.category]
        spent = self.book.spent(t.category, t.day.year, t.day.month)
        if spent > limit:
            messagebox.showwarning("Бюджет", f"Перевищено ліміт на «{t.category}»\n"
                                             f"Витрачено {spent:.2f} з {limit:.2f} грн")

    def on_add(self):
        t = AddDialog(self.root, self.book).show_modal()
        if t:
            self.book.add(t)
            self.refresh()
            self.check_budget(t)

    def on_edit(self):
        t = self.selected()
        if t is None:
            messagebox.showinfo("Редагування", "Спочатку виберіть запис у таблиці")
            return
        dialog = EditDialog(self.root, self.book, t)
        new = dialog.show_modal()
        if dialog.deleted:
            self.book.remove(t)
            self.refresh()
        elif new:
            self.book.update(t, new)
            self.refresh()
            self.check_budget(t)

    def on_delete(self):
        t = self.selected()
        if t and messagebox.askyesno("Видалення", f"Видалити запис № {t.id}?"):
            self.book.remove(t)
            self.refresh()

    def on_categories(self):
        CategoriesDialog(self.root, self.book).show_modal()
        self.refresh()

    def on_filter(self):
        f = FilterDialog(self.root, self.book, self.filter).show_modal()
        if f is None:
            return
        if f.text():
            self.filter = f
        else:
            self.filter = None
        self.refresh()

    def on_stats(self):
        StatsDialog(self.root, self.book).show_modal()

    def on_budget(self):
        BudgetDialog(self.root, self.book).show_modal()
        self.refresh()

    def on_about(self):
        AboutDialog(self.root).show_modal()

    def on_export(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv")], initialdir=BASE_DIR)
        if not path:
            return
        try:
            self.book.export_csv(path, self.shown())
        except OSError as e:
            messagebox.showerror("Помилка", f"Не вдалося записати файл:\n{e}")
            return
        messagebox.showinfo("Експорт", f"Збережено записів: {len(self.shown())}")

    def on_open(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")], initialdir=BASE_DIR)
        if not path:
            return
        try:
            self.book = FinanceBook.load(path)
        except (OSError, ValueError, KeyError):
            messagebox.showerror("Помилка", "Файл пошкоджений або має невірний формат")
            return
        self.path = path
        self.filter = None
        self.refresh()

    def on_save(self):
        try:
            self.book.save(self.path)
        except OSError as e:
            messagebox.showerror("Помилка", f"Не вдалося записати файл:\n{e}")
            return
        self.refresh()

    def on_save_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("JSON", "*.json")], initialdir=BASE_DIR)
        if path:
            self.path = path
            self.on_save()

    def on_exit(self):
        if self.book.changed and messagebox.askyesno("Вихід", "Зберегти зміни?"):
            self.on_save()
        self.root.destroy()
