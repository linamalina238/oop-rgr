import json
from datetime import date

INCOME = "income"
EXPENSE = "expense"
KIND_NAMES = {INCOME: "Дохід", EXPENSE: "Витрата"}
OTHER = "Інше"


def by_day(t):
    return t.day


class Transaction:
    def __init__(self, kind, amount, category, day, note=""):
        self.id = 0
        self.kind = kind
        self.amount = amount
        self.category = category
        self.day = day
        self.note = note

    def signed(self):
        if self.kind == INCOME:
            return self.amount
        return -self.amount

    def to_dict(self):
        return {
            "id": self.id,
            "kind": self.kind,
            "amount": self.amount,
            "category": self.category,
            "day": self.day.isoformat(),
            "note": self.note,
        }

    @staticmethod
    def from_dict(data):
        t = Transaction(data["kind"], data["amount"], data["category"],
                        date.fromisoformat(data["day"]), data["note"])
        t.id = data["id"]
        return t


class TransactionFilter:
    def __init__(self, kind=None, category=None, start=None, end=None):
        self.kind = kind
        self.category = category
        self.start = start
        self.end = end

    def match(self, t):
        if self.kind and t.kind != self.kind:
            return False
        if self.category and t.category != self.category:
            return False
        if self.start and t.day < self.start:
            return False
        if self.end and t.day > self.end:
            return False
        return True

    def text(self):
        parts = []
        if self.kind:
            parts.append(KIND_NAMES[self.kind])
        if self.category:
            parts.append(self.category)
        if self.start:
            parts.append("з " + self.start.strftime("%d.%m.%Y"))
        if self.end:
            parts.append("по " + self.end.strftime("%d.%m.%Y"))
        return ", ".join(parts)


class FinanceBook:
    def __init__(self):
        self.transactions = []
        self.categories = {
            INCOME: ["Зарплата", "Стипендія", "Подарунки", OTHER],
            EXPENSE: ["Продукти", "Транспорт", "Кафе", "Житло", "Зв'язок", "Розваги", OTHER],
        }
        self.budget = {}
        self.next_id = 1
        self.changed = False

    def add(self, t):
        t.id = self.next_id
        self.next_id += 1
        self.transactions.append(t)
        self.changed = True

    def find(self, tid):
        for t in self.transactions:
            if t.id == tid:
                return t
        return None

    def update(self, old, new):
        old.kind = new.kind
        old.amount = new.amount
        old.category = new.category
        old.day = new.day
        old.note = new.note
        self.changed = True

    def remove(self, t):
        self.transactions.remove(t)
        self.changed = True

    def sorted_list(self):
        return sorted(self.transactions, key=by_day, reverse=True)

    def total(self, kind):
        s = 0
        for t in self.transactions:
            if t.kind == kind:
                s += t.amount
        return s

    def balance(self):
        return self.total(INCOME) - self.total(EXPENSE)

    def by_category(self, kind, year, month):
        result = {}
        for t in self.transactions:
            if t.kind == kind and t.day.year == year and t.day.month == month:
                result[t.category] = result.get(t.category, 0) + t.amount
        return result

    def spent(self, category, year, month):
        return self.by_category(EXPENSE, year, month).get(category, 0)

    def add_category(self, kind, name):
        self.categories[kind].insert(-1, name)
        self.changed = True

    def rename_category(self, kind, old, new):
        names = self.categories[kind]
        names[names.index(old)] = new
        for t in self.transactions:
            if t.kind == kind and t.category == old:
                t.category = new
        if old in self.budget:
            self.budget[new] = self.budget.pop(old)
        self.changed = True

    def remove_category(self, kind, name):
        self.categories[kind].remove(name)
        for t in self.transactions:
            if t.kind == kind and t.category == name:
                t.category = OTHER
        self.budget.pop(name, None)
        self.changed = True

    def set_limit(self, category, limit):
        if limit > 0:
            self.budget[category] = limit
        else:
            self.budget.pop(category, None)
        self.changed = True

    def count(self, kind, category):
        n = 0
        for t in self.transactions:
            if t.kind == kind and t.category == category:
                n += 1
        return n

    def months(self):
        result = []
        for t in self.sorted_list():
            m = (t.day.year, t.day.month)
            if m not in result:
                result.append(m)
        return result

    def export_csv(self, path, items):
        with open(path, "w", encoding="utf-8") as f:
            f.write("№;Дата;Тип;Категорія;Сума;Коментар\n")
            for t in items:
                amount = f"{t.signed():.2f}".replace(".", ",")
                f.write(f"{t.id};{t.day.strftime('%d.%m.%Y')};{KIND_NAMES[t.kind]};"
                        f"{t.category};{amount};{t.note}\n")

    def save(self, path):
        data = {
            "next_id": self.next_id,
            "categories": self.categories,
            "budget": self.budget,
            "transactions": [t.to_dict() for t in self.transactions],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.changed = False

    @staticmethod
    def load(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        book = FinanceBook()
        book.next_id = data["next_id"]
        book.categories = data["categories"]
        book.budget = data["budget"]
        book.transactions = [Transaction.from_dict(item) for item in data["transactions"]]
        return book
