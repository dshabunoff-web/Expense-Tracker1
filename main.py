import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date, datetime
import json
import os

# ---------- Модели данных ---------- #

class Expense:
    def __init__(self, amount: float, category: str, date_str: str, note: str = ""):
        self.amount = float(amount)
        self.category = category
        self.date = date.fromisoformat(date_str)  # формат YYYY-MM-DD
        self.note = note

    def to_dict(self):
        return {
            "amount": self.amount,
            "category": self.category,
            "date": self.date.isoformat(),
            "note": self.note
        }

    @staticmethod
    def from_dict(d):
        return Expense(d["amount"], d["category"], d["date"], d.get("note", ""))

# ---------- Приложение ---------- #

class ExpenseTrackerApp:
    HISTORY_FILE = "expense_history.json"

    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("900x650")

        self.expenses = []          # полный список расходов
        self.filtered_expenses = []   # после фильтрации

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        # Панель добавления расхода
        add_frame = ttk.Frame(self.root, padding=10)
        add_frame.pack(fill="x")

        ttk.Label(add_frame, text="Категория:").grid(row=0, column=0, sticky="e")
        self.category_var = tk.StringVar(value="Продукты")
        self.category_cb = ttk.Combobox(add_frame, textvariable=self.category_var, state="readonly")
        self.category_cb['values'] = ["Продукты", "Транспорт", "Развлечения", "Жилье", "Здоровье", "Другое"]
        self.category_cb.grid(row=0, column=1, padx=6)
        self.category_cb.current(0)

        ttk.Label(add_frame, text="Сумма:").grid(row=0, column=2, sticky="e")
        self.amount_var = tk.StringVar(value="100")
        ttk.Entry(add_frame, textvariable=self.amount_var, width=12).grid(row=0, column=3, padx=6)

        ttk.Label(add_frame, text="Дата (YYYY-MM-DD):").grid(row=0, column=4, sticky="e")
        self.date_var = tk.StringVar(value=date.today().isoformat())
        ttk.Entry(add_frame, textvariable=self.date_var, width=12).grid(row=0, column=5, padx=6)

        ttk.Label(add_frame, text="Заметка:").grid(row=0, column=6, sticky="e")
        self.note_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.note_var, width=25).grid(row=0, column=7, padx=6)

        ttk.Button(add_frame, text="Добавить", command=self.add_expense).grid(row=0, column=8, padx=6)

        # Панель фильтров и статистики
        filter_frame = ttk.Frame(self.root, padding=10)
        filter_frame.pack(fill="x")

        ttk.Label(filter_frame, text="Фильтры:", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")

        ttk.Label(filter_frame, text="Начальная дата:").grid(row=1, column=0, sticky="e", pady=2)
        self.start_date_var = tk.StringVar()
        ttk.Entry(filter_frame, textvariable=self.start_date_var, width=12).grid(row=1, column=1, sticky="w", pady=2)

        ttk.Label(filter_frame, text="Категория:").grid(row=1, column=2, sticky="e", pady=2)
        self.filter_cat_var = tk.StringVar(value="Все")
        self.filter_cat_cb = ttk.Combobox(filter_frame, textvariable=self.filter_cat_var, state="readonly")
        self.filter_cat_cb['values'] = ["Все", "Продукты", "Транспорт", "Развлечения", "Жилье", "Здоровье", "Другое"]
        self.filter_cat_cb.grid(row=1, column=3, sticky="w", pady=2)
        self.filter_cat_cb.current(0)

        ttk.Button(filter_frame, text="Применить фильтр", command=self.apply_filters).grid(row=1, column=4, padx=6)
        ttk.Button(filter_frame, text="Сбросить фильтры", command=self.reset_filters).grid(row=1, column=5, padx=6)

        # Основная таблица расходов
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(main_frame, columns=("date","category","amount","note"), show="headings")
        self.tree.heading("date", text="Дата")
        self.tree.heading("category", text="Категория")
        self.tree.heading("amount", text="Сумма")
        self.tree.heading("note", text="Заметка")
        self.tree.column("date", width=110)
        self.tree.column("category", width=120)
        self.tree.column("amount", width=100, anchor="e")
        self.tree.column("note", width=420)
        self.tree.pack(fill="both", expand=True)

        # Контролы под таблицей
        ctrl_frame = ttk.Frame(main_frame)
        ctrl_frame.pack(fill="x", pady=6)
        ttk.Button(ctrl_frame, text="Удалить выбранное", command=self.delete_selected).pack(side="left", padx=6)
        ttk.Button(ctrl_frame, text="Экспорт в JSON", command=self.export_json).pack(side="left", padx=6)
        ttk.Button(ctrl_frame, text="Импорт из JSON", command=self.import_json).pack(side="left")

        # С '.summary' — подсчет суммы за период
        summary_frame = ttk.Frame(self.root, padding=10)
        summary_frame.pack(fill="x")
        self.summary_var = tk.StringVar(value="Итого за период: 0.00")
        ttk.Label(summary_frame, textvariable=self.summary_var, font=("Segoe UI", 12, "bold")).pack(anchor="w")

        # Меню
        self._setup_menu()

    def _setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Сохранить как...", command=self.export_json)
        filemenu.add_command(label="Импорт из JSON", command=self.import_json)
        filemenu.add_separator()
        filemenu.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Файл", menu=filemenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="О программе", command=self._show_about)
        menubar.add_cascade(label="Справка", menu=helpmenu)

    def _show_about(self):
        messagebox.showinfo("О программе", "Expense Tracker — учёт личных расходов с фильтрами, JSON-экспортом и Git.")

    # ---------- Работа с данными ---------- #

    def add_expense(self):
        try:
            amount = float(self.amount_var.get())
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Сумма должна быть числом.")
            return
        category = self.category_var.get()
        date_str = self.date_var.get()
        try:
            date.fromisoformat(date_str)
        except ValueError:
            messagebox.showerror("Ошибка ввода", "Дата должна быть в формате YYYY-MM-DD.")
            return
        note = self.note_var.get()

        exp = Expense(amount, category, date_str, note)
        self.expenses.append(exp)
        self._append_to_table(exp)
        self.clear_add_form()
        self._save_history()  # сохраняем историю при изменении
        self._update_summary()

    def _append_to_table(self, exp: Expense):
        self.tree.insert("", "end", values=(exp.date.isoformat(), exp.category, f"{exp.amount:.2f}", exp.note))

    def clear_add_form(self):
        self.amount_var.set("0")
        self.date_var.set(date.today().isoformat())
        self.note_var.set("")

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Нет выбора", "Выберите элемент для удаления.")
            return
        idx = self.tree.index(sel[0])
        del self.expenses[idx]
        self.tree.delete(sel[0])
        self._save_history()
        self._update_summary()

    def export_json(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("JSON файлы","*.json")])
        if not path:
            return
        data = [e.to_dict() for e in self.expenses]
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Успех", "Данные экспортированы в JSON.")
        except Exception as e:
            messagebox.showerror("Ошибка экспорта", str(e))

    def import_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON файлы","*.json")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.expenses = [Expense.from_dict(d) for d in data]
            self._refresh_table()
            self._save_history()
            self._update_summary()
            messagebox.showinfo("Успех", "Данные импортированы.")
        except Exception as e:
            messagebox.showerror("Ошибка импорта", str(e))

    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for exp in self.expenses:
            self._append_to_table(exp)

    # ---------- История ---------- #

    def _load_history(self):
        if not os.path.exists(self.HISTORY_FILE):
            return
        try:
            with open(self.HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.expenses = [Expense.from_dict(d) for d in data]
            self._refresh_table()
        except Exception as e:
            messagebox.showwarning("Чтение истории", f"Не удалось загрузить историю: {e}")

    def _save_history(self):
        data = [e.to_dict() for e in self.expenses]
        with open(self.HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def apply_filters(self):
        start = self.start_date_var.get()
        cat = self.filter_cat_var.get()
        self.filtered_expenses = []
        self.tree.delete(*self.tree.get_children())

        for exp in self.expenses:
            if start:
                try:
                    start_dt = date.fromisoformat(start)
                    if exp.date < start_dt:
                        continue
                except ValueError:
                    pass
            if cat != "Все" and exp.category != cat:
                continue
            self.filtered_expenses.append(exp)

        for exp in self.filtered_expenses:
            self._append_to_table(exp)

        self._update_summary()

    def reset_filters(self):
        self.start_date_var.set("")
        self.filter_cat_var.set("Все")
        self.apply_filters()

    def _update_summary(self):
        total = sum(e.amount for e in self.expenses)
        self.summary_var.set(f"Итого за период: {total:.2f}")

# ---------- Запуск ---------- #

def main():
    root = tk.Tk()
    app = ExpenseTrackerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()