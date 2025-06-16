import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
import pandas as pd
import matplotlib.pyplot as plt

# ------------- Database Logic -------------
class DataStorage:
    def __init__(self, db_name="expenses.db"):
        self.db_name = db_name
        self._initialize_db()

    def _initialize_db(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    date TEXT NOT NULL
                )
            ''')
            conn.commit()

    def add_expense(self, amount, category, date):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO expenses (amount, category, date)
                VALUES (?, ?, ?)
            ''', (amount, category, date))
            conn.commit()

    def delete_expense(self, expense_id):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
        # Delete selected expense
            cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
            conn.commit()

        # Rebuild table with new IDs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS temp_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL
            )
        ''')
        cursor.execute('INSERT INTO temp_expenses (amount, category, date) SELECT amount, category, date FROM expenses')
        cursor.execute('DROP TABLE expenses')
        cursor.execute('ALTER TABLE temp_expenses RENAME TO expenses')
        conn.commit()


    def get_all_expenses(self):
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM expenses ORDER BY date DESC')
            return [dict(row) for row in cursor.fetchall()]

# ------------- Chart Drawing -------------
def create_pie_chart(expenses):
    if not expenses:
        messagebox.showinfo("Info", "No expenses to show.")
        return

    df = pd.DataFrame(expenses)
    category_totals = df.groupby('category')['amount'].sum()

    fig, ax = plt.subplots()
    ax.pie(category_totals, labels=category_totals.index, autopct='%1.1f%%', startangle=90)
    ax.set_title('Expense Breakdown by Category')
    plt.show()

# ------------- Main App UI -------------
class ExpenseTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("💸 Expense Tracker App")
        self.root.geometry("1000x600")
        self.root.configure(bg="#E3F6FD")

        self.storage = DataStorage()
        self.selected_expense_id = None
        self.is_dark_mode = False

        self.setup_ui()
        self.load_expenses()

    def setup_ui(self):
        # Frames
        self.left_frame = tk.Frame(self.root, bg="#E3F6FD", padx=20, pady=20)
        self.left_frame.pack(side="left", fill="y")

        self.right_frame = tk.Frame(self.root, bg="#FFFFFF", padx=20, pady=20)
        self.right_frame.pack(side="right", expand=True, fill="both")

        # Heading
        heading = tk.Label(self.left_frame, text="Expense Tracker", font=("Comic Sans MS", 24, "bold"), bg="#E3F6FD", fg="#0077B6")
        heading.pack(pady=10)

        # Amount
        tk.Label(self.left_frame, text="Amount:", font=("Comic Sans MS", 12), bg="#E3F6FD").pack(anchor="w")
        self.amount_entry = tk.Entry(self.left_frame, font=("Comic Sans MS", 11))
        self.amount_entry.pack(fill="x", pady=5)

        # Category Dropdown
        tk.Label(self.left_frame, text="Category:", font=("Comic Sans MS", 12), bg="#E3F6FD").pack(anchor="w")
        self.category_combobox = ttk.Combobox(self.left_frame, values=["Food", "Transportation", "Education", "Shopping", "Entertainment", "Other"], font=("Comic Sans MS", 11))
        self.category_combobox.pack(fill="x", pady=5)

        # Buttons
        btn_style = {"font": ("Verdana", 12, "bold"), "bg": "#00B4D8", "fg": "white", "bd": 0, "relief": "flat"}

        tk.Button(self.left_frame, text="➕ Add Expense", command=self.add_expense, **btn_style).pack(fill="x", pady=10)
        tk.Button(self.left_frame, text="🗑️ Delete Selected", command=self.delete_expense, **btn_style).pack(fill="x", pady=5)
        tk.Button(self.left_frame, text="📊 Show Pie Chart", command=self.show_pie_chart, **btn_style).pack(fill="x", pady=5)
        tk.Button(self.left_frame, text="🌓 Toggle Dark Mode", command=self.toggle_dark_mode, **btn_style).pack(fill="x", pady=5)

        # Treeview Table
        columns = ("ID", "Amount", "Category", "Date")
        self.expense_table = ttk.Treeview(self.right_frame, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            self.expense_table.heading(col, text=col)
            self.expense_table.column(col, width=100, anchor="center")
        self.expense_table.pack(expand=True, fill="both")

        self.expense_table.bind("<<TreeviewSelect>>", self.on_row_select)

    def add_expense(self):
        amount = self.amount_entry.get()
        category = self.category_combobox.get()
        date = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        if not amount or not category:
            messagebox.showerror("Input Error", "All fields are required.")
            return
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Input Error", "Amount must be a positive number.")
            return
        
        self.storage.add_expense(amount, category, date)
        self.load_expenses()
        self.clear_inputs()

        messagebox.showinfo("Success", "Expense added successfully!")

    def delete_expense(self):
        if not self.selected_expense_id:
            messagebox.showwarning("Selection Error", "Please select an expense to delete.")
            return

        self.storage.delete_expense(self.selected_expense_id)
        self.load_expenses()
        self.clear_inputs()
        messagebox.showinfo("Success", "Expense deleted successfully!")

    def load_expenses(self):
        expenses = self.storage.get_all_expenses()
        self.expense_table.delete(*self.expense_table.get_children())
        for exp in expenses:
            self.expense_table.insert("", "end", values=(exp["id"], exp["amount"], exp["category"], exp["date"]))

    def on_row_select(self, event):
        selected = self.expense_table.selection()
        if selected:
            item = self.expense_table.item(selected[0])
            values = item["values"]
            self.selected_expense_id = values[0]
            self.amount_entry.delete(0, tk.END)
            self.amount_entry.insert(0, values[1])
            self.category_combobox.set(values[2])

    def clear_inputs(self):
        self.amount_entry.delete(0, tk.END)
        self.category_combobox.set("")
        self.selected_expense_id = None

    def show_pie_chart(self):
        expenses = self.storage.get_all_expenses()
        create_pie_chart(expenses)

    def toggle_dark_mode(self):
        if self.is_dark_mode:
            self.root.configure(bg="#E3F6FD")
            self.left_frame.configure(bg="#E3F6FD")
            self.right_frame.configure(bg="#FFFFFF")
            for widget in self.left_frame.winfo_children():
                widget.configure(bg="#E3F6FD", fg="black")
            self.is_dark_mode = False
        else:
            self.root.configure(bg="#2C2C2C")
            self.left_frame.configure(bg="#2C2C2C")
            self.right_frame.configure(bg="#333333")
            for widget in self.left_frame.winfo_children():
                widget.configure(bg="#2C2C2C", fg="white")
            self.is_dark_mode = True

# ------------- Run App -------------
if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTrackerApp(root)
    root.mainloop()


