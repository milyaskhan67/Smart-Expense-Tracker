import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import datetime
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import pandas as pd
import hashlib
import os
import time
from fpdf import FPDF

class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Expense Tracker")
        self.root.geometry("1200x700")
        self.current_user = None
        self.theme = "light"
        self.setup_database()
        self.load_settings()
        self.create_login_screen()
        
    def setup_database(self):
        self.conn = sqlite3.connect('expense_tracker.db')
        self.cursor = self.conn.cursor()
        
        # Users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                theme TEXT DEFAULT 'light'
            )
        ''')
        
        # Expenses table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                is_deleted INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Goals table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                goal_name TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_amount REAL DEFAULT 0,
                target_date TEXT,
                created_date TEXT NOT NULL,
                is_completed INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Shared expenses table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS shared_expenses (
                shared_id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                friend_name TEXT NOT NULL,
                amount_owed REAL NOT NULL,
                is_paid INTEGER DEFAULT 0,
                FOREIGN KEY (expense_id) REFERENCES expenses (expense_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Categories table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_name TEXT NOT NULL,
                monthly_limit REAL,
                is_locked INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE(user_id, category_name)
            )
        ''')
        
        # Budgets table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                month_year TEXT NOT NULL,
                amount REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE(user_id, month_year)
            )
        ''')
        
        # Challenges table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS challenges (
                challenge_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                target_amount REAL NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                current_amount REAL DEFAULT 0,
                is_completed INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        self.conn.commit()
        
        # Add default categories if they don't exist
        default_categories = [
            ('Food', 10000),
            ('Transportation', 5000),
            ('Shopping', 8000),
            ('Entertainment', 3000),
            ('Utilities', 6000),
            ('Rent', 20000),
            ('Others', 5000)
        ]
        
        # Check if we have any users to associate categories with
        self.cursor.execute("SELECT user_id FROM users")
        users = self.cursor.fetchall()
        
        if users:
            for user_id in users:
                for category, limit in default_categories:
                    self.cursor.execute('''
                        INSERT OR IGNORE INTO categories (user_id, category_name, monthly_limit)
                        VALUES (?, ?, ?)
                    ''', (user_id[0], category, limit))
        
        self.conn.commit()
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_login_screen(self):
        self.clear_window()
        
        self.login_frame = ttk.Frame(self.root, padding="20")
        self.login_frame.pack(expand=True)
        
        ttk.Label(self.login_frame, text="Smart Expense Tracker", font=('Helvetica', 16, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
        
        ttk.Label(self.login_frame, text="Username:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(self.login_frame)
        self.username_entry.grid(row=1, column=1, pady=5)
        
        ttk.Label(self.login_frame, text="Password:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=2, column=1, pady=5)
        
        ttk.Button(self.login_frame, text="Login", command=self.login).grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(self.login_frame, text="Register", command=self.show_register).grid(row=4, column=0, columnspan=2, pady=5)
        
        # Add theme toggle button
        ttk.Button(self.login_frame, text="Toggle Theme", command=self.toggle_theme).grid(row=5, column=0, columnspan=2, pady=5)
    
    def toggle_theme(self):
        self.theme = "dark" if self.theme == "light" else "light"
        self.apply_theme()
        
        if self.current_user:
            self.cursor.execute("UPDATE users SET theme=? WHERE user_id=?", (self.theme, self.current_user[0]))
            self.conn.commit()
    
    def apply_theme(self):
        if self.theme == "dark":
            self.root.configure(bg='#2d2d2d')
            style = ttk.Style()
            style.theme_use('alt')
            style.configure('TFrame', background='#2d2d2d')
            style.configure('TLabel', background='#2d2d2d', foreground='white')
            style.configure('TButton', background='#3d3d3d', foreground='white')
            style.configure('TEntry', fieldbackground='#3d3d3d', foreground='white')
            style.configure('TCombobox', fieldbackground='#3d3d3d', foreground='white')
            style.map('TButton', background=[('active', '#4d4d4d')])
        else:
            self.root.configure(bg='SystemButtonFace')
            style = ttk.Style()
            style.theme_use('clam')
            style.configure('TFrame', background='SystemButtonFace')
            style.configure('TLabel', background='SystemButtonFace', foreground='black')
            style.configure('TButton', background='SystemButtonFace', foreground='black')
            style.configure('TEntry', fieldbackground='white', foreground='black')
            style.configure('TCombobox', fieldbackground='white', foreground='black')
    
    def show_register(self):
        self.register_window = tk.Toplevel(self.root)
        self.register_window.title("Register")
        self.register_window.geometry("400x300")
        
        ttk.Label(self.register_window, text="Register New Account").pack(pady=10)
        
        ttk.Label(self.register_window, text="Username:").pack()
        self.reg_username = ttk.Entry(self.register_window)
        self.reg_username.pack()
        
        ttk.Label(self.register_window, text="Password:").pack()
        self.reg_password = ttk.Entry(self.register_window, show="*")
        self.reg_password.pack()
        
        ttk.Label(self.register_window, text="Confirm Password:").pack()
        self.reg_confirm = ttk.Entry(self.register_window, show="*")
        self.reg_confirm.pack()
        
        ttk.Label(self.register_window, text="Email (optional):").pack()
        self.reg_email = ttk.Entry(self.register_window)
        self.reg_email.pack()
        
        ttk.Button(self.register_window, text="Register", command=self.register).pack(pady=10)
    
    def register(self):
        username = self.reg_username.get()
        password = self.reg_password.get()
        confirm = self.reg_confirm.get()
        email = self.reg_email.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Username and password are required")
            return
        
        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match")
            return
        
        hashed_password = self.hash_password(password)
        
        try:
            self.cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", 
                              (username, hashed_password, email))
            self.conn.commit()
            
            # Add default categories for the new user
            user_id = self.cursor.lastrowid
            default_categories = [
                ('Food', 10000),
                ('Transportation', 5000),
                ('Shopping', 8000),
                ('Entertainment', 3000),
                ('Utilities', 6000),
                ('Rent', 20000),
                ('Others', 5000)
            ]
            
            for category, limit in default_categories:
                self.cursor.execute('''
                    INSERT INTO categories (user_id, category_name, monthly_limit)
                    VALUES (?, ?, ?)
                ''', (user_id, category, limit))
            
            self.conn.commit()
            
            messagebox.showinfo("Success", "Registration successful. Please login.")
            self.register_window.destroy()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists")
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Username and password are required")
            return
        
        hashed_password = self.hash_password(password)
        
        self.cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
        user = self.cursor.fetchone()
        
        if user:
            self.current_user = user
            self.load_settings()
            # Destroy login frame
            self.login_frame.destroy()
            # Check if budget is set
            now = datetime.datetime.now()
            current_month = now.strftime("%Y-%m")
            self.cursor.execute('''
                SELECT amount 
                FROM budgets 
                WHERE user_id=? AND month_year=?
            ''', (self.current_user[0], current_month))
            budget = self.cursor.fetchone()
            if budget and budget[0] > 0:
                self.create_main_interface()
            else:
                self.start_budget()
        else:
            messagebox.showerror("Error", "Invalid username or password")
    
    def load_settings(self):
        if self.current_user:
            self.theme = self.current_user[4] if self.current_user[4] else "light"
        self.apply_theme()
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def create_main_interface(self):
            self.clear_window()
            self.apply_theme()
            
            # Create menu bar
            self.menu_bar = tk.Menu(self.root)
            
            # File menu
            file_menu = tk.Menu(self.menu_bar, tearoff=0)
            file_menu.add_command(label="Dashboard", command=self.show_dashboard)
            file_menu.add_command(label="Add Expense", command=self.show_add_expense)
            file_menu.add_command(label="View Expenses", command=self.show_expenses)
            file_menu.add_command(label="Reports", command=self.show_reports)
            file_menu.add_separator()
            file_menu.add_command(label="Logout", command=self.logout)
            file_menu.add_command(label="Exit", command=self.root.quit)
            self.menu_bar.add_cascade(label="Menu", menu=file_menu)
            
            # Goals menu
            goals_menu = tk.Menu(self.menu_bar, tearoff=0)
            goals_menu.add_command(label="Set New Goal", command=self.show_add_goal)
            goals_menu.add_command(label="View Goals", command=self.show_goals)
            self.menu_bar.add_cascade(label="Goals", menu=goals_menu)
            
            # Shared Expenses menu
            shared_menu = tk.Menu(self.menu_bar, tearoff=0)
            shared_menu.add_command(label="Add Shared Expense", command=self.show_add_shared)
            shared_menu.add_command(label="View Shared Expenses", command=self.show_shared)
            self.menu_bar.add_cascade(label="Shared", menu=shared_menu)
            
            # Settings menu
            settings_menu = tk.Menu(self.menu_bar, tearoff=0)
            settings_menu.add_command(label="Categories", command=self.manage_categories)
            settings_menu.add_command(label="Budget", command=self.manage_budget)
            settings_menu.add_command(label="Challenges", command=self.manage_challenges)
            settings_menu.add_command(label="Profile", command=self.manage_profile)
            settings_menu.add_command(label="Change Theme", command=self.toggle_theme)
            self.menu_bar.add_cascade(label="Settings", menu=settings_menu)
            
            self.root.config(menu=self.menu_bar)
            
            # Create main frame
            self.main_frame = ttk.Frame(self.root)
            self.main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Show dashboard by default
            self.show_dashboard()
    
    def show_dashboard(self):
        self.clear_main_frame()
        
        # Header
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(header_frame, text=f"Welcome, {self.current_user[1]}", font=('Helvetica', 14, 'bold')).pack(side=tk.LEFT)
        
        # Current month and year
        now = datetime.datetime.now()
        current_month = now.strftime("%B %Y")
        ttk.Label(header_frame, text=current_month, font=('Helvetica', 12)).pack(side=tk.RIGHT)
        
        # Summary cards
        summary_frame = ttk.Frame(self.main_frame)
        summary_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Get summary data
        total_expenses = self.get_monthly_expenses()
        budget = self.get_current_budget()
        savings = budget - total_expenses if budget else 0
        top_category = self.get_top_category()
        
        # Expense card
        expense_card = ttk.Frame(summary_frame, relief=tk.RIDGE, borderwidth=2)
        expense_card.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.BOTH)
        ttk.Label(expense_card, text="Total Expenses", font=('Helvetica', 10, 'bold')).pack(pady=5)
        ttk.Label(expense_card, text=f"PKR {total_expenses:,.2f}", font=('Helvetica', 14)).pack(pady=5)
        
        # Budget card
        budget_card = ttk.Frame(summary_frame, relief=tk.RIDGE, borderwidth=2)
        budget_card.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.BOTH)
        ttk.Label(budget_card, text="Monthly Budget", font=('Helvetica', 10, 'bold')).pack(pady=5)
        budget_text = f"PKR {budget:,.2f}" if budget else "Not set"
        ttk.Label(budget_card, text=budget_text, font=('Helvetica', 14)).pack(pady=5)
        
        # Savings card
        savings_card = ttk.Frame(summary_frame, relief=tk.RIDGE, borderwidth=2)
        savings_card.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.BOTH)
        ttk.Label(savings_card, text="Savings", font=('Helvetica', 10, 'bold')).pack(pady=5)
        savings_text = f"PKR {savings:,.2f}" if budget else "Budget not set"
        ttk.Label(savings_card, text=savings_text, font=('Helvetica', 14)).pack(pady=5)
        
        # Top category card
        category_card = ttk.Frame(summary_frame, relief=tk.RIDGE, borderwidth=2)
        category_card.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.BOTH)
        ttk.Label(category_card, text="Top Category", font=('Helvetica', 10, 'bold')).pack(pady=5)
        category_text = top_category if top_category else "No expenses"
        ttk.Label(category_card, text=category_text, font=('Helvetica', 14)).pack(pady=5)
        
        # Charts frame
        charts_frame = ttk.Frame(self.main_frame)
        charts_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pie chart
        pie_frame = ttk.Frame(charts_frame)
        pie_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        ttk.Label(pie_frame, text="Expense by Category", font=('Helvetica', 10, 'bold')).pack()
        self.create_pie_chart(pie_frame)
        
        # Bar chart
        bar_frame = ttk.Frame(charts_frame)
        bar_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        ttk.Label(bar_frame, text="Monthly Trend", font=('Helvetica', 10, 'bold')).pack()
        self.create_bar_chart(bar_frame)
        
        # Recent expenses
        recent_frame = ttk.Frame(self.main_frame)
        recent_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(recent_frame, text="Recent Expenses", font=('Helvetica', 12, 'bold')).pack(anchor=tk.W)
        
        columns = ("Date", "Category", "Amount", "Description")
        self.recent_tree = ttk.Treeview(recent_frame, columns=columns, show="headings", height=5)
        
        for col in columns:
            self.recent_tree.heading(col, text=col)
            self.recent_tree.column(col, width=100)
        
        self.recent_tree.pack(fill=tk.BOTH, expand=True)
        
        # Load recent expenses
        self.load_recent_expenses()
        
        # Budget alerts
        if budget and total_expenses > 0:
            percentage = (total_expenses / budget) * 100
            if percentage > 100:
                messagebox.showwarning("Budget Alert", f"You have exceeded your budget by {percentage-100:.2f}%!")
            elif percentage > 80:
                messagebox.showwarning("Budget Alert", f"You have used {percentage:.2f}% of your budget. Consider reducing expenses.")
    
    def get_monthly_expenses(self):
        now = datetime.datetime.now()
        month_year = now.strftime("%Y-%m")
        
        self.cursor.execute('''
            SELECT COALESCE(SUM(amount), 0) 
            FROM expenses 
            WHERE user_id=? AND strftime('%Y-%m', date)=? AND is_deleted=0
        ''', (self.current_user[0], month_year))
        
        return self.cursor.fetchone()[0]
    
    def get_current_budget(self):
        now = datetime.datetime.now()
        month_year = now.strftime("%Y-%m")
        
        self.cursor.execute('''
            SELECT amount FROM budgets 
            WHERE user_id=? AND month_year=?
        ''', (self.current_user[0], month_year))
        
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def get_top_category(self):
        now = datetime.datetime.now()
        month_year = now.strftime("%Y-%m")
        
        self.cursor.execute('''
            SELECT category, SUM(amount) as total 
            FROM expenses 
            WHERE user_id=? AND strftime('%Y-%m', date)=? AND is_deleted=0
            GROUP BY category 
            ORDER BY total DESC 
            LIMIT 1
        ''', (self.current_user[0], month_year))
        
        result = self.cursor.fetchone()
        return f"{result[0]}: PKR {result[1]:,.2f}" if result else None
    
    def create_pie_chart(self, parent):
        now = datetime.datetime.now()
        month_year = now.strftime("%Y-%m")

        self.cursor.execute('''
            SELECT category, SUM(amount) as total 
            FROM expenses 
            WHERE user_id=? AND strftime('%Y-%m', date)=? AND is_deleted=0
            GROUP BY category
        ''', (self.current_user[0], month_year))

        data = self.cursor.fetchall()

        # Filter out categories with non-positive totals
        filtered_data = [(cat, amt) for cat, amt in data if amt > 0]

        if not filtered_data:
            ttk.Label(parent, text="No expense data available").pack()
            return

        categories = [item[0] for item in filtered_data]
        amounts = [item[1] for item in filtered_data]

        fig, ax = plt.subplots(figsize=(5, 4))
        ax.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        ax.set_title('Expense Distribution')

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def create_bar_chart(self, parent):
        # Get data for last 6 months
        now = datetime.datetime.now()
        months = []
        totals = []
        
        for i in range(5, -1, -1):
            month = (now - datetime.timedelta(days=30*i)).strftime("%Y-%m")
            months.append(month)
            
            self.cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) 
                FROM expenses 
                WHERE user_id=? AND strftime('%Y-%m', date)=? AND is_deleted=0
            ''', (self.current_user[0], month))
            
            totals.append(self.cursor.fetchone()[0])
        
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.bar(months, totals)
        ax.set_title('Monthly Spending Trend')
        ax.set_ylabel('Amount (PKR)')
        ax.tick_params(axis='x', rotation=45)
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def load_recent_expenses(self):
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)
        
        self.cursor.execute('''
            SELECT date, category, amount, description 
            FROM expenses 
            WHERE user_id=? AND is_deleted=0
            ORDER BY date DESC 
            LIMIT 10
        ''', (self.current_user[0],))
        
        for expense in self.cursor.fetchall():
            formatted_date = datetime.datetime.strptime(expense[0], "%Y-%m-%d").strftime("%d %b %Y")
            self.recent_tree.insert("", tk.END, values=(
                formatted_date, 
                expense[1], 
                f"PKR {expense[2]:,.2f}", 
                expense[3] if expense[3] else ""
            ))
    
    def show_add_expense(self):
        self.clear_main_frame()
        
        ttk.Label(self.main_frame, text="Add New Expense", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        form_frame = ttk.Frame(self.main_frame)
        form_frame.pack(pady=10)
        
        # Amount
        ttk.Label(form_frame, text="Amount (PKR):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.amount_entry = ttk.Entry(form_frame)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Category
        ttk.Label(form_frame, text="Category:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(form_frame, textvariable=self.category_var)
        self.category_combo.grid(row=1, column=1, padx=5, pady=5)
        
        # Load categories
        self.load_categories()
        
        # Date
        ttk.Label(form_frame, text="Date:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
        self.date_entry = ttk.Entry(form_frame)
        self.date_entry.grid(row=2, column=1, padx=5, pady=5)
        self.date_entry.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
        self.desc_entry = ttk.Entry(form_frame)
        self.desc_entry.grid(row=3, column=1, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Save", command=self.save_expense).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.show_dashboard).pack(side=tk.LEFT, padx=5)
        
        # Check for category limits
        self.check_category_limits()
    
    def load_categories(self):
        self.cursor.execute("SELECT category_name FROM categories WHERE user_id=?", (self.current_user[0],))
        categories = [row[0] for row in self.cursor.fetchall()]
        self.category_combo['values'] = categories
        if categories:
            self.category_combo.current(0)
    
    def check_category_limits(self):
        category = self.category_var.get()
        if not category:
            return
        
        self.cursor.execute('''
            SELECT monthly_limit, is_locked 
            FROM categories 
            WHERE user_id=? AND category_name=?
        ''', (self.current_user[0], category))
        
        result = self.cursor.fetchone()
        if not result:
            return
        
        limit, is_locked = result
        
        if is_locked:
            messagebox.showerror("Category Locked", f"The {category} category is locked as you've exceeded its monthly limit.")
            return
        
        if limit:
            now = datetime.datetime.now()
            month_year = now.strftime("%Y-%m")
            
            self.cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) 
                FROM expenses 
                WHERE user_id=? AND category=? AND strftime('%Y-%m', date)=? AND is_deleted=0
            ''', (self.current_user[0], category, month_year))
            
            spent = self.cursor.fetchone()[0]
            
            if spent >= limit:
                self.cursor.execute('''
                    UPDATE categories 
                    SET is_locked=1 
                    WHERE user_id=? AND category_name=?
                ''', (self.current_user[0], category))
                self.conn.commit()
                messagebox.showwarning("Category Locked", f"You've reached the monthly limit for {category}. This category is now locked.")
            elif spent >= 0.8 * limit:
                messagebox.showwarning("Approaching Limit", f"You've used {spent/limit*100:.1f}% of your {category} budget. Consider reducing spending in this category.")
    
    def save_expense(self):
        try:
            amount = float(self.amount_entry.get())
            category = self.category_var.get()
            date = self.date_entry.get()
            description = self.desc_entry.get()
            
            # Validate date
            try:
                datetime.datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD")
                return
            
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be positive")
                return
            
            if not category:
                messagebox.showerror("Error", "Category is required")
                return
            
            # Check if category is locked
            self.cursor.execute('''
                SELECT is_locked FROM categories 
                WHERE user_id=? AND category_name=?
            ''', (self.current_user[0], category))
            
            result = self.cursor.fetchone()
            if result and result[0]:
                messagebox.showerror("Error", f"The {category} category is locked as you've exceeded its monthly limit.")
                return
            
            # Save expense
            self.cursor.execute('''
                INSERT INTO expenses (user_id, amount, category, date, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (self.current_user[0], amount, category, date, description))
            
            self.conn.commit()
            
            # Check category limits
            self.check_category_limits()
            
            messagebox.showinfo("Success", "Expense added successfully")
            self.show_dashboard()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid amount. Please enter a number")
    
    
    
    def show_expenses(self, period="all"):
        self.clear_main_frame()
        
        ttk.Label(self.main_frame, text="View Expenses", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        # Filter options
        filter_frame = ttk.Frame(self.main_frame)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Filter by:").pack(side=tk.LEFT)
        
        self.filter_var = tk.StringVar(value=period)
        ttk.Radiobutton(filter_frame, text="All", variable=self.filter_var, value="all", 
                        command=lambda: self.show_expenses("all")).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="This Month", variable=self.filter_var, value="month", 
                        command=lambda: self.show_expenses("month")).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="This Week", variable=self.filter_var, value="week", 
                        command=lambda: self.show_expenses("week")).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Today", variable=self.filter_var, value="today", 
                        command=lambda: self.show_expenses("today")).pack(side=tk.LEFT, padx=5)
        
        # Category filter
        ttk.Label(filter_frame, text="Category:").pack(side=tk.LEFT, padx=(10, 5))
        self.expense_category_var = tk.StringVar()
        self.expense_category_combo = ttk.Combobox(filter_frame, textvariable=self.expense_category_var, state="readonly")
        self.expense_category_combo.pack(side=tk.LEFT, padx=5)
        self.expense_category_combo.set("All Categories")
        
        # Load categories
        self.cursor.execute("SELECT category_name FROM categories WHERE user_id=?", (self.current_user[0],))
        categories = ["All Categories"] + [row[0] for row in self.cursor.fetchall()]
        self.expense_category_combo['values'] = categories
        
        # Search
        ttk.Label(filter_frame, text="Search:").pack(side=tk.LEFT, padx=(10, 5))
        self.search_entry = ttk.Entry(filter_frame)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="Go", command=self.apply_expense_filters).pack(side=tk.LEFT, padx=5)
        
        # Treeview for expenses
        columns = ("ID", "Date", "Category", "Amount", "Description", "Actions")
        self.expense_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.expense_tree.heading(col, text=col)
            self.expense_tree.column(col, width=100)
        
        self.expense_tree.column("ID", width=50)
        self.expense_tree.column("Date", width=100)
        self.expense_tree.column("Amount", width=100)
        self.expense_tree.column("Actions", width=150)
        
        self.expense_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Action buttons for selected expense
        action_frame = ttk.Frame(self.main_frame)
        action_frame.pack(pady=5)
        
        ttk.Button(action_frame, text="Edit", command=self.edit_expense).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Delete", command=self.delete_expense).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Undo Delete", command=self.undo_delete_expense).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Back", command=self.show_dashboard).pack(side=tk.LEFT, padx=5)
        
        # Load expenses
        self.load_expenses(period)
    
    def load_expenses(self, period="all", category=None, search=None):
        for item in self.expense_tree.get_children():
            self.expense_tree.delete(item)
        
        query = '''
            SELECT expense_id, date, category, amount, description 
            FROM expenses 
            WHERE user_id=? AND is_deleted=0
        '''
        params = [self.current_user[0]]
        
        now = datetime.datetime.now()
        
        if period == "month":
            month_year = now.strftime("%Y-%m")
            query += " AND strftime('%Y-%m', date)=?"
            params.append(month_year)
        elif period == "week":
            week_start = (now - datetime.timedelta(days=now.weekday())).strftime("%Y-%m-%d")
            query += " AND date >= ?"
            params.append(week_start)
        elif period == "today":
            today = now.strftime("%Y-%m-%d")
            query += " AND date=?"
            params.append(today)
        
        if category and category != "All Categories":
            query += " AND category=?"
            params.append(category)
        
        if search:
            query += " AND (category LIKE ? OR description LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        
        query += " ORDER BY date DESC"
        
        self.cursor.execute(query, params)
        
        for expense in self.cursor.fetchall():
            formatted_date = datetime.datetime.strptime(expense[1], "%Y-%m-%d").strftime("%d %b %Y")
            self.expense_tree.insert("", tk.END, values=(
                expense[0], 
                formatted_date, 
                expense[2], 
                f"PKR {expense[3]:,.2f}", 
                expense[4] if expense[4] else "",
                "Edit | Delete"
            ))
    
    def apply_expense_filters(self):
        period = self.filter_var.get()
        category = self.expense_category_var.get()
        search = self.search_entry.get()
        
        self.load_expenses(period, category if category != "" else None, search if search != "" else None)
    
    def edit_expense(self):
        selected = self.expense_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an expense to edit")
            return
        
        item = self.expense_tree.item(selected[0])
        expense_id = item['values'][0]
        
        # Get expense details
        self.cursor.execute('''
            SELECT amount, category, date, description 
            FROM expenses 
            WHERE expense_id=?
        ''', (expense_id,))
        
        expense = self.cursor.fetchone()
        
        # Create edit window
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Expense")
        edit_window.geometry("400x300")
        
        ttk.Label(edit_window, text="Edit Expense", font=('Helvetica', 12, 'bold')).pack(pady=10)
        
        form_frame = ttk.Frame(edit_window)
        form_frame.pack(pady=10)
        
        # Amount
        ttk.Label(form_frame, text="Amount (PKR):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        amount_entry = ttk.Entry(form_frame)
        amount_entry.grid(row=0, column=1, padx=5, pady=5)
        amount_entry.insert(0, expense[0])
        
        # Category
        ttk.Label(form_frame, text="Category:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        category_var = tk.StringVar(value=expense[1])
        category_combo = ttk.Combobox(form_frame, textvariable=category_var)
        category_combo.grid(row=1, column=1, padx=5, pady=5)
        
        # Load categories
        self.cursor.execute("SELECT category_name FROM categories WHERE user_id=?", (self.current_user[0],))
        categories = [row[0] for row in self.cursor.fetchall()]
        category_combo['values'] = categories
        
        # Date
        ttk.Label(form_frame, text="Date:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
        date_entry = ttk.Entry(form_frame)
        date_entry.grid(row=2, column=1, padx=5, pady=5)
        date_entry.insert(0, expense[2])
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
        desc_entry = ttk.Entry(form_frame)
        desc_entry.grid(row=3, column=1, padx=5, pady=5)
        desc_entry.insert(0, expense[3] if expense[3] else "")
        
        # Buttons
        button_frame = ttk.Frame(edit_window)
        button_frame.pack(pady=10)
        
        def save_changes():
            try:
                amount = float(amount_entry.get())
                category = category_var.get()
                date = date_entry.get()
                description = desc_entry.get()
                
                # Validate date
                try:
                    datetime.datetime.strptime(date, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD")
                    return
                
                if amount <= 0:
                    messagebox.showerror("Error", "Amount must be positive")
                    return
                
                if not category:
                    messagebox.showerror("Error", "Category is required")
                    return
                
                # Update expense
                self.cursor.execute('''
                    UPDATE expenses 
                    SET amount=?, category=?, date=?, description=? 
                    WHERE expense_id=?
                ''', (amount, category, date, description, expense_id))
                
                self.conn.commit()
                
                messagebox.showinfo("Success", "Expense updated successfully")
                edit_window.destroy()
                self.show_expenses(self.filter_var.get())
                
            except ValueError:
                messagebox.showerror("Error", "Invalid amount. Please enter a number")
        
        ttk.Button(button_frame, text="Save", command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=edit_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def delete_expense(self):
        selected = self.expense_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an expense to delete")
            return
        
        item = self.expense_tree.item(selected[0])
        expense_id = item['values'][0]
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this expense?"):
            # Soft delete (move to trash)
            self.cursor.execute('''
                UPDATE expenses 
                SET is_deleted=1 
                WHERE expense_id=?
            ''', (expense_id,))
            
            self.conn.commit()
            
            messagebox.showinfo("Success", "Expense moved to trash")
            self.show_expenses(self.filter_var.get())
    
    def undo_delete_expense(self):
        # Show items in trash
        self.cursor.execute('''
            SELECT expense_id, date, category, amount, description 
            FROM expenses 
            WHERE user_id=? AND is_deleted=1
            ORDER BY date DESC
        ''', (self.current_user[0],))
        
        deleted_expenses = self.cursor.fetchall()
        
        if not deleted_expenses:
            messagebox.showinfo("Info", "Trash is empty")
            return
        
        # Create undo window
        undo_window = tk.Toplevel(self.root)
        undo_window.title("Restore Deleted Expenses")
        undo_window.geometry("600x400")
        
        ttk.Label(undo_window, text="Deleted Expenses (Trash)", font=('Helvetica', 12, 'bold')).pack(pady=10)
        
        columns = ("ID", "Date", "Category", "Amount", "Description")
        tree = ttk.Treeview(undo_window, columns=columns, show="headings", height=10)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        tree.column("ID", width=50)
        tree.column("Date", width=100)
        tree.column("Amount", width=100)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for expense in deleted_expenses:
            formatted_date = datetime.datetime.strptime(expense[1], "%Y-%m-%d").strftime("%d %b %Y")
            tree.insert("", tk.END, values=(
                expense[0], 
                formatted_date, 
                expense[2], 
                f"PKR {expense[3]:,.2f}", 
                expense[4] if expense[4] else ""
            ))
        
        def restore_selected():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Warning", "Please select an expense to restore")
                return
            
            item = tree.item(selected[0])
            expense_id = item['values'][0]
            
            self.cursor.execute('''
                UPDATE expenses 
                SET is_deleted=0 
                WHERE expense_id=?
            ''', (expense_id,))
            
            self.conn.commit()
            
            messagebox.showinfo("Success", "Expense restored successfully")
            undo_window.destroy()
            self.show_expenses(self.filter_var.get())
        
        def empty_trash():
            if messagebox.askyesno("Confirm", "Are you sure you want to permanently delete all items in trash?"):
                self.cursor.execute('''
                    DELETE FROM expenses 
                    WHERE user_id=? AND is_deleted=1
                ''', (self.current_user[0],))
                
                self.conn.commit()
                
                messagebox.showinfo("Success", "Trash emptied")
                undo_window.destroy()
        
        button_frame = ttk.Frame(undo_window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Restore Selected", command=restore_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Empty Trash", command=empty_trash).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=undo_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def show_reports(self):
        self.clear_main_frame()
        
        ttk.Label(self.main_frame, text="Reports", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        # Report type selection
        report_frame = ttk.Frame(self.main_frame)
        report_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(report_frame, text="Report Type:").pack(side=tk.LEFT)
        
        self.report_type = tk.StringVar(value="category")
        
        ttk.Radiobutton(report_frame, text="By Category", variable=self.report_type, 
                        value="category", command=self.generate_report).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(report_frame, text="By Time Period", variable=self.report_type, 
                        value="period", command=self.generate_report).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(report_frame, text="Comparison", variable=self.report_type, 
                        value="comparison", command=self.generate_report).pack(side=tk.LEFT, padx=5)
        
        # Time period selection
        self.time_frame = ttk.Frame(self.main_frame)
        self.time_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(self.time_frame, text="Time Period:").pack(side=tk.LEFT)
        
        self.time_period = tk.StringVar(value="month")
        
        ttk.Radiobutton(self.time_frame, text="Month", variable=self.time_period, 
                        value="month", command=self.generate_report).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(self.time_frame, text="Quarter", variable=self.time_period, 
                        value="quarter", command=self.generate_report).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(self.time_frame, text="Year", variable=self.time_period, 
                        value="year", command=self.generate_report).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(self.time_frame, text="Custom", variable=self.time_period, 
                        value="custom", command=self.generate_report).pack(side=tk.LEFT, padx=5)
        
        # Custom date range (hidden by default)
        self.custom_frame = ttk.Frame(self.main_frame)
        
        ttk.Label(self.custom_frame, text="From:").grid(row=0, column=0, padx=5, pady=5)
        self.from_date = ttk.Entry(self.custom_frame)
        self.from_date.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.custom_frame, text="To:").grid(row=0, column=2, padx=5, pady=5)
        self.to_date = ttk.Entry(self.custom_frame)
        self.to_date.grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(self.custom_frame, text="Apply", command=self.generate_report).grid(row=0, column=4, padx=5)
        
        # Chart frame
        self.chart_frame = ttk.Frame(self.main_frame)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Generate initial report
        self.generate_report()
        
        # Export button
        ttk.Button(self.main_frame, text="Export to PDF", command=self.export_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.main_frame, text="Back", command=self.show_dashboard).pack(side=tk.LEFT, padx=5)
    
    def generate_report(self):
        # Show/hide custom date frame
        if self.time_period.get() == "custom":
            self.custom_frame.pack(fill=tk.X, padx=10, pady=5)
        else:
            self.custom_frame.pack_forget()
        
        # Clear previous chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        report_type = self.report_type.get()
        
        if report_type == "category":
            self.generate_category_report()
        elif report_type == "period":
            self.generate_period_report()
        elif report_type == "comparison":
            self.generate_comparison_report()
    
    def generate_category_report(self):
        # Get time period
        start_date, end_date = self.get_date_range()
        
        # Get data
        self.cursor.execute('''
            SELECT category, SUM(amount) as total 
            FROM expenses 
            WHERE user_id=? AND date BETWEEN ? AND ? AND is_deleted=0
            GROUP BY category 
            ORDER BY total DESC
        ''', (self.current_user[0], start_date, end_date))
        
        data = self.cursor.fetchall()
        
        if not data:
            ttk.Label(self.chart_frame, text="No expense data available for the selected period").pack()
            return
        
        # Filter out categories with non-positive totals
        filtered = [(cat, amt) for cat, amt in data if amt > 0]
        if not filtered:
            ttk.Label(self.chart_frame, text="No expense data available for the selected period").pack()
            return

        categories = [item[0] for item in filtered]
        amounts = [item[1] for item in filtered]

        # Create chart
        fig, ax = plt.subplots(figsize=(8, 6))

        if len(categories) <= 5:
            # Pie chart for small number of categories
            ax.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=90)
            ax.set_title('Expense Distribution by Category')
        else:
            # Bar chart for many categories
            bars = ax.bar(categories, amounts)
            ax.set_title('Expenses by Category')
            ax.set_ylabel('Amount (PKR)')
            ax.tick_params(axis='x', rotation=45)
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:,.2f}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom')
        
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        
    def generate_period_report(self):
        # Get time period
        time_period = self.time_period.get()
        now = datetime.datetime.now()
        
        if time_period == "month":
            # Monthly breakdown for the year
            months = []
            totals = []
            
            for i in range(1, 13):
                month = f"{now.year}-{i:02d}"
                months.append(datetime.datetime.strptime(month, "%Y-%m").strftime("%b %Y"))
                
                self.cursor.execute('''
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM expenses 
                    WHERE user_id=? AND strftime('%Y-%m', date)=? AND is_deleted=0
                ''', (self.current_user[0], month))
                
                totals.append(self.cursor.fetchone()[0])
            
            # Create chart
            fig, ax = plt.subplots(figsize=(8, 6))
            bars = ax.bar(months, totals)
            ax.set_title('Monthly Expenses')
            ax.set_ylabel('Amount (PKR)')
            ax.tick_params(axis='x', rotation=45)
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:,.2f}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom')
            
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        elif time_period == "quarter":
            # Quarterly breakdown
            quarters = []
            totals = []
            
            for q in range(1, 5):
                start_month = (q-1)*3 + 1
                end_month = q*3
                
                start_date = f"{now.year}-{start_month:02d}-01"
                end_date = f"{now.year}-{end_month:02d}-{31 if end_month in [1,3,5,7,8,10,12] else 30}"
                
                quarters.append(f"Q{q} {now.year}")
                
                self.cursor.execute('''
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM expenses 
                    WHERE user_id=? AND date BETWEEN ? AND ? AND is_deleted=0
                ''', (self.current_user[0], start_date, end_date))
                
                totals.append(self.cursor.fetchone()[0])
            
            # Create chart
            fig, ax = plt.subplots(figsize=(8, 6))
            bars = ax.bar(quarters, totals)
            ax.set_title('Quarterly Expenses')
            ax.set_ylabel('Amount (PKR)')
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:,.2f}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom')
            
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        elif time_period == "year":
            # Yearly breakdown for last 5 years
            years = []
            totals = []
            
            for y in range(now.year-4, now.year+1):
                years.append(str(y))
                
                self.cursor.execute('''
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM expenses 
                    WHERE user_id=? AND strftime('%Y', date)=? AND is_deleted=0
                ''', (self.current_user[0], str(y)))
                
                totals.append(self.cursor.fetchone()[0])
            
            # Create chart
            fig, ax = plt.subplots(figsize=(8, 6))
            bars = ax.bar(years, totals)
            ax.set_title('Yearly Expenses')
            ax.set_ylabel('Amount (PKR)')
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:,.2f}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom')
            
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        elif time_period == "custom":
            # Custom date range
            try:
                start_date = self.from_date.get()
                end_date = self.to_date.get()
                
                # Validate dates
                datetime.datetime.strptime(start_date, "%Y-%m-%d")
                datetime.datetime.strptime(end_date, "%Y-%m-%d")
                
                # Get daily expenses
                self.cursor.execute('''
                    SELECT date, SUM(amount) 
                    FROM expenses 
                    WHERE user_id=? AND date BETWEEN ? AND ? AND is_deleted=0
                    GROUP BY date 
                    ORDER BY date
                ''', (self.current_user[0], start_date, end_date))
                
                data = self.cursor.fetchall()
                
                if not data:
                    ttk.Label(self.chart_frame, text="No expense data available for the selected period , (format for date is yy-mm-dd)").pack()
                    return
                
                dates = [datetime.datetime.strptime(item[0], "%Y-%m-%d").strftime("%d %b") for item in data]
                amounts = [item[1] for item in data]
                
                # Create chart
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.plot(dates, amounts, marker='o')
                ax.set_title('Daily Expenses')
                ax.set_ylabel('Amount (PKR)')
                ax.tick_params(axis='x', rotation=45)
                
                # Add value labels
                for i, amount in enumerate(amounts):
                    ax.annotate(f'{amount:,.2f}',
                                xy=(i, amount),
                                xytext=(0, 5),  # 5 points vertical offset
                                textcoords="offset points",
                                ha='center', va='bottom')
                
                canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
                
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD")
    
    def generate_comparison_report(self):
        # Compare two time periods
        now = datetime.datetime.now()
        
        # Get previous period
        if self.time_period.get() == "month":
            current_start = f"{now.year}-{now.month:02d}-01"
            current_end = now.strftime("%Y-%m-%d")
            
            prev_month = now - datetime.timedelta(days=30)
            prev_start = f"{prev_month.year}-{prev_month.month:02d}-01"
            prev_end = prev_month.strftime("%Y-%m-%d")
            
            labels = [now.strftime("%B %Y"), prev_month.strftime("%B %Y")]
            
        elif self.time_period.get() == "quarter":
            current_quarter = (now.month - 1) // 3 + 1
            current_start_month = (current_quarter - 1) * 3 + 1
            current_start = f"{now.year}-{current_start_month:02d}-01"
            current_end = now.strftime("%Y-%m-%d")
            
            prev_quarter = current_quarter - 1 if current_quarter > 1 else 4
            prev_year = now.year if current_quarter > 1 else now.year - 1
            prev_start_month = (prev_quarter - 1) * 3 + 1
            prev_start = f"{prev_year}-{prev_start_month:02d}-01"
            prev_end = f"{prev_year}-{prev_start_month+2:02d}-{31 if prev_start_month+2 in [1,3,5,7,8,10,12] else 30}"
            
            labels = [f"Q{current_quarter} {now.year}", f"Q{prev_quarter} {prev_year}"]
            
        elif self.time_period.get() == "year":
            current_start = f"{now.year}-01-01"
            current_end = now.strftime("%Y-%m-%d")
            
            prev_start = f"{now.year-1}-01-01"
            prev_end = f"{now.year-1}-12-31"
            
            labels = [str(now.year), str(now.year-1)]
            
        elif self.time_period.get() == "custom":
            try:
                current_start = self.from_date.get()
                current_end = self.to_date.get()
                
                # Validate dates
                datetime.datetime.strptime(current_start, "%Y-%m-%d")
                datetime.datetime.strptime(current_end, "%Y-%m-%d")
                
                # Calculate previous period
                start_date = datetime.datetime.strptime(current_start, "%Y-%m-%d")
                end_date = datetime.datetime.strptime(current_end, "%Y-%m-%d")
                delta = end_date - start_date
                
                prev_start_date = start_date - delta - datetime.timedelta(days=1)
                prev_end_date = start_date - datetime.timedelta(days=1)
                
                prev_start = prev_start_date.strftime("%Y-%m-%d")
                prev_end = prev_end_date.strftime("%Y-%m-%d")
                
                labels = [
                    f"{start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}",
                    f"{prev_start_date.strftime('%d %b %Y')} to {prev_end_date.strftime('%d %b %Y')}"
                ]
                
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD")
        
        # Get data for both periods
        periods = [
            (current_start, current_end),
            (prev_start, prev_end)
        ]
        
        categories = set()
        data = {}
        
        for i, (start, end) in enumerate(periods):
            self.cursor.execute('''
                SELECT category, SUM(amount) 
                FROM expenses 
                WHERE user_id=? AND date BETWEEN ? AND ? AND is_deleted=0
                GROUP BY category
            ''', (self.current_user[0], start, end))
            
            results = self.cursor.fetchall()
            data[labels[i]] = {}
            
            for category, amount in results:
                data[labels[i]][category] = amount
                categories.add(category)
        
        # Prepare data for chart
        categories = sorted(categories)
        x = range(len(categories))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        for i, label in enumerate(labels):
            amounts = [data[label].get(cat, 0) for cat in categories]
            ax.bar([p + i*width for p in x], amounts, width, label=label)
        
        ax.set_title('Expense Comparison')
        ax.set_ylabel('Amount (PKR)')
        ax.set_xticks([p + width/2 for p in x])
        ax.set_xticklabels(categories, rotation=45)
        ax.legend()
        
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def get_date_range(self):
        time_period = self.time_period.get()
        now = datetime.datetime.now()
        
        if time_period == "month":
            start_date = f"{now.year}-{now.month:02d}-01"
            end_date = now.strftime("%Y-%m-%d")
        elif time_period == "quarter":
            quarter = (now.month - 1) // 3 + 1
            start_month = (quarter - 1) * 3 + 1
            end_month = quarter * 3
            
            start_date = f"{now.year}-{start_month:02d}-01"
            end_date = f"{now.year}-{end_month:02d}-{31 if end_month in [1,3,5,7,8,10,12] else 30}"
        elif time_period == "year":
            start_date = f"{now.year}-01-01"
            end_date = now.strftime("%Y-%m-%d")
        elif time_period == "custom":
            start_date = self.from_date.get()
            end_date = self.to_date.get()
            
            # Validate dates
            try:
                datetime.datetime.strptime(start_date, "%Y-%m-%d")
                datetime.datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                return (None, None)
        
        return (start_date, end_date)
    
    
    def export_report(self):
        try:
            # Create a new PDF document
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Add title
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, txt="Expense Report", ln=1, align='C')
            pdf.set_font("Arial", size=12)
            
            # Add user info and date
            pdf.cell(200, 10, txt=f"User: {self.current_user[1]}", ln=1)
            pdf.cell(200, 10, txt=f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1)
            pdf.ln(5)
            
            # Get the report type and time period
            report_type = self.report_type.get()
            time_period = self.time_period.get()
            
            # Add report parameters
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt="Report Parameters:", ln=1)
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Report Type: {report_type.capitalize()}", ln=1)
            pdf.cell(200, 10, txt=f"Time Period: {time_period.capitalize()}", ln=1)
            
            if time_period == "custom":
                pdf.cell(200, 10, txt=f"From: {self.from_date.get()} To: {self.to_date.get()}", ln=1)
            
            pdf.ln(10)
            
            # Get the appropriate data based on report type
            if report_type == "category":
                self.export_category_report(pdf, time_period)
            elif report_type == "period":
                self.export_period_report(pdf, time_period)
            elif report_type == "comparison":
                self.export_comparison_report(pdf, time_period)
            
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"Expense_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            
            if file_path:
                pdf.output(file_path)
                messagebox.showinfo("Success", f"Report successfully exported to:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export report: {str(e)}")

    def export_category_report(self, pdf, time_period):
        # Get date range
        start_date, end_date = self.get_date_range()
        
        if start_date is None or end_date is None:
            raise ValueError("Invalid date range")
        
        # Get category data
        self.cursor.execute('''
            SELECT category, SUM(amount) as total 
            FROM expenses 
            WHERE user_id=? AND date BETWEEN ? AND ? AND is_deleted=0
            GROUP BY category 
            ORDER BY total DESC
        ''', (self.current_user[0], start_date, end_date))
        
        data = self.cursor.fetchall()
        
        if not data:
            pdf.cell(200, 10, txt="No expense data available for the selected period", ln=1)
            return
        
        # Add section header
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Expenses by Category", ln=1)
        pdf.set_font("Arial", size=12)
        
        # Calculate total expenses
        total = sum(item[1] for item in data)
        
        # Add summary
        pdf.cell(200, 10, txt=f"Date Range: {start_date} to {end_date}", ln=1)
        pdf.cell(200, 10, txt=f"Total Expenses: PKR {total:,.2f}", ln=1)
        pdf.ln(5)
        
        # Create table header
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(90, 10, "Category", border=1)
        pdf.cell(50, 10, "Amount", border=1)
        pdf.cell(50, 10, "Percentage", border=1)
        pdf.ln()
        pdf.set_font("Arial", size=12)
        
        # Add table rows
        for category, amount in data:
            percentage = (amount / total) * 100 if total > 0 else 0
            
            pdf.cell(90, 10, category, border=1)
            pdf.cell(50, 10, f"PKR {amount:,.2f}", border=1)
            pdf.cell(50, 10, f"{percentage:.1f}%", border=1)
            pdf.ln()
        
        pdf.ln(10)
        
        # Add pie chart (simple representation)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Expense Distribution:", ln=1)
        pdf.set_font("Arial", size=10)
        
        for category, amount in data:
            percentage = (amount / total) * 100 if total > 0 else 0
            pdf.cell(200, 10, txt=f"{category}: {percentage:.1f}% (PKR {amount:,.2f})", ln=1)

    def export_period_report(self, pdf, time_period):
        now = datetime.datetime.now()
        
        if time_period == "month":
            # Monthly breakdown for the year
            months = []
            totals = []
            
            for i in range(1, 13):
                month = f"{now.year}-{i:02d}"
                months.append(datetime.datetime.strptime(month, "%Y-%m").strftime("%b %Y"))
                
                self.cursor.execute('''
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM expenses 
                    WHERE user_id=? AND strftime('%Y-%m', date)=? AND is_deleted=0
                ''', (self.current_user[0], month))
                
                totals.append(self.cursor.fetchone()[0])
            
            # Add section header
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt="Monthly Expenses", ln=1)
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Year: {now.year}", ln=1)
            pdf.ln(5)
            
            # Create table header
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(100, 10, "Month", border=1)
            pdf.cell(90, 10, "Amount", border=1)
            pdf.ln()
            pdf.set_font("Arial", size=12)
            
            # Add table rows
            for month, amount in zip(months, totals):
                pdf.cell(100, 10, month, border=1)
                pdf.cell(90, 10, f"PKR {amount:,.2f}", border=1)
                pdf.ln()
            
            # Add summary
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(100, 10, "Total:", border=1)
            pdf.cell(90, 10, f"PKR {sum(totals):,.2f}", border=1)
            pdf.ln()
            
        elif time_period == "quarter":
            # Quarterly breakdown
            quarters = []
            totals = []
            
            for q in range(1, 5):
                start_month = (q-1)*3 + 1
                end_month = q*3
                
                start_date = f"{now.year}-{start_month:02d}-01"
                end_date = f"{now.year}-{end_month:02d}-{31 if end_month in [1,3,5,7,8,10,12] else 30}"
                
                quarters.append(f"Q{q} {now.year}")
                
                self.cursor.execute('''
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM expenses 
                    WHERE user_id=? AND date BETWEEN ? AND ? AND is_deleted=0
                ''', (self.current_user[0], start_date, end_date))
                
                totals.append(self.cursor.fetchone()[0])
            
            # Add section header
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt="Quarterly Expenses", ln=1)
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Year: {now.year}", ln=1)
            pdf.ln(5)
            
            # Create table header
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(100, 10, "Quarter", border=1)
            pdf.cell(90, 10, "Amount", border=1)
            pdf.ln()
            pdf.set_font("Arial", size=12)
            
            # Add table rows
            for quarter, amount in zip(quarters, totals):
                pdf.cell(100, 10, quarter, border=1)
                pdf.cell(90, 10, f"PKR {amount:,.2f}", border=1)
                pdf.ln()
            
            # Add summary
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(100, 10, "Total:", border=1)
            pdf.cell(90, 10, f"PKR {sum(totals):,.2f}", border=1)
            pdf.ln()
            
        elif time_period == "year":
            # Yearly breakdown for last 5 years
            years = []
            totals = []
            
            for y in range(now.year-4, now.year+1):
                years.append(str(y))
                
                self.cursor.execute('''
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM expenses 
                    WHERE user_id=? AND strftime('%Y', date)=? AND is_deleted=0
                ''', (self.current_user[0], str(y)))
                
                totals.append(self.cursor.fetchone()[0])
            
            # Add section header
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt="Yearly Expenses", ln=1)
            pdf.set_font("Arial", size=12)
            pdf.ln(5)
            
            # Create table header
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(100, 10, "Year", border=1)
            pdf.cell(90, 10, "Amount", border=1)
            pdf.ln()
            pdf.set_font("Arial", size=12)
            
            # Add table rows
            for year, amount in zip(years, totals):
                pdf.cell(100, 10, year, border=1)
                pdf.cell(90, 10, f"PKR {amount:,.2f}", border=1)
                pdf.ln()
            
            # Add summary
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(100, 10, "5-Year Total:", border=1)
            pdf.cell(90, 10, f"PKR {sum(totals):,.2f}", border=1)
            pdf.ln()
            
        elif time_period == "custom":
            # Custom date range
            start_date = self.from_date.get()
            end_date = self.to_date.get()
            
            # Get daily expenses
            self.cursor.execute('''
                SELECT date, SUM(amount) 
                FROM expenses 
                WHERE user_id=? AND date BETWEEN ? AND ? AND is_deleted=0
                GROUP BY date 
                ORDER BY date
            ''', (self.current_user[0], start_date, end_date))
            
            data = self.cursor.fetchall()
            
            if not data:
                pdf.cell(200, 10, txt="No expense data available for the selected period", ln=1)
                return
            
            # Add section header
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt="Daily Expenses", ln=1)
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"From: {start_date} To: {end_date}", ln=1)
            pdf.ln(5)
            
            # Create table header
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(70, 10, "Date", border=1)
            pdf.cell(60, 10, "Day", border=1)
            pdf.cell(60,  10, "Amount", border=1)
            pdf.ln()
            pdf.set_font("Arial", size=12)
            
            # Add table rows
            total = 0
            for date_str, amount in data:
                date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                formatted_date = date.strftime("%d %b %Y")
                day_name = date.strftime("%A")
                
                pdf.cell(70, 10, formatted_date, border=1)
                pdf.cell(60, 10, day_name, border=1)
                pdf.cell(60, 10, f"PKR {amount:,.2f}", border=1)
                pdf.ln()
                total += amount
            
            # Add summary
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(130, 10, "Total:", border=1)
            pdf.cell(60, 10, f"PKR {total:,.2f}", border=1)
            pdf.ln()

    def export_comparison_report(self, pdf, time_period):
        now = datetime.datetime.now()
        
        # Get previous period
        if time_period == "month":
            current_start = f"{now.year}-{now.month:02d}-01"
            current_end = now.strftime("%Y-%m-%d")
            
            prev_month = now - datetime.timedelta(days=30)
            prev_start = f"{prev_month.year}-{prev_month.month:02d}-01"
            prev_end = prev_month.strftime("%Y-%m-%d")
            
            labels = [now.strftime("%B %Y"), prev_month.strftime("%B %Y")]
            
        elif time_period == "quarter":
            current_quarter = (now.month - 1) // 3 + 1
            current_start_month = (current_quarter - 1) * 3 + 1
            current_start = f"{now.year}-{current_start_month:02d}-01"
            current_end = now.strftime("%Y-%m-%d")
            
            prev_quarter = current_quarter - 1 if current_quarter > 1 else 4
            prev_year = now.year if current_quarter > 1 else now.year - 1
            prev_start_month = (prev_quarter - 1) * 3 + 1
            prev_start = f"{prev_year}-{prev_start_month:02d}-01"
            prev_end = f"{prev_year}-{prev_start_month+2:02d}-{31 if prev_start_month+2 in [1,3,5,7,8,10,12] else 30}"
            
            labels = [f"Q{current_quarter} {now.year}", f"Q{prev_quarter} {prev_year}"]
            
        elif time_period == "year":
            current_start = f"{now.year}-01-01"
            current_end = now.strftime("%Y-%m-%d")
            
            prev_start = f"{now.year-1}-01-01"
            prev_end = f"{now.year-1}-12-31"
            
            labels = [str(now.year), str(now.year-1)]
            
        elif time_period == "custom":
            current_start = self.from_date.get()
            current_end = self.to_date.get()
            
            # Calculate previous period
            start_date = datetime.datetime.strptime(current_start, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(current_end, "%Y-%m-%d")
            delta = end_date - start_date
            
            prev_start_date = start_date - delta - datetime.timedelta(days=1)
            prev_end_date = start_date - datetime.timedelta(days=1)
            
            prev_start = prev_start_date.strftime("%Y-%m-%d")
            prev_end = prev_end_date.strftime("%Y-%m-%d")
            
            labels = [
                f"{start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}",
                f"{prev_start_date.strftime('%d %b %Y')} to {prev_end_date.strftime('%d %b %Y')}"
            ]
        
        # Get data for both periods
        periods = [
            (current_start, current_end),
            (prev_start, prev_end)
        ]
        
        categories = set()
        data = {}
        
        for i, (start, end) in enumerate(periods):
            self.cursor.execute('''
                SELECT category, SUM(amount) 
                FROM expenses 
                WHERE user_id=? AND date BETWEEN ? AND ? AND is_deleted=0
                GROUP BY category
            ''', (self.current_user[0], start, end))
            
            results = self.cursor.fetchall()
            data[labels[i]] = {}
            
            for category, amount in results:
                data[labels[i]][category] = amount
                categories.add(category)
        
        # Add section header
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Expense Comparison", ln=1)
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Comparing: {labels[0]} vs {labels[1]}", ln=1)
        pdf.ln(5)
        
        # Create table header
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(90, 10, "Category", border=1)
        pdf.cell(50, 10, labels[0], border=1)
        pdf.cell(50, 10, labels[1], border=1)
        pdf.ln()
        pdf.set_font("Arial", size=12)
        
        # Add table rows
        for category in sorted(categories):
            current_amount = data[labels[0]].get(category, 0)
            prev_amount = data[labels[1]].get(category, 0)
            difference = current_amount - prev_amount
            change = (difference / prev_amount * 100) if prev_amount != 0 else float('inf')
            
            pdf.cell(90, 10, category, border=1)
            pdf.cell(50, 10, f"PKR {current_amount:,.2f}", border=1)
            pdf.cell(50, 10, f"PKR {prev_amount:,.2f}", border=1)
            pdf.ln()
            
            # Add change indicator
            pdf.set_font("Arial", size=10)
            if difference > 0:
                pdf.cell(90, 10, "")
                pdf.cell(50, 10, f"Increased by PKR {difference:,.2f}", border=1)
                pdf.cell(50, 10, f"{change:.1f}%", border=1)
            elif difference < 0:
                pdf.cell(90, 10, "")
                pdf.cell(50, 10, f"Decreased by PKR {abs(difference):,.2f}", border=1)
                pdf.cell(50, 10, f"{abs(change):.1f}%", border=1)
            else:
                pdf.cell(90, 10, "")
                pdf.cell(50, 10, "No change", border=1)
                pdf.cell(50, 10, "0%", border=1)
            
            pdf.ln()
            pdf.set_font("Arial", size=12)
        
        # Add totals
        current_total = sum(data[labels[0]].values())
        prev_total = sum(data[labels[1]].values())
        total_diff = current_total - prev_total
        total_change = (total_diff / prev_total * 100) if prev_total != 0 else float('inf')
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(90, 10, "Total", border=1)
        pdf.cell(50, 10, f"PKR {current_total:,.2f}", border=1)
        pdf.cell(50, 10, f"PKR {prev_total:,.2f}", border=1)
        pdf.ln()
        
        # Add total change
        pdf.set_font("Arial", 'B', 12)
        if total_diff > 0:
            pdf.cell(90, 10, "")
            pdf.cell(50, 10, f"Increased by PKR {total_diff:,.2f}", border=1)
            pdf.cell(50, 10, f"{total_change:.1f}%", border=1)
        elif total_diff < 0:
            pdf.cell(90, 10, "")
            pdf.cell(50, 10, f"Decreased by PKR {abs(total_diff):,.2f}", border=1)
            pdf.cell(50, 10, f"{abs(total_change):.1f}%", border=1)
        else:
            pdf.cell(90, 10, "")
            pdf.cell(50, 10, "No change", border=1)
            pdf.cell(50, 10, "0%", border=1)
        
        pdf.ln()
    def show_add_goal(self):
        self.clear_main_frame()
        
        ttk.Label(self.main_frame, text="Set New Savings Goal", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        form_frame = ttk.Frame(self.main_frame)
        form_frame.pack(pady=10)
        
        # Goal name
        ttk.Label(form_frame, text="Goal Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.goal_name_entry = ttk.Entry(form_frame)
        self.goal_name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Target amount
        ttk.Label(form_frame, text="Target Amount (PKR):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        self.goal_amount_entry = ttk.Entry(form_frame)
        self.goal_amount_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Current amount
        ttk.Label(form_frame, text="Current Amount (PKR):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
        self.goal_current_entry = ttk.Entry(form_frame)
        self.goal_current_entry.grid(row=2, column=1, padx=5, pady=5)
        self.goal_current_entry.insert(0, "0")
        
        # Target date
        ttk.Label(form_frame, text="Target Date:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
        self.goal_date_entry = ttk.Entry(form_frame)
        self.goal_date_entry.grid(row=3, column=1, padx=5, pady=5)
        self.goal_date_entry.insert(0, (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d"))
        
        # Buttons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Save", command=self.save_goal).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.show_dashboard).pack(side=tk.LEFT, padx=5)
    
    def save_goal(self):
        try:
            name = self.goal_name_entry.get()
            target = float(self.goal_amount_entry.get())
            current = float(self.goal_current_entry.get())
            date = self.goal_date_entry.get()
            
            # Validate date
            try:
                datetime.datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD")
                return
            
            if target <= 0:
                messagebox.showerror("Error", "Target amount must be positive")
                return
            
            if current < 0:
                messagebox.showerror("Error", "Current amount cannot be negative")
                return
            
            if current > target:
                messagebox.showerror("Error", "Current amount cannot exceed target amount")
                return
            
            if not name:
                messagebox.showerror("Error", "Goal name is required")
                return
            
            # Save goal
            self.cursor.execute('''
                INSERT INTO goals (user_id, goal_name, target_amount, current_amount, target_date, created_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.current_user[0], name, target, current, date, datetime.datetime.now().strftime("%Y-%m-%d")))
            
            self.conn.commit()
            
            messagebox.showinfo("Success", "Goal saved successfully")
            self.show_goals()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid amount. Please enter a number")
    
    def show_goals(self):
        self.clear_main_frame()
        
        ttk.Label(self.main_frame, text="Your Savings Goals", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        # Get goals
        self.cursor.execute('''
            SELECT goal_id, goal_name, target_amount, current_amount, target_date, is_completed 
            FROM goals 
            WHERE user_id=?
            ORDER BY is_completed, target_date
        ''', (self.current_user[0],))
        
        goals = self.cursor.fetchall()
        
        if not goals:
            ttk.Label(self.main_frame, text="You don't have any savings goals yet.").pack()
            ttk.Button(self.main_frame, text="Add New Goal", command=self.show_add_goal).pack(pady=5)
            ttk.Button(self.main_frame, text="Back", command=self.show_dashboard).pack(pady=5)
            return
        
        # Create a frame for each goal
        for goal in goals:
            goal_id, name, target, current, target_date, is_completed = goal
            
            goal_frame = ttk.Frame(self.main_frame, relief=tk.RIDGE, borderwidth=2)
            goal_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # Goal info
            info_frame = ttk.Frame(goal_frame)
            info_frame.pack(fill=tk.X, padx=5, pady=5)
            
            ttk.Label(info_frame, text=name, font=('Helvetica', 10, 'bold')).pack(anchor=tk.W)
            
            # Progress bar
            progress = current / target if target > 0 else 0
            progress_bar = ttk.Progressbar(info_frame, orient=tk.HORIZONTAL, length=200, mode='determinate')
            progress_bar.pack(fill=tk.X, pady=5)
            progress_bar['value'] = progress * 100
            
            # Details
            details_frame = ttk.Frame(info_frame)
            details_frame.pack(fill=tk.X)
            
            ttk.Label(details_frame, text=f"PKR {current:,.2f} of PKR {target:,.2f}").pack(side=tk.LEFT)
            ttk.Label(details_frame, text=f"{progress*100:.1f}%").pack(side=tk.LEFT, padx=10)
            
            # Target date
            try:
                formatted_date = datetime.datetime.strptime(target_date, "%Y-%m-%d").strftime("%d %b %Y")
                days_left = (datetime.datetime.strptime(target_date, "%Y-%m-%d") - datetime.datetime.now()).days
                date_text = f"Target: {formatted_date} ({days_left} days left)"
            except ValueError:
                date_text = "Target: No date set"
            
            ttk.Label(info_frame, text=date_text).pack(anchor=tk.W)
            
            # Action buttons
            action_frame = ttk.Frame(goal_frame)
            action_frame.pack(fill=tk.X, padx=5, pady=5)
            
            if not is_completed:
                ttk.Button(action_frame, text="Add Savings", 
                          command=lambda gid=goal_id: self.add_to_goal(gid)).pack(side=tk.LEFT, padx=2)
                ttk.Button(action_frame, text="Edit", 
                          command=lambda gid=goal_id: self.edit_goal(gid)).pack(side=tk.LEFT, padx=2)
                ttk.Button(action_frame, text="Complete", 
                          command=lambda gid=goal_id: self.complete_goal(gid)).pack(side=tk.LEFT, padx=2)
            else:
                ttk.Label(action_frame, text="Completed!", font=('Helvetica', 9, 'bold')).pack(side=tk.LEFT, padx=2)
            
            ttk.Button(action_frame, text="Delete", 
                      command=lambda gid=goal_id: self.delete_goal(gid)).pack(side=tk.LEFT, padx=2)
        
        # Add new goal button
        ttk.Button(self.main_frame, text="Add New Goal", command=self.show_add_goal).pack(pady=10)
        ttk.Button(self.main_frame, text="Back", command=self.show_dashboard).pack(pady=5)
    
    def add_to_goal(self, goal_id):
        # Get goal details
        self.cursor.execute('''
            SELECT goal_name, target_amount, current_amount 
            FROM goals 
            WHERE goal_id=? AND user_id=?
        ''', (goal_id, self.current_user[0]))
        
        goal = self.cursor.fetchone()
        if not goal:
            messagebox.showerror("Error", "Goal not found")
            return
        
        name, target, current = goal
        
        # Create add window
        add_window = tk.Toplevel(self.root)
        add_window.title(f"Add to Goal: {name}")
        add_window.geometry("300x200")
        
        ttk.Label(add_window, text=f"Add to {name}", font=('Helvetica', 12, 'bold')).pack(pady=10)
        
        ttk.Label(add_window, text=f"Target: PKR {target:,.2f}").pack()
        ttk.Label(add_window, text=f"Current: PKR {current:,.2f}").pack()
        
        ttk.Label(add_window, text="Amount to add:").pack(pady=5)
        amount_entry = ttk.Entry(add_window)
        amount_entry.pack()
        
        def save_addition():
            try:
                amount = float(amount_entry.get())
                
                if amount <= 0:
                    messagebox.showerror("Error", "Amount must be positive")
                    return
                
                new_current = current + amount
                
                if new_current > target:
                    if not messagebox.askyesno("Confirm", 
                                            f"Adding PKR {amount:,.2f} will exceed your target of PKR {target:,.2f}. Continue?"):
                        return
                
                # Update goal
                self.cursor.execute('''
                    UPDATE goals 
                    SET current_amount=? 
                    WHERE goal_id=?
                ''', (new_current, goal_id))

                # Also add as an expense (deduct from savings)
                now = datetime.datetime.now().strftime("%Y-%m-%d")
                self.cursor.execute('''
                    INSERT INTO expenses (user_id, amount, category, date, description)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    self.current_user[0],
                    amount,
                    "Goal",      # Use "Goal" as the category
                    now,
                    name         # Use the goal name as the description
                ))

                self.conn.commit()

                messagebox.showinfo("Success", f"Added PKR {amount:,.2f} to your goal and recorded as an expense")
                add_window.destroy()
                self.show_goals()
                
            except ValueError:
                messagebox.showerror("Error", "Invalid amount. Please enter a number")
        
        ttk.Button(add_window, text="Add", command=save_addition).pack(pady=10)
    
    def edit_goal(self, goal_id):
        # Get goal details
        self.cursor.execute('''
            SELECT goal_name, target_amount, current_amount, target_date 
            FROM goals 
            WHERE goal_id=? AND user_id=?
        ''', (goal_id, self.current_user[0]))
        
        goal = self.cursor.fetchone()
        if not goal:
            messagebox.showerror("Error", "Goal not found")
            return
        
        name, target, current, target_date = goal
        
        # Create edit window
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Edit Goal: {name}")
        edit_window.geometry("400x300")
        
        ttk.Label(edit_window, text="Edit Goal", font=('Helvetica', 12, 'bold')).pack(pady=10)
        
        form_frame = ttk.Frame(edit_window)
        form_frame.pack(pady=10)
        
        # Goal name
        ttk.Label(form_frame, text="Goal Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        name_entry = ttk.Entry(form_frame)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        name_entry.insert(0, name)
        
        # Target amount
        ttk.Label(form_frame, text="Target Amount (PKR):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        target_entry = ttk.Entry(form_frame)
        target_entry.grid(row=1, column=1, padx=5, pady=5)
        target_entry.insert(0, target)
        
        # Current amount
        ttk.Label(form_frame, text="Current Amount (PKR):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
        current_entry = ttk.Entry(form_frame)
        current_entry.grid(row=2, column=1, padx=5, pady=5)
        current_entry.insert(0, current)
        
        # Target date
        ttk.Label(form_frame, text="Target Date:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
        date_entry = ttk.Entry(form_frame)
        date_entry.grid(row=3, column=1, padx=5, pady=5)
        date_entry.insert(0, target_date)
        
        def save_changes():
            try:
                new_name = name_entry.get()
                new_target = float(target_entry.get())
                new_current = float(current_entry.get())
                new_date = date_entry.get()
                
                # Validate date
                try:
                    datetime.datetime.strptime(new_date, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD")
                    return
                
                if new_target <= 0:
                    messagebox.showerror("Error", "Target amount must be positive")
                    return
                
                if new_current < 0:
                    messagebox.showerror("Error", "Current amount cannot be negative")
                    return
                
                if new_current > new_target:
                    if not messagebox.askyesno("Confirm", 
                                            "Current amount exceeds target amount. Continue?"):
                        return
                
                if not new_name:
                    messagebox.showerror("Error", "Goal name is required")
                    return
                
                # Update goal
                self.cursor.execute('''
                    UPDATE goals 
                    SET goal_name=?, target_amount=?, current_amount=?, target_date=? 
                    WHERE goal_id=?
                ''', (new_name, new_target, new_current, new_date, goal_id))
                
                self.conn.commit()
                
                messagebox.showinfo("Success", "Goal updated successfully")
                edit_window.destroy()
                self.show_goals()
                
            except ValueError:
                messagebox.showerror("Error", "Invalid amount. Please enter a number")
        
        ttk.Button(edit_window, text="Save", command=save_changes).pack(pady=10)
    
    def complete_goal(self, goal_id):
        if messagebox.askyesno("Confirm", "Mark this goal as completed?"):
            self.cursor.execute('''
                UPDATE goals 
                SET is_completed=1 
                WHERE goal_id=?
            ''', (goal_id,))
            
            self.conn.commit()
            
            messagebox.showinfo("Success", "Goal marked as completed")
            self.show_goals()
    
    def delete_goal(self, goal_id):
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this goal?"):
            self.cursor.execute('''
                DELETE FROM goals 
                WHERE goal_id=?
            ''', (goal_id,))
            
            self.conn.commit()
            
            messagebox.showinfo("Success", "Goal deleted")
            self.show_goals()
    
    def show_add_shared(self):
        self.clear_main_frame()
        
        ttk.Label(self.main_frame, text="Add Shared Expense", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        form_frame = ttk.Frame(self.main_frame)
        form_frame.pack(pady=10)
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.shared_desc = ttk.Entry(form_frame)
        self.shared_desc.grid(row=0, column=1, padx=5, pady=5)
        self.shared_desc.insert(0, "Lend Money")
        
        # Total amount
        ttk.Label(form_frame, text="Total Amount (PKR):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        self.shared_amount = ttk.Entry(form_frame)
        self.shared_amount.grid(row=1, column=1, padx=5, pady=5)
        
        # Date
        ttk.Label(form_frame, text="Date:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
        self.shared_date = ttk.Entry(form_frame)
        self.shared_date.grid(row=2, column=1, padx=5, pady=5)
        self.shared_date.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
        
        # Category
        ttk.Label(form_frame, text="Category:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
        self.shared_category = ttk.Combobox(form_frame)
        self.shared_category.grid(row=3, column=1, padx=5, pady=5)
        
        # Load categories
        self.cursor.execute("SELECT category_name FROM categories WHERE user_id=?", (self.current_user[0],))
        categories = [row[0] for row in self.cursor.fetchall()]
        self.shared_category['values'] = categories
        if categories:
            self.shared_category.current(0)
        
        # Friends frame
        ttk.Label(form_frame, text="Friends:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.NE)
        self.friends_frame = ttk.Frame(form_frame)
        self.friends_frame.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Default friends
        self.friends = []
        self.add_friend_row()
        
        # Add friend button
        ttk.Button(form_frame, text="Add Friend", command=self.add_friend_row).grid(row=5, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Save", command=self.save_shared).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.show_dashboard).pack(side=tk.LEFT, padx=5)
    
    def add_friend_row(self):
        row = len(self.friends)
        
        name_var = tk.StringVar()
        paid_var = tk.BooleanVar(value=False)
        
        name_entry = ttk.Entry(self.friends_frame, textvariable=name_var, width=20)
        name_entry.grid(row=row, column=0, padx=5, pady=2)
        
        paid_check = ttk.Checkbutton(self.friends_frame, text="Paid", variable=paid_var)
        paid_check.grid(row=row, column=1, padx=5, pady=2)
        
        self.friends.append((name_var, paid_var))
    
    def save_shared(self):
        try:
            description = self.shared_desc.get()
            amount = float(self.shared_amount.get())
            date = self.shared_date.get()
            category = self.shared_category.get()
            
            # Validate date
            try:
                datetime.datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD")
                return
            
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be positive")
                return
            
            if not category:
                messagebox.showerror("Error", "Category is required")
                return
            
            if len(self.friends) < 1:
                messagebox.showerror("Error", "At least one friend is required")
                return
            
            # Get friend names
            friends = []
            for name_var, paid_var in self.friends:
                name = name_var.get().strip()
                if name:
                    friends.append((name, paid_var.get()))
            
            if not friends:
                messagebox.showerror("Error", "At least one friend is required")
                return
            
            # Calculate share
            share = amount / len(friends)
            
            # Save main expense
            self.cursor.execute('''
                INSERT INTO expenses (user_id, amount, category, date, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (self.current_user[0], amount, category, date, description))
            
            expense_id = self.cursor.lastrowid
            
            # Save shared expenses
            for name, paid in friends:
                self.cursor.execute('''
                    INSERT INTO shared_expenses (expense_id, user_id, friend_name, amount_owed, is_paid)
                    VALUES (?, ?, ?, ?, ?)
                ''', (expense_id, self.current_user[0], name, share, 1 if paid else 0))
            
            self.conn.commit()
            
            messagebox.showinfo("Success", "Shared expense saved successfully")
            self.show_shared()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid amount. Please enter a number")
    
    def show_shared(self):
        self.clear_main_frame()
        
        ttk.Label(self.main_frame, text="Shared Expenses", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        # Get shared expenses
        self.cursor.execute('''
            SELECT e.expense_id, e.date, e.description, e.amount, 
                   GROUP_CONCAT(se.friend_name || ' (PKR ' || se.amount_owed || ')', ', ')
            FROM expenses e
            JOIN shared_expenses se ON e.expense_id = se.expense_id
            WHERE e.user_id=?
            GROUP BY e.expense_id
            ORDER BY e.date DESC
        ''', (self.current_user[0],))
        
        shared_expenses = self.cursor.fetchall()
        
        if not shared_expenses:
            ttk.Label(self.main_frame, text="You don't have any shared expenses yet.").pack()
            ttk.Button(self.main_frame, text="Add Shared Expense", command=self.show_add_shared).pack(pady=5)
            ttk.Button(self.main_frame, text="Back", command=self.show_dashboard).pack(pady=5)
            return
        
        # Create treeview
        columns = ("ID", "Date", "Description", "Total", "Friends", "Actions")
        self.shared_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.shared_tree.heading(col, text=col)
            self.shared_tree.column(col, width=100)
        
        self.shared_tree.column("ID", width=50)
        self.shared_tree.column("Date", width=100)
        self.shared_tree.column("Description", width=150)
        self.shared_tree.column("Total", width=100)
        self.shared_tree.column("Friends", width=200)
        self.shared_tree.column("Actions", width=100)
        
        self.shared_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Load data
        for expense in shared_expenses:
            formatted_date = datetime.datetime.strptime(expense[1], "%Y-%m-%d").strftime("%d %b %Y")
            self.shared_tree.insert("", tk.END, values=(
                expense[0],
                formatted_date,
                expense[2] if expense[2] else "",
                f"PKR {expense[3]:,.2f}",
                expense[4],
                "View | Delete"
            ))
        
        # Action buttons
        action_frame = ttk.Frame(self.main_frame)
        action_frame.pack(pady=5)
        
        ttk.Button(action_frame, text="View Details", command=self.view_shared_details).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Delete", command=self.delete_shared).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Add New", command=self.show_add_shared).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Back", command=self.show_dashboard).pack(side=tk.LEFT, padx=5)
    
    def view_shared_details(self):
        selected = self.shared_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a shared expense to view")
            return

        item = self.shared_tree.item(selected[0])
        expense_id = item['values'][0]

        # Get expense details
        self.cursor.execute('''
            SELECT e.date, e.description, e.amount, e.category 
            FROM expenses e 
            WHERE e.expense_id=?
        ''', (expense_id,))

        expense = self.cursor.fetchone()

        # Get shared details
        self.cursor.execute('''
            SELECT friend_name, amount_owed, is_paid 
            FROM shared_expenses 
            WHERE expense_id=?
            ORDER BY friend_name
        ''', (expense_id,))

        friends = self.cursor.fetchall()

        # Create details window
        detail_window = tk.Toplevel(self.root)
        detail_window.title("Shared Expense Details")
        detail_window.geometry("500x400")

        ttk.Label(detail_window, text="Shared Expense Details", font=('Helvetica', 12, 'bold')).pack(pady=10)

        # Main info
        info_frame = ttk.Frame(detail_window)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        formatted_date = datetime.datetime.strptime(expense[0], "%Y-%m-%d").strftime("%d %b %Y")

        ttk.Label(info_frame, text=f"Date: {formatted_date}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Description: {expense[1] if expense[1] else 'None'}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Category: {expense[3]}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Total Amount: PKR {expense[2]:,.2f}").pack(anchor=tk.W)

        # Friends list
        ttk.Label(detail_window, text="Friends:", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W, padx=10, pady=5)

        tree_frame = ttk.Frame(detail_window)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("Friend", "Amount", "Status")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=5)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        tree.column("Friend", width=150)
        tree.column("Amount", width=100)
        tree.column("Status", width=100)

        tree.pack(fill=tk.BOTH, expand=True)

        for friend in friends:
            tree.insert("", tk.END, values=(
                friend[0],
                f"PKR {friend[1]:,.2f}",
                "Paid" if friend[2] else "Unpaid"
            ))

        # Mark as paid button
        def mark_paid():
            selected_friend = tree.selection()
            if not selected_friend:
                messagebox.showwarning("Warning", "Please select a friend to mark as paid")
                return

            friend_name = tree.item(selected_friend[0])['values'][0]

            # Mark as paid in shared_expenses
            self.cursor.execute('''
                UPDATE shared_expenses 
                SET is_paid=1 
                WHERE expense_id=? AND friend_name=?
            ''', (expense_id, friend_name))

            # Get the amount owed for this friend and expense
            self.cursor.execute('''
                SELECT amount_owed FROM shared_expenses
                WHERE expense_id=? AND friend_name=?
            ''', (expense_id, friend_name))
            row = self.cursor.fetchone()
            if row:
                amount_owed = row[0]
                now = datetime.datetime.now()
                # Subtract from expenses by adding a negative expense (this increases savings)
                self.cursor.execute('''
                    INSERT INTO expenses (user_id, amount, category, date, description)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    self.current_user[0],
                    -amount_owed,
                    "Reimbursement",
                    now.strftime("%Y-%m-%d"),
                    f"Reimbursement from {friend_name}"
                ))
            self.conn.commit()

            messagebox.showinfo("Success", f"Marked {friend_name} as paid")
            detail_window.destroy()
            self.show_dashboard()  # Refresh dashboard and challenge bar

        ttk.Button(detail_window, text="Mark as Paid", command=mark_paid).pack(pady=10)
    
    def delete_shared(self):
        selected = self.shared_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a shared expense to delete")
            return
        
        item = self.shared_tree.item(selected[0])
        expense_id = item['values'][0]
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this shared expense?"):
            # Delete from shared_expenses first
            self.cursor.execute('''
                DELETE FROM shared_expenses 
                WHERE expense_id=?
            ''', (expense_id,))
            
            # Then delete from expenses
            self.cursor.execute('''
                DELETE FROM expenses 
                WHERE expense_id=?
            ''', (expense_id,))
            
            self.conn.commit()
            
            messagebox.showinfo("Success", "Shared expense deleted")
            self.show_shared()
    
    def manage_categories(self):
        self.clear_main_frame()
        
        ttk.Label(self.main_frame, text="Manage Categories", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        # Get categories
        self.cursor.execute('''
            SELECT category_name, monthly_limit, is_locked 
            FROM categories 
            WHERE user_id=?
            ORDER BY category_name
        ''', (self.current_user[0],))
        
        categories = self.cursor.fetchall()
        
        # Treeview for categories
        columns = ("Category", "Monthly Limit", "Status", "Actions")
        self.category_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.category_tree.heading(col, text=col)
            self.category_tree.column(col, width=100)
        
        self.category_tree.column("Category", width=150)
        self.category_tree.column("Monthly Limit", width=150)
        self.category_tree.column("Status", width=100)
        self.category_tree.column("Actions", width=100)
        
        self.category_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Load data
        for category in categories:
            status = "Locked" if category[2] else "Active"
            limit = f"PKR {category[1]:,.2f}" if category[1] else "No limit"
            self.category_tree.insert("", tk.END, values=(
                category[0],
                limit,
                status,
                "Edit | Delete"
            ))
        
        # Action buttons
        action_frame = ttk.Frame(self.main_frame)
        action_frame.pack(pady=5)
        
        ttk.Button(action_frame, text="Add Category", command=self.add_category).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Edit", command=self.edit_category).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Delete", command=self.delete_category).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Unlock All", command=self.unlock_all_categories).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Back", command=self.show_dashboard).pack(side=tk.LEFT, padx=5)
    
    def add_category(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("Add New Category")
        add_window.geometry("300x200")
        
        ttk.Label(add_window, text="Add New Category", font=('Helvetica', 12, 'bold')).pack(pady=10)
        
        form_frame = ttk.Frame(add_window)
        form_frame.pack(pady=10)
        
        # Category name
        ttk.Label(form_frame, text="Category Name:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        name_entry = ttk.Entry(form_frame)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Monthly limit
        ttk.Label(form_frame, text="Monthly Limit:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        limit_entry = ttk.Entry(form_frame)
        limit_entry.grid(row=1, column=1, padx=5, pady=5)
        limit_entry.insert(0, "0")
        
        def save_category():
            name = name_entry.get().strip()
            limit = limit_entry.get()
            
            if not name:
                messagebox.showerror("Error", "Category name is required")
                return
            
            try:
                limit_value = float(limit)
                if limit_value < 0:
                    messagebox.showerror("Error", "Limit cannot be negative")
                    return
            except ValueError:
                messagebox.showerror("Error", "Invalid limit amount. Please enter a number")
                return
            
            # Save category
            try:
                self.cursor.execute('''
                    INSERT INTO categories (user_id, category_name, monthly_limit)
                    VALUES (?, ?, ?)
                ''', (self.current_user[0], name, limit_value if limit_value > 0 else None))
                
                self.conn.commit()
                
                messagebox.showinfo("Success", "Category added successfully")
                add_window.destroy()
                self.manage_categories()
                
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Category already exists")
        
        ttk.Button(add_window, text="Save", command=save_category).pack(pady=10)
    
    def edit_category(self):
        selected = self.category_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a category to edit")
            return
        
        item = self.category_tree.item(selected[0])
        category_name = item['values'][0]
        
        # Get category details
        self.cursor.execute('''
            SELECT monthly_limit, is_locked 
            FROM categories 
            WHERE user_id=? AND category_name=?
        ''', (self.current_user[0], category_name))
        
        category = self.cursor.fetchone()
        
        # Create edit window
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Edit Category: {category_name}")
        edit_window.geometry("300x200")
        
        ttk.Label(edit_window, text=f"Edit Category: {category_name}", font=('Helvetica', 12, 'bold')).pack(pady=10)
        
        form_frame = ttk.Frame(edit_window)
        form_frame.pack(pady=10)
        
        # Monthly limit
        ttk.Label(form_frame, text="Monthly Limit:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        limit_entry = ttk.Entry(form_frame)
        limit_entry.grid(row=0, column=1, padx=5, pady=5)
        limit_entry.insert(0, category[0] if category[0] else "0")
        
        # Lock status
        lock_var = tk.BooleanVar(value=bool(category[1]))
        ttk.Checkbutton(form_frame, text="Lock Category", variable=lock_var).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        def save_changes():
            limit = limit_entry.get()
            
            try:
                limit_value = float(limit)
                if limit_value < 0:
                    messagebox.showerror("Error", "Limit cannot be negative")
                    return
            except ValueError:
                messagebox.showerror("Error", "Invalid limit amount. Please enter a number")
                return
            
            # Update category
            self.cursor.execute('''
                UPDATE categories 
                SET monthly_limit=?, is_locked=? 
                WHERE user_id=? AND category_name=?
            ''', (limit_value if limit_value > 0 else None, 1 if lock_var.get() else 0, 
                 self.current_user[0], category_name))
            
            self.conn.commit()
            
            messagebox.showinfo("Success", "Category updated successfully")
            edit_window.destroy()
            self.manage_categories()
        
        ttk.Button(edit_window, text="Save", command=save_changes).pack(pady=10)
    
    def delete_category(self):
        selected = self.category_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a category to delete")
            return
        
        item = self.category_tree.item(selected[0])
        category_name = item['values'][0]
        
        # Check if category is used in expenses
        self.cursor.execute('''
            SELECT COUNT(*) 
            FROM expenses 
            WHERE user_id=? AND category=? AND is_deleted=0
        ''', (self.current_user[0], category_name))
        
        count = self.cursor.fetchone()[0]
        
        if count > 0:
            messagebox.showerror("Error", f"Cannot delete '{category_name}' as it is used in {count} expense(s)")
            return
        
        if messagebox.askyesno("Confirm", f"Are you sure you want to delete the '{category_name}' category?"):
            self.cursor.execute('''
                DELETE FROM categories 
                WHERE user_id=? AND category_name=?
            ''', (self.current_user[0], category_name))
            
            self.conn.commit()
            
            messagebox.showinfo("Success", "Category deleted")
            self.manage_categories()
    
    def unlock_all_categories(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to unlock all categories?"):
            self.cursor.execute('''
                UPDATE categories 
                SET is_locked=0 
                WHERE user_id=?
            ''', (self.current_user[0],))
            
            self.conn.commit()
            
            messagebox.showinfo("Success", "All categories unlocked")
            self.manage_categories()
    
    def manage_budget(self):
        self.clear_main_frame()
        
        ttk.Label(self.main_frame, text="Manage Budget", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        # Get current month and year
        now = datetime.datetime.now()
        current_month = now.strftime("%Y-%m")
        
        # Get current budget
        self.cursor.execute('''
            SELECT amount 
            FROM budgets 
            WHERE user_id=? AND month_year=?
        ''', (self.current_user[0], current_month))
        
        budget = self.cursor.fetchone()
        current_budget = budget[0] if budget else 0
        
        # Budget form
        form_frame = ttk.Frame(self.main_frame)
        form_frame.pack(pady=10)
        
        ttk.Label(form_frame, text=f"Budget for {now.strftime('%B %Y')}:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.budget_entry = ttk.Entry(form_frame)
        self.budget_entry.grid(row=0, column=1, padx=5, pady=5)
        self.budget_entry.insert(0, current_budget)
        
        # Buttons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Save", command=self.save_budget).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Back", command=self.show_dashboard).pack(side=tk.LEFT, padx=5)
        
        # Budget history
        ttk.Label(self.main_frame, text="Budget History", font=('Helvetica', 12, 'bold')).pack(pady=10)
        
        # Get budget history
        self.cursor.execute('''
            SELECT month_year, amount 
            FROM budgets 
            WHERE user_id=?
            ORDER BY month_year DESC
            LIMIT 12
        ''', (self.current_user[0],))
        
        history = self.cursor.fetchall()
        
        if not history:
            ttk.Label(self.main_frame, text="No budget history available").pack()
            return
        
        # Create treeview
        columns = ("Month", "Budget Amount", "Actual Expenses", "Difference")
        history_tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=min(len(history), 10))
        
        for col in columns:
            history_tree.heading(col, text=col)
            history_tree.column(col, width=100, anchor=tk.CENTER)
        
        history_tree.column("Month", width=150)
        history_tree.column("Budget Amount", width=150)
        history_tree.column("Actual Expenses", width=150)
        history_tree.column("Difference", width=150)
        
        history_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Load data
        for month_year, amount in history:
            month = datetime.datetime.strptime(month_year, "%Y-%m").strftime("%B %Y")
            
            # Get actual expenses
            self.cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) 
                FROM expenses 
                WHERE user_id=? AND strftime('%Y-%m', date)=? AND is_deleted=0
            ''', (self.current_user[0], month_year))
            
            actual = self.cursor.fetchone()[0]
            difference = amount - actual
            
            history_tree.insert("", tk.END, values=(
                month,
                f"PKR {amount:,.2f}",
                f"PKR {actual:,.2f}",
                f"PKR {difference:,.2f}",
            ))
    
    def start_budget(self):
        now = datetime.datetime.now()
        current_month = now.strftime("%Y-%m")
    
        self.budget_frame = ttk.Frame(self.root, padding="20")
        self.budget_frame.pack(expand=True)
    
        ttk.Label(self.budget_frame, text="Add Budget", font=('Helvetica', 14, 'bold')).pack(pady=10)
        ttk.Label(self.budget_frame, text=f"Budget for {now.strftime('%B %Y')}:").pack(pady=5)
    
        entry_frame = ttk.Frame(self.budget_frame)
        entry_frame.pack(pady=10)
        ttk.Label(entry_frame, text="Amount (PKR):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.budget_entry = ttk.Entry(entry_frame)
        self.budget_entry.grid(row=0, column=1, padx=5, pady=5)
    
        button_frame = ttk.Frame(self.budget_frame)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Save", command=self.save_first_budget).pack(side=tk.LEFT, padx=5)
        
    def save_first_budget(self):
        try:
            amount = float(self.budget_entry.get())
            
            if amount < 0:
                messagebox.showerror("Error", "Budget cannot be negative")
                return
            
            # Get current month and year
            now = datetime.datetime.now()
            month_year = now.strftime("%Y-%m")
            
            # Save or update budget
            self.cursor.execute('''
                INSERT OR REPLACE INTO budgets (user_id, month_year, amount)
                VALUES (?, ?, ?)
            ''', (self.current_user[0], month_year, amount))
            
            self.conn.commit()
            
            messagebox.showinfo("Success", "Budget saved successfully")
            self.create_main_interface()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid amount. Please enter a number")
        
    def save_budget(self):
        try:
            amount = float(self.budget_entry.get())
            
            if amount < 0:
                messagebox.showerror("Error", "Budget cannot be negative")
                return
            
            # Get current month and year
            now = datetime.datetime.now()
            month_year = now.strftime("%Y-%m")
            
            # Save or update budget
            self.cursor.execute('''
                INSERT OR REPLACE INTO budgets (user_id, month_year, amount)
                VALUES (?, ?, ?)
            ''', (self.current_user[0], month_year, amount))
            
            self.conn.commit()
            
            messagebox.showinfo("Success", "Budget saved successfully")
            self.show_dashboard()
            
        except ValueError:
            messagebox.showerror("Error", "Invalid amount. Please enter a number")
    
    def manage_challenges(self):
        self.clear_main_frame()
        
        ttk.Label(self.main_frame, text="Monthly Challenges", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        # --- AUTO-UPDATE CHALLENGE PROGRESS ---
        now = datetime.datetime.now()
        current_month = now.strftime("%Y-%m")
        # Get all current month challenges
        self.cursor.execute('''
            SELECT challenge_id, category FROM challenges
            WHERE user_id=? AND strftime('%Y-%m', start_date) <= ? AND strftime('%Y-%m', end_date) >= ?
        ''', (self.current_user[0], current_month, current_month))
        challenges = self.cursor.fetchall()
        for challenge_id, category in challenges:
            # Sum only positive expenses for this category in this month
            self.cursor.execute('''
                SELECT COALESCE(SUM(amount), 0)
                FROM expenses
                WHERE user_id=? AND category=? AND strftime('%Y-%m', date)=? AND is_deleted=0 AND amount > 0
            ''', (self.current_user[0], category, current_month))
            spent = self.cursor.fetchone()[0]
            self.cursor.execute('''
                UPDATE challenges SET current_amount=?
                WHERE challenge_id=?
            ''', (spent, challenge_id))
        self.conn.commit()
        # --- END AUTO-UPDATE ---
        
        # Now fetch and display challenges as before
        self.cursor.execute('''
            SELECT challenge_id, category, target_amount, current_amount, is_completed 
            FROM challenges 
            WHERE user_id=? AND strftime('%Y-%m', start_date) <= ? AND strftime('%Y-%m', end_date) >= ?
        ''', (self.current_user[0], current_month, current_month))
        challenges = self.cursor.fetchall()
        
        # Get current month challenges
        now = datetime.datetime.now()
        current_month = now.strftime("%Y-%m")
        
        self.cursor.execute('''
            SELECT challenge_id, category, target_amount, current_amount, is_completed 
            FROM challenges 
            WHERE user_id=? AND strftime('%Y-%m', start_date) <= ? AND strftime('%Y-%m', end_date) >= ?
        ''', (self.current_user[0], current_month, current_month))
        
        challenges = self.cursor.fetchall()
        
        # Create a frame for each challenge
        if challenges:
            for challenge in challenges:
                challenge_id, category, target, current, is_completed = challenge
                
                challenge_frame = ttk.Frame(self.main_frame, relief=tk.RIDGE, borderwidth=2)
                challenge_frame.pack(fill=tk.X, padx=10, pady=5)
                
                # Challenge info
                info_frame = ttk.Frame(challenge_frame)
                info_frame.pack(fill=tk.X, padx=5, pady=5)
                
                status = "Completed!" if is_completed else "In Progress"
                ttk.Label(info_frame, text=f"{category} Challenge - {status}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W)
                
                # Progress bar
                progress = current / target if target > 0 else 0
                progress_bar = ttk.Progressbar(info_frame, orient=tk.HORIZONTAL, length=200, mode='determinate')
                progress_bar.pack(fill=tk.X, pady=5)
                progress_bar['value'] = progress * 100
                
                # Details
                details_frame = ttk.Frame(info_frame)
                details_frame.pack(fill=tk.X)
                
                ttk.Label(details_frame, text=f"Spent: PKR {current:,.2f} of PKR {target:,.2f}").pack(side=tk.LEFT)
                ttk.Label(details_frame, text=f"{progress*100:.1f}%").pack(side=tk.LEFT, padx=10)
                
                # Action buttons
                action_frame = ttk.Frame(challenge_frame)
                action_frame.pack(fill=tk.X, padx=5, pady=5)
                
                if not is_completed:
                    ttk.Button(action_frame, text="Update", 
                              command=lambda cid=challenge_id: self.update_challenge(cid)).pack(side=tk.LEFT, padx=2)
                    ttk.Button(action_frame, text="Complete", 
                              command=lambda cid=challenge_id: self.complete_challenge(cid)).pack(side=tk.LEFT, padx=2)
                else:
                    ttk.Label(action_frame, text="Challenge completed!", font=('Helvetica', 9, 'bold')).pack(side=tk.LEFT, padx=2)
                
                ttk.Button(action_frame, text="Delete", 
                          command=lambda cid=challenge_id: self.delete_challenge(cid)).pack(side=tk.LEFT, padx=2)
        
        # Add new challenge button
        ttk.Button(self.main_frame, text="Add New Challenge", command=self.add_challenge).pack(pady=10)
        
        # Completed challenges button
        ttk.Button(self.main_frame, text="View Completed Challenges", command=self.view_completed_challenges).pack(pady=5)
        
        # Back button
        ttk.Button(self.main_frame, text="Back", command=self.show_dashboard).pack(pady=5)
    
    def add_challenge(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("Add New Challenge")
        add_window.geometry("400x300")
        
        ttk.Label(add_window, text="Add New Challenge", font=('Helvetica', 12, 'bold')).pack(pady=10)
        
        form_frame = ttk.Frame(add_window)
        form_frame.pack(pady=10)
        
        # Category
        ttk.Label(form_frame, text="Category:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        category_combo = ttk.Combobox(form_frame)
        category_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Load categories
        self.cursor.execute("SELECT category_name FROM categories WHERE user_id=?", (self.current_user[0],))
        categories = [row[0] for row in self.cursor.fetchall()]
        category_combo['values'] = categories
        if categories:
            category_combo.current(0)
        
        # Target amount
        ttk.Label(form_frame, text="Target Amount (PKR):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        target_entry = ttk.Entry(form_frame)
        target_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Start date
        ttk.Label(form_frame, text="Start Date:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
        start_entry = ttk.Entry(form_frame)
        start_entry.grid(row=2, column=1, padx=5, pady=5)
        start_entry.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
        
        # End date
        ttk.Label(form_frame, text="End Date:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
        end_entry = ttk.Entry(form_frame)
        end_entry.grid(row=3, column=1, padx=5, pady=5)
        end_entry.insert(0, (datetime.datetime.now() + datetime.timedelta(days=30)).strftime("%Y-%m-%d"))
        
        def save_challenge():
            try:
                category = category_combo.get()
                target = float(target_entry.get())
                start_date = start_entry.get()
                end_date = end_entry.get()
                
                # Validate dates
                try:
                    datetime.datetime.strptime(start_date, "%Y-%m-%d")
                    datetime.datetime.strptime(end_date, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD")
                    return
                
                if target <= 0:
                    messagebox.showerror("Error", "Target amount must be positive")
                    return
                
                if not category:
                    messagebox.showerror("Error", "Category is required")
                    return
                
                # Save challenge
                self.cursor.execute('''
                    INSERT INTO challenges (user_id, category, target_amount, start_date, end_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (self.current_user[0], category, target, start_date, end_date))
                
                self.conn.commit()
                
                messagebox.showinfo("Success", "Challenge added successfully")
                add_window.destroy()
                self.manage_challenges()
                
            except ValueError:
                messagebox.showerror("Error", "Invalid amount. Please enter a number")
        
        ttk.Button(add_window, text="Save", command=save_challenge).pack(pady=10)
    
    def update_challenge(self, challenge_id):
        # Get current month expenses for the challenge category
        self.cursor.execute('''
            SELECT c.category, COALESCE(SUM(e.amount), 0) 
            FROM challenges c
            LEFT JOIN expenses e ON e.user_id = c.user_id AND e.category = c.category 
                                AND strftime('%Y-%m', e.date) = strftime('%Y-%m', date('now')) 
                                AND e.is_deleted=0
            WHERE c.challenge_id=?
            GROUP BY c.category
        ''', (challenge_id,))
        
        result = self.cursor.fetchone()
        if not result:
            messagebox.showerror("Error", "Challenge not found")
            return
        
        category, current = result
        
        # Create update window
        update_window = tk.Toplevel(self.root)
        update_window.title(f"Update Challenge: {category}")
        update_window.geometry("300x200")
        
        ttk.Label(update_window, text=f"Update {category} Challenge", font=('Helvetica', 12, 'bold')).pack(pady=10)
        
        ttk.Label(update_window, text=f"Current spending: PKR {current:,.2f}").pack()
        
        ttk.Label(update_window, text="Manual adjustment:").pack(pady=5)
        adjust_entry = ttk.Entry(update_window)
        adjust_entry.pack()
        adjust_entry.insert(0, "0")
        
        def save_update():
            try:
                adjustment = float(adjust_entry.get())
                new_current = current + adjustment
                
                if new_current < 0:
                    messagebox.showerror("Error", "Amount cannot be negative")
                    return
                
                # Update challenge
                self.cursor.execute('''
                    UPDATE challenges 
                    SET current_amount=? 
                    WHERE challenge_id=?
                ''', (new_current, challenge_id))
                
                self.conn.commit()
                
                messagebox.showinfo("Success", "Challenge updated successfully")
                update_window.destroy()
                self.manage_challenges()
                
            except ValueError:
                messagebox.showerror("Error", "Invalid amount. Please enter a number")
        
        ttk.Button(update_window, text="Update", command=save_update).pack(pady=10)
    
    def complete_challenge(self, challenge_id):
        if messagebox.askyesno("Confirm", "Mark this challenge as completed?"):
            self.cursor.execute('''
                UPDATE challenges 
                SET is_completed=1 
                WHERE challenge_id=?
            ''', (challenge_id,))
            
            self.conn.commit()
            
            messagebox.showinfo("Success", "Challenge marked as completed")
            self.manage_challenges()
    
    def delete_challenge(self, challenge_id):
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this challenge?"):
            self.cursor.execute('''
                DELETE FROM challenges 
                WHERE challenge_id=?
            ''', (challenge_id,))
            
            self.conn.commit()
            
            messagebox.showinfo("Success", "Challenge deleted")
            self.manage_challenges()
    
    def view_completed_challenges(self):
        self.clear_main_frame()
        
        ttk.Label(self.main_frame, text="Completed Challenges", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        # Get completed challenges
        self.cursor.execute('''
            SELECT challenge_id, category, target_amount, current_amount, end_date 
            FROM challenges 
            WHERE user_id=? AND is_completed=1
            ORDER BY end_date DESC
        ''', (self.current_user[0],))
        
        challenges = self.cursor.fetchall()
        
        if not challenges:
            ttk.Label(self.main_frame, text="No completed challenges yet").pack()
            ttk.Button(self.main_frame, text="Back", command=self.manage_challenges).pack(pady=5)
            return
        
        # Create treeview
        columns = ("Category", "Target", "Actual", "Savings", "Completed On", "Actions")
        tree = ttk.Treeview(self.main_frame, columns=columns, show="headings", height=min(len(challenges), 10))
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor=tk.CENTER)
        
        tree.column("Category", width=150)
        tree.column("Target", width=100)
        tree.column("Actual", width=100)
        tree.column("Savings", width=100)
        tree.column("Completed On", width=150)
        tree.column("Actions", width=100)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Load data
        for challenge in challenges:
            challenge_id, category, target, current, end_date = challenge
            savings = target - current
            formatted_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").strftime("%d %b %Y")
            
            tree.insert("", tk.END, values=(
                category,
                f"PKR {target:,.2f}",
                f"PKR {current:,.2f}",
                f"PKR {savings:,.2f}",
                formatted_date,
                "Delete"
            ))
        
        # Action buttons
        action_frame = ttk.Frame(self.main_frame)
        action_frame.pack(pady=5)
        
        ttk.Button(action_frame, text="Delete Selected", 
                  command=lambda: self.delete_challenge_from_tree(tree)).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Back", command=self.manage_challenges).pack(side=tk.LEFT, padx=5)
    
    def delete_challenge_from_tree(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a challenge to delete")
            return
        
        item = tree.item(selected[0])
        challenge_id = item['values'][0]  # Assuming first column is challenge_id
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this challenge?"):
            self.cursor.execute('''
                DELETE FROM challenges 
                WHERE challenge_id=?
            ''', (challenge_id,))
            
            self.conn.commit()
            
            messagebox.showinfo("Success", "Challenge deleted")
            self.view_completed_challenges()
    
    def manage_profile(self):
        self.clear_main_frame()
        
        ttk.Label(self.main_frame, text="Your Profile", font=('Helvetica', 14, 'bold')).pack(pady=10)
        
        # Get user details
        self.cursor.execute('''
            SELECT username, email, theme 
            FROM users 
            WHERE user_id=?
        ''', (self.current_user[0],))
        
        user = self.cursor.fetchone()
        
        # Profile form
        form_frame = ttk.Frame(self.main_frame)
        form_frame.pack(pady=10)
        
        # Username
        ttk.Label(form_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        username_label = ttk.Label(form_frame, text=user[0])
        username_label.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Email
        ttk.Label(form_frame, text="Email:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        self.email_entry = ttk.Entry(form_frame)
        self.email_entry.grid(row=1, column=1, padx=5, pady=5)
        self.email_entry.insert(0, user[1] if user[1] else "")
        
        # Theme
        ttk.Label(form_frame, text="Theme:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
        self.theme_var = tk.StringVar(value=user[2])
        ttk.Radiobutton(form_frame, text="Light", variable=self.theme_var, value="light").grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Radiobutton(form_frame, text="Dark", variable=self.theme_var, value="dark").grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Change password button
        ttk.Button(form_frame, text="Change Password", command=self.change_password).grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Save", command=self.save_profile).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Back", command=self.show_dashboard).pack(side=tk.LEFT, padx=5)
    
    def save_profile(self):
        email = self.email_entry.get()
        theme = self.theme_var.get()
        
        # Update profile
        self.cursor.execute('''
            UPDATE users 
            SET email=?, theme=?
            WHERE user_id=?
        ''', (email if email else None, theme, self.current_user[0]))
        
        self.conn.commit()
        
        # Update current theme if changed
        if self.theme != theme:
            self.theme = theme
            self.apply_theme()
        
        messagebox.showinfo("Success", "Profile updated successfully")
        self.show_dashboard()
    
    def change_password(self):
        change_window = tk.Toplevel(self.root)
        change_window.title("Change Password")
        change_window.geometry("300x200")
        
        ttk.Label(change_window, text="Change Password", font=('Helvetica', 12, 'bold')).pack(pady=10)
        
        form_frame = ttk.Frame(change_window)
        form_frame.pack(pady=10)
        
        # Current password
        ttk.Label(form_frame, text="Current Password:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        current_entry = ttk.Entry(form_frame, show="*")
        current_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # New password
        ttk.Label(form_frame, text="New Password:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        new_entry = ttk.Entry(form_frame, show="*")
        new_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Confirm new password
        ttk.Label(form_frame, text="Confirm New:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
        confirm_entry = ttk.Entry(form_frame, show="*")
        confirm_entry.grid(row=2, column=1, padx=5, pady=5)
        
        def save_password():
            current = current_entry.get()
            new = new_entry.get()
            confirm = confirm_entry.get()
            
            if not current or not new or not confirm:
                messagebox.showerror("Error", "All fields are required")
                return
            
            if new != confirm:
                messagebox.showerror("Error", "New passwords do not match")
                return
            
            # Verify current password
            hashed_current = self.hash_password(current)
            self.cursor.execute('''
                SELECT password FROM users WHERE user_id=?
            ''', (self.current_user[0],))
            
            db_password = self.cursor.fetchone()[0]
            
            if hashed_current != db_password:
                messagebox.showerror("Error", "Current password is incorrect")
                return
            
            # Update password
            hashed_new = self.hash_password(new)
            self.cursor.execute('''
                UPDATE users 
                SET password=?
                WHERE user_id=?
            ''', (hashed_new, self.current_user[0]))
            
            self.conn.commit()
            
            messagebox.showinfo("Success", "Password changed successfully")
            change_window.destroy()
        
        ttk.Button(change_window, text="Save", command=save_password).pack(pady=10)
    
    def clear_main_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    def logout(self):
        self.current_user = None
        self.create_login_screen()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTracker(root)
    app.run()