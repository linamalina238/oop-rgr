import os
import tempfile
import unittest
from datetime import date

from model import EXPENSE, INCOME, OTHER, FinanceBook, Transaction, TransactionFilter


class TestFinanceBook(unittest.TestCase):
    def setUp(self):
        self.book = FinanceBook()
        self.book.add(Transaction(INCOME, 5000, "Стипендія", date(2026, 11, 1)))
        self.book.add(Transaction(EXPENSE, 300, "Продукти", date(2026, 11, 2)))
        self.book.add(Transaction(EXPENSE, 150, "Кафе", date(2026, 11, 5)))
        self.book.add(Transaction(EXPENSE, 200, "Продукти", date(2026, 10, 20)))

    def test_add(self):
        self.assertEqual(len(self.book.transactions), 4)
        self.assertEqual(self.book.transactions[3].id, 4)

    def test_balance(self):
        self.assertEqual(self.book.total(INCOME), 5000)
        self.assertEqual(self.book.total(EXPENSE), 650)
        self.assertEqual(self.book.balance(), 4350)

    def test_by_category(self):
        self.assertEqual(self.book.by_category(EXPENSE, 2026, 11), {"Продукти": 300, "Кафе": 150})
        self.assertEqual(self.book.spent("Продукти", 2026, 10), 200)

    def test_update_remove(self):
        t = self.book.find(3)
        self.book.update(t, Transaction(EXPENSE, 99, "Кафе", date(2026, 11, 5)))
        self.assertEqual(self.book.find(3).amount, 99)
        self.book.remove(t)
        self.assertIsNone(self.book.find(3))

    def test_categories(self):
        self.book.add_category(EXPENSE, "Книги")
        self.assertEqual(self.book.categories[EXPENSE][-2:], ["Книги", OTHER])
        self.book.rename_category(EXPENSE, "Продукти", "Їжа")
        self.assertEqual(self.book.find(2).category, "Їжа")
        self.book.remove_category(EXPENSE, "Їжа")
        self.assertEqual(self.book.find(4).category, OTHER)

    def test_save_load(self):
        self.book.budget["Кафе"] = 500
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "data.json")
            self.book.save(path)
            loaded = FinanceBook.load(path)
        self.assertEqual(len(loaded.transactions), 4)
        self.assertEqual(loaded.find(2).day, date(2026, 11, 2))
        self.assertEqual(loaded.budget, {"Кафе": 500})
        self.assertEqual(loaded.next_id, 5)

    def test_months(self):
        self.assertEqual(self.book.months(), [(2026, 11), (2026, 10)])

    def test_filter(self):
        f = TransactionFilter(EXPENSE, "Продукти")
        found = [t.id for t in self.book.transactions if f.match(t)]
        self.assertEqual(found, [2, 4])
        f = TransactionFilter(start=date(2026, 11, 2), end=date(2026, 11, 4))
        found = [t.id for t in self.book.transactions if f.match(t)]
        self.assertEqual(found, [2])
        self.assertEqual(TransactionFilter().text(), "")

    def test_budget(self):
        self.book.set_limit("Продукти", 250)
        self.assertTrue(self.book.spent("Продукти", 2026, 11) > self.book.budget["Продукти"])
        self.book.set_limit("Продукти", 0)
        self.assertEqual(self.book.budget, {})

    def test_export(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "out.csv")
            self.book.export_csv(path, self.book.sorted_list())
            with open(path, encoding="utf-8") as f:
                lines = f.read().splitlines()
        self.assertEqual(len(lines), 5)
        self.assertEqual(lines[1], "3;05.11.2026;Витрата;Кафе;-150,00;")


if __name__ == "__main__":
    unittest.main()
