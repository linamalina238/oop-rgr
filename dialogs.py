import tkinter as tk
from datetime import date, datetime

from controls import ComboField, LabelField, ListField, RadioField, TextField
from model import EXPENSE, INCOME, KIND_NAMES, OTHER, Transaction, TransactionFilter
from my_dialog import MyDialog


def parse_date(text):
    return datetime.strptime(text, "%d.%m.%Y").date()


class TransactionDialog(MyDialog):
    def __init__(self, master, book):
        super().__init__(master)
        self.book = book
        self.amount = 0
        self.day = None

    def build(self):
        kind = self.add("kind", RadioField("Тип:", [(EXPENSE, KIND_NAMES[EXPENSE]),
                                                     (INCOME, KIND_NAMES[INCOME])]))
        kind.on_change = self.on_kind_change
        self.add("amount", TextField("Сума, грн:", width=12))
        self.add("category", ComboField("Категорія:", self.book.categories[EXPENSE]))
        self.add("day", TextField("Дата:", date.today().strftime("%d.%m.%Y"), width=12))
        self.add("note", TextField("Коментар:", width=30))

    def on_init(self):
        self.controls["amount"].focus()

    def on_kind_change(self, kind):
        self.controls["category"].set_values(self.book.categories[kind])

    def check(self):
        try:
            self.amount = float(self.value("amount").replace(",", "."))
        except ValueError:
            self.error("Сума має бути числом")
            return False
        if self.amount <= 0:
            self.error("Сума має бути більше нуля")
            return False
        try:
            self.day = parse_date(self.value("day"))
        except ValueError:
            self.error("Дата має бути у форматі ДД.ММ.РРРР")
            return False
        if len(self.value("note")) > 60:
            self.error("Коментар не може бути довшим за 60 символів")
            return False
        return True

    def get_result(self):
        return Transaction(self.value("kind"), round(self.amount, 2), self.value("category"),
                           self.day, self.value("note"))


class AddDialog(TransactionDialog):
    TITLE = "Нова операція"
    OK_TEXT = "Додати"


class EditDialog(TransactionDialog):
    TITLE = "Редагування операції"
    OK_TEXT = "Зберегти"

    def __init__(self, master, book, transaction):
        super().__init__(master, book)
        self.transaction = transaction
        self.deleted = False

    def build(self):
        self.add("number", LabelField("Запис:", f"№ {self.transaction.id}"))
        super().build()

    def build_buttons(self, frame):
        super().build_buttons(frame)
        self.add_button(frame, "Видалити", self.on_delete)

    def on_init(self):
        t = self.transaction
        self.set_value("kind", t.kind)
        self.on_kind_change(t.kind)
        self.set_value("amount", f"{t.amount:g}")
        self.set_value("category", t.category)
        self.set_value("day", t.day.strftime("%d.%m.%Y"))
        self.set_value("note", t.note)
        self.controls["amount"].focus()

    def on_delete(self):
        if self.ask(f"Видалити запис № {self.transaction.id}?"):
            self.deleted = True
            self.close(None)


class CategoriesDialog(MyDialog):
    TITLE = "Категорії"

    def __init__(self, master, book):
        super().__init__(master)
        self.book = book

    def build(self):
        kind = self.add("kind", RadioField("Тип:", [(EXPENSE, "Витрати"), (INCOME, "Доходи")]))
        kind.on_change = lambda k: self.fill()
        names = self.add("list", ListField("Категорії:", self.book.categories[EXPENSE], height=9))
        names.on_change = self.on_select
        self.add("name", TextField("Назва:"))

        frame = tk.Frame(self.body)
        frame.grid(row=self.row, column=1, sticky="w", pady=(4, 0))
        self.add_button(frame, "Додати", self.on_add)
        self.add_button(frame, "Змінити", self.on_rename)
        self.add_button(frame, "Видалити", self.on_delete)

    def build_buttons(self, frame):
        self.add_button(frame, "Закрити", self.on_cancel)

    def on_init(self):
        self.controls["name"].focus()

    def on_ok(self):
        self.on_add()

    def fill(self, select=None):
        self.controls["list"].set_items(self.book.categories[self.value("kind")])
        self.controls["list"].set(select)
        self.set_value("name", "")

    def on_select(self, name):
        if name:
            self.set_value("name", name)

    def new_name(self):
        name = self.value("name")
        if not name:
            self.error("Введіть назву категорії")
            return None
        if name in self.book.categories[self.value("kind")]:
            self.error(f"Категорія «{name}» вже існує")
            return None
        return name

    def selected(self):
        old = self.value("list")
        if old is None:
            self.error("Виберіть категорію у списку")
            return None
        if old == OTHER:
            self.error(f"Категорію «{OTHER}» не можна змінювати")
            return None
        return old

    def on_add(self):
        name = self.new_name()
        if name:
            self.book.add_category(self.value("kind"), name)
            self.fill(name)

    def on_rename(self):
        old = self.selected()
        if old is None:
            return
        name = self.new_name()
        if name:
            self.book.rename_category(self.value("kind"), old, name)
            self.fill(name)

    def on_delete(self):
        old = self.selected()
        if old is None:
            return
        kind = self.value("kind")
        text = f"Видалити категорію «{old}»?"
        n = self.book.count(kind, old)
        if n:
            text += f"\nОперацій з цією категорією: {n}, вони перейдуть в «{OTHER}»"
        if self.ask(text):
            self.book.remove_category(kind, old)
            self.fill()


class FilterDialog(MyDialog):
    TITLE = "Фільтр"
    ALL = "Усі"
    KINDS = {KIND_NAMES[INCOME]: INCOME, KIND_NAMES[EXPENSE]: EXPENSE}

    def __init__(self, master, book, current):
        super().__init__(master)
        self.book = book
        self.current = current
        self.start = None
        self.end = None

    def build(self):
        kind = self.add("kind", ComboField("Тип:", [self.ALL] + list(self.KINDS)))
        kind.on_change = self.on_kind_change
        self.add("category", ComboField("Категорія:", [self.ALL]))
        self.add("start", TextField("Дата з:", width=12))
        self.add("end", TextField("Дата по:", width=12))
        self.add("hint", LabelField("", "Порожня дата - без обмеження"))

    def build_buttons(self, frame):
        super().build_buttons(frame)
        self.add_button(frame, "Скинути", self.on_reset)

    def on_init(self):
        self.on_kind_change(self.ALL)
        f = self.current
        if f is None:
            return
        if f.kind:
            self.set_value("kind", KIND_NAMES[f.kind])
            self.on_kind_change(KIND_NAMES[f.kind])
        if f.category:
            self.set_value("category", f.category)
        if f.start:
            self.set_value("start", f.start.strftime("%d.%m.%Y"))
        if f.end:
            self.set_value("end", f.end.strftime("%d.%m.%Y"))

    def on_kind_change(self, kind_name):
        if kind_name in self.KINDS:
            names = self.book.categories[self.KINDS[kind_name]]
        else:
            names = []
            for name in self.book.categories[INCOME] + self.book.categories[EXPENSE]:
                if name not in names:
                    names.append(name)
        self.controls["category"].set_values([self.ALL] + names)

    def check(self):
        try:
            self.start = parse_date(self.value("start")) if self.value("start") else None
            self.end = parse_date(self.value("end")) if self.value("end") else None
        except ValueError:
            self.error("Дата має бути у форматі ДД.ММ.РРРР")
            return False
        if self.start and self.end and self.start > self.end:
            self.error("Початкова дата більша за кінцеву")
            return False
        return True

    def get_result(self):
        kind = self.KINDS.get(self.value("kind"))
        category = self.value("category")
        if category == self.ALL:
            category = None
        return TransactionFilter(kind, category, self.start, self.end)

    def on_reset(self):
        self.close(TransactionFilter())


class StatsDialog(MyDialog):
    TITLE = "Статистика"
    COLORS = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc948", "#b07aa1", "#9c755f"]

    def __init__(self, master, book):
        super().__init__(master)
        self.book = book
        self.months = book.months()
        if not self.months:
            self.months = [(date.today().year, date.today().month)]
        self.canvas = None

    def build(self):
        names = [f"{m:02}.{y}" for y, m in self.months]
        month = self.add("month", ComboField("Місяць:", names, width=10))
        month.on_change = lambda v: self.draw()
        kind = self.add("kind", RadioField("Діаграма:", [(EXPENSE, "Витрати"), (INCOME, "Доходи")]))
        kind.on_change = lambda v: self.draw()
        self.add("income", LabelField("Доходи:"))
        self.add("expense", LabelField("Витрати:"))
        self.add("balance", LabelField("Різниця:"))

        self.canvas = tk.Canvas(self.body, width=440, height=200, bg="white")
        self.canvas.grid(row=self.row, column=0, columnspan=2, pady=(8, 0))

    def build_buttons(self, frame):
        self.add_button(frame, "Закрити", self.on_cancel)

    def on_init(self):
        self.draw()

    def on_ok(self):
        self.on_cancel()

    def draw(self):
        index = self.controls["month"].values.index(self.value("month"))
        year, month = self.months[index]
        income = sum(self.book.by_category(INCOME, year, month).values())
        expense = sum(self.book.by_category(EXPENSE, year, month).values())
        self.set_value("income", f"{income:.2f} грн")
        self.set_value("expense", f"{expense:.2f} грн")
        self.set_value("balance", f"{income - expense:.2f} грн")

        c = self.canvas
        c.delete("all")
        data = self.book.by_category(self.value("kind"), year, month)
        if not data:
            c.config(height=60)
            c.create_text(220, 30, text="Немає даних за цей місяць", fill="gray")
            return

        total = sum(data.values())
        top = max(data.values())
        c.config(height=len(data) * 28 + 16)
        y = 10
        for i, (name, value) in enumerate(data.items()):
            w = int(200 * value / top)
            c.create_text(10, y + 9, text=name, anchor="w")
            c.create_rectangle(110, y, 110 + w, y + 18, fill=self.COLORS[i % len(self.COLORS)], outline="")
            c.create_text(116 + w, y + 9, text=f"{value:.2f} ({value / total * 100:.0f}%)", anchor="w")
            y += 28


class BudgetDialog(MyDialog):
    TITLE = "Бюджет"

    def __init__(self, master, book):
        super().__init__(master)
        self.book = book
        self.year = date.today().year
        self.month = date.today().month

    def build(self):
        category = self.add("category", ComboField("Категорія:", self.book.categories[EXPENSE]))
        category.on_change = self.on_category
        self.add("limit", TextField("Ліміт на місяць:", width=12))

        frame = tk.Frame(self.body)
        frame.grid(row=self.row, column=1, sticky="w", pady=(0, 6))
        self.add_button(frame, "Встановити", self.on_set)
        self.row += 1

        state = self.add("list", ListField(f"Стан за {self.month:02}.{self.year}:", height=8, width=40))
        state.on_change = self.on_list_select
        self.add("hint", LabelField("", "Порожній ліміт або 0 - прибрати ліміт"))

    def build_buttons(self, frame):
        self.add_button(frame, "Закрити", self.on_cancel)

    def on_init(self):
        self.on_category(self.value("category"))
        self.fill()
        self.controls["limit"].focus()

    def on_ok(self):
        self.on_set()

    def fill(self):
        lines = []
        for name in self.book.categories[EXPENSE]:
            if name in self.book.budget:
                limit = self.book.budget[name]
                spent = self.book.spent(name, self.year, self.month)
                line = f"{name}: {spent:.2f} з {limit:.2f}"
                if spent > limit:
                    line += "  - ПЕРЕВИЩЕНО"
                lines.append(line)
        if not lines:
            lines.append("Ліміти ще не встановлені")
        self.controls["list"].set_items(lines)

    def on_category(self, name):
        limit = self.book.budget.get(name)
        self.set_value("limit", f"{limit:g}" if limit else "")

    def on_list_select(self, line):
        if line is None:
            return
        name = line.split(":")[0]
        if name in self.book.categories[EXPENSE]:
            self.set_value("category", name)
            self.on_category(name)

    def on_set(self):
        text = self.value("limit").replace(",", ".")
        try:
            limit = float(text) if text else 0
        except ValueError:
            self.error("Ліміт має бути числом")
            return
        if limit < 0:
            self.error("Ліміт не може бути від'ємним")
            return
        self.book.set_limit(self.value("category"), round(limit, 2))
        self.fill()


class AboutDialog(MyDialog):
    TITLE = "Про програму"

    def build(self):
        self.add("text", LabelField("", "Облік особистих фінансів\n\n"
                                        "Розрахунково-графічна робота з ООП\n"
                                        "Варіант 12. Бібліотека модальних діалогів MyDialog\n\n"
                                        "Python, tkinter"))

    def build_buttons(self, frame):
        self.add_button(frame, "Закрити", self.on_cancel)
