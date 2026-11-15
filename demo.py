import tkinter as tk
from datetime import datetime

from controls import CheckField, ComboField, LabelField, ListField, RadioField, TextField
from my_dialog import MyDialog


class TestDialog(MyDialog):
    TITLE = "Тестовий діалог"

    def build(self):
        self.add("kind", RadioField("Тип:", [("expense", "Витрата"), ("income", "Дохід")]))
        self.add("amount", TextField("Сума:", width=12))
        self.add("category", ComboField("Категорія:", ["Продукти", "Транспорт", "Кафе", "Інше"]))
        self.add("day", TextField("Дата:", datetime.now().strftime("%d.%m.%Y"), width=12))
        self.add("items", ListField("Список:", ["Перший", "Другий", "Третій", "Четвертий"], height=4))
        self.add("flag", CheckField("Запам'ятати вибір"))

    def on_init(self):
        self.controls["amount"].focus()

    def check(self):
        try:
            amount = float(self.value("amount").replace(",", "."))
        except ValueError:
            self.error("Сума має бути числом")
            return False
        if amount <= 0:
            self.error("Сума має бути більше нуля")
            return False
        try:
            datetime.strptime(self.value("day"), "%d.%m.%Y")
        except ValueError:
            self.error("Дата має бути у форматі ДД.ММ.РРРР")
            return False
        return True


class NameDialog(MyDialog):
    TITLE = "Введення імені"

    def build(self):
        self.add("name", TextField("Ім'я:"))

    def check(self):
        if not self.value("name"):
            self.error("Ім'я не може бути порожнім")
            return False
        return True


class AboutDialog(MyDialog):
    TITLE = "Про програму"

    def build(self):
        self.add("text", LabelField("", "Бібліотека модальних діалогів MyDialog\n"
                                        "Розрахунково-графічна робота з ООП\nВаріант 12"))

    def build_buttons(self, frame):
        self.add_button(frame, "Закрити", self.on_cancel)


class DemoApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MyDialog - перевірка")
        self.root.geometry("480x300+100+100")

        menubar = tk.Menu(self.root)
        window_menu = tk.Menu(menubar, tearoff=0)
        window_menu.add_command(label="Тестовий діалог...", command=self.on_test)
        window_menu.add_command(label="Введення імені...", command=self.on_name)
        window_menu.add_command(label="Про програму...", command=self.on_about)
        window_menu.add_separator()
        window_menu.add_command(label="Вихід", command=self.root.destroy)
        menubar.add_cascade(label="Вікно", menu=window_menu)
        self.root.config(menu=menubar)

        self.output = tk.Label(self.root, text="Оберіть діалог у меню «Вікно»",
                               anchor="nw", justify=tk.LEFT, padx=10, pady=10)
        self.output.pack(fill=tk.BOTH, expand=True)

    def show_result(self, result):
        if result is None:
            self.output.config(text="Діалог закрито без збереження")
            return
        text = ""
        for key, value in result.items():
            text += f"{key}: {value}\n"
        self.output.config(text=text)

    def on_test(self):
        self.show_result(TestDialog(self.root).show_modal())

    def on_name(self):
        self.show_result(NameDialog(self.root).show_modal())

    def on_about(self):
        AboutDialog(self.root).show_modal()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    DemoApp().run()
