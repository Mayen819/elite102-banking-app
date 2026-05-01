import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3

# connect to the local sqlite file
def get_connection():
    return sqlite3.connect("banking.db")

# create tables if they don't exist yet
def setup_database():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            balance REAL NOT NULL DEFAULT 0.0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            timestamp TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    """)
    conn.commit()
    conn.close()

# insert a new account and log the first deposit
def create_account(name, initial_deposit):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO accounts (name, balance) VALUES (?, ?)", (name, initial_deposit))
    account_id = cursor.lastrowid
    if initial_deposit > 0:
        cursor.execute(
            "INSERT INTO transactions (account_id, type, amount) VALUES (?, ?, ?)",
            (account_id, "deposit", initial_deposit)
        )
    conn.commit()
    conn.close()
    return account_id

# add money to an account
def deposit(account_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE id = ?", (account_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None, "Account not found."
    new_balance = row[0] + amount
    cursor.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_balance, account_id))
    cursor.execute(
        "INSERT INTO transactions (account_id, type, amount) VALUES (?, ?, ?)",
        (account_id, "deposit", amount)
    )
    conn.commit()
    conn.close()
    return new_balance, None

# take money out, block if not enough funds
def withdraw(account_id, amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE id = ?", (account_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None, "Account not found."
    if row[0] < amount:
        conn.close()
        return None, f"Not enough funds. Balance: ${row[0]:.2f}"
    new_balance = row[0] - amount
    cursor.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_balance, account_id))
    cursor.execute(
        "INSERT INTO transactions (account_id, type, amount) VALUES (?, ?, ?)",
        (account_id, "withdrawal", amount)
    )
    conn.commit()
    conn.close()
    return new_balance, None

# get name and balance for one account
def check_balance(account_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, balance FROM accounts WHERE id = ?", (account_id,))
    row = cursor.fetchone()
    conn.close()
    return row

# get all accounts
def list_accounts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, balance, created_at FROM accounts ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    return rows

# get all transactions for one account
def transaction_history(account_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM accounts WHERE id = ?", (account_id,))
    acct = cursor.fetchone()
    if not acct:
        conn.close()
        return None, None
    cursor.execute(
        "SELECT type, amount, timestamp FROM transactions WHERE account_id = ? ORDER BY timestamp",
        (account_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return acct[0], rows

# color palette matching the screenshot
BG     = "#0f1628"
CARD   = "#1a2340"
RED    = "#e03030"
ORANGE = "#cc8800"
GREEN  = "#5a9a00"
BLUE   = "#1a9fda"
PINK   = "#cc22cc"
GRAY   = "#4a5568"
WHITE  = "#ffffff"
SUBTEXT = "#8899aa"
TITLE1 = "#9999ee"
TITLE2 = "#cc88ff"

# rounded button using canvas trick for Mac
def rounded_button(parent, text, color, command, w=280, h=80):
    canvas = tk.Canvas(parent, width=w, height=h, bg=BG, highlightthickness=0)
    radius = 20

    # draw rounded rectangle
    canvas.create_arc(0, 0, radius*2, radius*2, start=90, extent=90, fill=color, outline=color)
    canvas.create_arc(w-radius*2, 0, w, radius*2, start=0, extent=90, fill=color, outline=color)
    canvas.create_arc(0, h-radius*2, radius*2, h, start=180, extent=90, fill=color, outline=color)
    canvas.create_arc(w-radius*2, h-radius*2, w, h, start=270, extent=90, fill=color, outline=color)
    canvas.create_rectangle(radius, 0, w-radius, h, fill=color, outline=color)
    canvas.create_rectangle(0, radius, w, h-radius, fill=color, outline=color)
    canvas.create_text(w//2, h//2, text=text, fill=WHITE,
                       font=("Helvetica", 16, "bold"))

    # make whole canvas clickable
    canvas.bind("<Button-1>", lambda e: command())
    canvas.configure(cursor="hand2")
    return canvas

# popup window base
def make_window(title, w=460, h=420):
    win = tk.Toplevel()
    win.title(title)
    win.geometry(f"{w}x{h}")
    win.configure(bg=BG)
    win.resizable(False, False)
    win.lift()
    win.focus_force()
    return win

# styled input field
def input_box(parent):
    return tk.Entry(
        parent, bg=CARD, fg=WHITE,
        insertbackground=WHITE,
        font=("Helvetica", 13),
        relief="flat", bd=12
    )

# styled submit button for popups
def submit_btn(parent, label, color, action):
    return tk.Button(
        parent, text=label, bg=color, fg=WHITE,
        font=("Helvetica", 12, "bold"),
        relief="flat", padx=16, pady=10,
        cursor="hand2",
        activebackground=color, activeforeground=WHITE,
        command=action
    )

# create account popup
def open_create_account():
    win = make_window("Create Account")
    tk.Label(win, text="Create New Account", bg=BG, fg=RED,
             font=("Helvetica", 18, "bold")).pack(pady=22)

    panel = tk.Frame(win, bg=CARD, padx=26, pady=22)
    panel.pack(fill="x", padx=26)

    tk.Label(panel, text="Full Name", bg=CARD, fg=SUBTEXT,
             font=("Helvetica", 10)).pack(anchor="w")
    name_box = input_box(panel)
    name_box.pack(fill="x", pady=(2, 14))

    tk.Label(panel, text="Initial Deposit ($)", bg=CARD, fg=SUBTEXT,
             font=("Helvetica", 10)).pack(anchor="w")
    dep_box = input_box(panel)
    dep_box.pack(fill="x", pady=(2, 4))

    status = tk.Label(win, text="", bg=BG, fg=RED, font=("Helvetica", 11))
    status.pack(pady=10)

    def submit():
        name = name_box.get().strip()
        try:
            amount = float(dep_box.get().strip())
            if not name:
                status.config(text="Name can't be blank.", fg="#e05252")
                return
            if amount < 0:
                status.config(text="Deposit can't be negative.", fg="#e05252")
                return
            aid = create_account(name, amount)
            status.config(text=f"Account created! ID: {aid}", fg=GREEN)
            name_box.delete(0, "end")
            dep_box.delete(0, "end")
        except ValueError:
            status.config(text="Enter a valid amount.", fg="#e05252")

    submit_btn(win, "Create Account", RED, submit).pack(pady=4)

# deposit popup
def open_deposit():
    win = make_window("Deposit")
    tk.Label(win, text="Deposit Funds", bg=BG, fg=ORANGE,
             font=("Helvetica", 18, "bold")).pack(pady=22)

    panel = tk.Frame(win, bg=CARD, padx=26, pady=22)
    panel.pack(fill="x", padx=26)

    tk.Label(panel, text="Account ID", bg=CARD, fg=SUBTEXT,
             font=("Helvetica", 10)).pack(anchor="w")
    id_box = input_box(panel)
    id_box.pack(fill="x", pady=(2, 14))

    tk.Label(panel, text="Amount ($)", bg=CARD, fg=SUBTEXT,
             font=("Helvetica", 10)).pack(anchor="w")
    amt_box = input_box(panel)
    amt_box.pack(fill="x", pady=(2, 4))

    status = tk.Label(win, text="", bg=BG, fg=ORANGE, font=("Helvetica", 11))
    status.pack(pady=10)

    def submit():
        try:
            aid = int(id_box.get().strip())
            amt = float(amt_box.get().strip())
            if amt <= 0:
                status.config(text="Amount must be positive.", fg="#e05252")
                return
            new_bal, err = deposit(aid, amt)
            if err:
                status.config(text=err, fg="#e05252")
            else:
                status.config(text=f"Deposited ${amt:.2f} | Balance: ${new_bal:.2f}", fg=ORANGE)
        except ValueError:
            status.config(text="Enter valid numbers.", fg="#e05252")

    submit_btn(win, "Deposit", ORANGE, submit).pack(pady=4)

# withdraw popup
def open_withdraw():
    win = make_window("Withdraw")
    tk.Label(win, text="Withdraw Funds", bg=BG, fg=GREEN,
             font=("Helvetica", 18, "bold")).pack(pady=22)

    panel = tk.Frame(win, bg=CARD, padx=26, pady=22)
    panel.pack(fill="x", padx=26)

    tk.Label(panel, text="Account ID", bg=CARD, fg=SUBTEXT,
             font=("Helvetica", 10)).pack(anchor="w")
    id_box = input_box(panel)
    id_box.pack(fill="x", pady=(2, 14))

    tk.Label(panel, text="Amount ($)", bg=CARD, fg=SUBTEXT,
             font=("Helvetica", 10)).pack(anchor="w")
    amt_box = input_box(panel)
    amt_box.pack(fill="x", pady=(2, 4))

    status = tk.Label(win, text="", bg=BG, fg=GREEN, font=("Helvetica", 11))
    status.pack(pady=10)

    def submit():
        try:
            aid = int(id_box.get().strip())
            amt = float(amt_box.get().strip())
            if amt <= 0:
                status.config(text="Amount must be positive.", fg="#e05252")
                return
            new_bal, err = withdraw(aid, amt)
            if err:
                status.config(text=err, fg="#e05252")
            else:
                status.config(text=f"Withdrew ${amt:.2f} | Balance: ${new_bal:.2f}", fg=GREEN)
        except ValueError:
            status.config(text="Enter valid numbers.", fg="#e05252")

    submit_btn(win, "Withdraw", GREEN, submit).pack(pady=4)

# check balance popup
def open_check_balance():
    win = make_window("Check Balance")
    tk.Label(win, text="Check Balance", bg=BG, fg=BLUE,
             font=("Helvetica", 18, "bold")).pack(pady=22)

    panel = tk.Frame(win, bg=CARD, padx=26, pady=22)
    panel.pack(fill="x", padx=26)

    tk.Label(panel, text="Account ID", bg=CARD, fg=SUBTEXT,
             font=("Helvetica", 10)).pack(anchor="w")
    id_box = input_box(panel)
    id_box.pack(fill="x", pady=(2, 4))

    status = tk.Label(win, text="", bg=BG, fg=BLUE,
                      font=("Helvetica", 15, "bold"))
    status.pack(pady=18)

    def submit():
        try:
            aid = int(id_box.get().strip())
            row = check_balance(aid)
            if not row:
                status.config(text="Account not found.", fg="#e05252")
            else:
                status.config(text=f"{row[0]}\n${float(row[1]):,.2f}", fg=BLUE)
        except ValueError:
            status.config(text="Enter a valid ID.", fg="#e05252")

    submit_btn(win, "Check Balance", BLUE, submit).pack(pady=4)

# all accounts table
def open_list_accounts():
    win = make_window("All Accounts", w=600, h=440)
    tk.Label(win, text="All Accounts", bg=BG, fg=PINK,
             font=("Helvetica", 18, "bold")).pack(pady=14)

    style = ttk.Style()
    style.theme_use("default")
    style.configure("Treeview",
                    background=CARD, foreground=WHITE,
                    fieldbackground=CARD,
                    rowheight=32, font=("Helvetica", 11))
    style.configure("Treeview.Heading",
                    background=GRAY, foreground=WHITE,
                    font=("Helvetica", 11, "bold"))

    cols = ("ID", "Name", "Balance", "Opened")
    tree = ttk.Treeview(win, columns=cols, show="headings", height=12)
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=140 if c != "Name" else 190, anchor="center")

    for row in list_accounts():
        tree.insert("", "end", values=(
            row[0], row[1], f"${float(row[2]):,.2f}", row[3]
        ))

    tree.pack(fill="both", expand=True, padx=18, pady=10)

# transaction history table
def open_transaction_history():
    win = make_window("Transaction History", w=560, h=460)
    tk.Label(win, text="Transaction History", bg=BG, fg=GRAY,
             font=("Helvetica", 18, "bold")).pack(pady=12)

    top = tk.Frame(win, bg=BG)
    top.pack(fill="x", padx=26)

    tk.Label(top, text="Account ID", bg=BG, fg=SUBTEXT,
             font=("Helvetica", 10)).pack(anchor="w")
    id_box = input_box(top)
    id_box.pack(fill="x", pady=(2, 8))

    style = ttk.Style()
    style.configure("Treeview",
                    background=CARD, foreground=WHITE,
                    fieldbackground=CARD,
                    rowheight=30, font=("Helvetica", 11))
    style.configure("Treeview.Heading",
                    background=GRAY, foreground=WHITE,
                    font=("Helvetica", 11, "bold"))

    cols = ("Type", "Amount", "Date & Time")
    tree = ttk.Treeview(win, columns=cols, show="headings", height=10)
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=170, anchor="center")

    def load():
        for i in tree.get_children():
            tree.delete(i)
        try:
            aid = int(id_box.get().strip())
            name, rows = transaction_history(aid)
            if name is None:
                messagebox.showerror("Not Found", "No account with that ID.")
                return
            if not rows:
                tree.insert("", "end", values=("No transactions yet", "", ""))
            else:
                for row in rows:
                    tree.insert("", "end", values=(
                        row[0], f"${float(row[1]):,.2f}", row[2]
                    ))
        except ValueError:
            messagebox.showerror("Error", "Enter a valid ID.")

    submit_btn(win, "Load History", GRAY, load).pack(pady=4)
    tree.pack(fill="both", expand=True, padx=18, pady=8)

# main window
def main():
    setup_database()

    root = tk.Tk()
    root.title("Elite 102 Bank")
    root.geometry("720x600")
    root.configure(bg=BG)
    root.resizable(False, False)

    # big gradient-style title using two colors side by side
    title_frame = tk.Frame(root, bg=BG)
    title_frame.pack(pady=(40, 6))
    tk.Label(title_frame, text="Elite 102 ", bg=BG, fg=TITLE1,
             font=("Helvetica", 38, "bold")).pack(side="left")
    tk.Label(title_frame, text="Bank", bg=BG, fg=TITLE2,
             font=("Helvetica", 38, "bold")).pack(side="left")

    tk.Label(root, text="Select an action below", bg=BG, fg=SUBTEXT,
             font=("Helvetica", 13)).pack(pady=(0, 30))

    # button grid 2 per row with rounded buttons
    menu_items = [
        ("Create Account",      RED,    open_create_account),
        ("Deposit",             ORANGE, open_deposit),
        ("Withdraw",            GREEN,  open_withdraw),
        ("Check Balance",       BLUE,   open_check_balance),
        ("List Accounts",       PINK,   open_list_accounts),
        ("Transaction History", GRAY,   open_transaction_history),
    ]

    grid_frame = tk.Frame(root, bg=BG)
    grid_frame.pack()

    for i, (label, color, cmd) in enumerate(menu_items):
        r, c = divmod(i, 2)
        btn = rounded_button(grid_frame, label, color, cmd, w=280, h=75)
        btn.grid(row=r, column=c, padx=18, pady=12)

    root.mainloop()

if __name__ == "__main__":
    main()