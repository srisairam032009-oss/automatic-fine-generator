import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta


# =========================
# DATABASE
# =========================

DB_NAME = "fines.db"

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS fines (
    fine_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT,
    vehicle_no TEXT,
    vehicle_type TEXT,
    violation TEXT,
    amount REAL,
    fine_date TEXT,
    due_date TEXT,
    status TEXT
)
""")

conn.commit()


# =========================
# FINE RULES
# =========================

FINE_RULES = {
    "No Helmet": 1000,
    "No Seat Belt": 1000,
    "Over Speeding": 2000,
    "Using Mobile While Driving": 5000,
    "Driving Without License": 5000,
    "Wrong Parking": 500,
    "Signal Jump": 1000,
    "Drunk Driving": 10000
}


# =========================
# MAIN WINDOW
# =========================

root = tk.Tk()
root.title("Automatic Fine Generator")
root.geometry("1000x700")
root.resizable(False, False)


# =========================
# VARIABLES
# =========================

name_var = tk.StringVar()
phone_var = tk.StringVar()
vehicle_no_var = tk.StringVar()
vehicle_type_var = tk.StringVar()
violation_var = tk.StringVar()
amount_var = tk.StringVar()
search_var = tk.StringVar()


# =========================
# FUNCTIONS
# =========================

def generate_fine_id():
    now = datetime.now()
    return "F" + now.strftime("%Y%m%d%H%M%S")


def calculate_fine(event=None):
    violation = violation_var.get()

    if violation in FINE_RULES:
        amount_var.set("₹ " + str(FINE_RULES[violation]))
    else:
        amount_var.set("")


def clear_fields():
    name_var.set("")
    phone_var.set("")
    vehicle_no_var.set("")
    vehicle_type_var.set("")
    violation_var.set("")
    amount_var.set("")


def generate_fine():
    name = name_var.get().strip()
    phone = phone_var.get().strip()
    vehicle_no = vehicle_no_var.get().strip()
    vehicle_type = vehicle_type_var.get().strip()
    violation = violation_var.get()

    if not name:
        messagebox.showerror("Error", "Please enter person's name")
        return

    if not vehicle_no:
        messagebox.showerror("Error", "Please enter vehicle number")
        return

    if not violation:
        messagebox.showerror("Error", "Please select a violation")
        return

    amount = FINE_RULES[violation]

    fine_id = generate_fine_id()

    fine_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    due_date = (
        datetime.now() + timedelta(days=15)
    ).strftime("%d-%m-%Y")

    try:
        cursor.execute("""
        INSERT INTO fines
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fine_id,
            name,
            phone,
            vehicle_no,
            vehicle_type,
            violation,
            amount,
            fine_date,
            due_date,
            "UNPAID"
        ))

        conn.commit()

        messagebox.showinfo(
            "Fine Generated",
            f"Fine generated successfully!\n\n"
            f"Fine ID: {fine_id}\n"
            f"Amount: ₹{amount}\n"
            f"Due Date: {due_date}"
        )

        load_data()
        clear_fields()

    except sqlite3.Error as e:
        messagebox.showerror("Database Error", str(e))


def load_data():
    for item in tree.get_children():
        tree.delete(item)

    cursor.execute("""
    SELECT fine_id, name, vehicle_no, violation,
           amount, fine_date, due_date, status
    FROM fines
    ORDER BY fine_date DESC
    """)

    rows = cursor.fetchall()

    for row in rows:
        tree.insert("", tk.END, values=row)


def search_fines():
    search = search_var.get().strip()

    for item in tree.get_children():
        tree.delete(item)

    cursor.execute("""
    SELECT fine_id, name, vehicle_no, violation,
           amount, fine_date, due_date, status
    FROM fines
    WHERE fine_id LIKE ?
       OR name LIKE ?
       OR vehicle_no LIKE ?
    ORDER BY fine_date DESC
    """, (
        "%" + search + "%",
        "%" + search + "%",
        "%" + search + "%"
    ))

    rows = cursor.fetchall()

    for row in rows:
        tree.insert("", tk.END, values=row)


def mark_paid():
    selected = tree.selection()

    if not selected:
        messagebox.showwarning(
            "Warning",
            "Please select a fine"
        )
        return

    item = tree.item(selected[0])
    fine_id = item["values"][0]

    cursor.execute("""
    UPDATE fines
    SET status = 'PAID'
    WHERE fine_id = ?
    """, (fine_id,))

    conn.commit()

    messagebox.showinfo(
        "Payment",
        "Fine marked as PAID"
    )

    load_data()


def delete_fine():
    selected = tree.selection()

    if not selected:
        messagebox.showwarning(
            "Warning",
            "Please select a fine"
        )
        return

    item = tree.item(selected[0])
    fine_id = item["values"][0]

    confirm = messagebox.askyesno(
        "Confirm Delete",
        "Are you sure you want to delete this fine?"
    )

    if confirm:
        cursor.execute("""
        DELETE FROM fines
        WHERE fine_id = ?
        """, (fine_id,))

        conn.commit()

        messagebox.showinfo(
            "Deleted",
            "Fine deleted successfully"
        )

        load_data()


def generate_receipt():
    selected = tree.selection()

    if not selected:
        messagebox.showwarning(
            "Warning",
            "Please select a fine"
        )
        return

    item = tree.item(selected[0])
    fine_id = item["values"][0]

    cursor.execute("""
    SELECT *
    FROM fines
    WHERE fine_id = ?
    """, (fine_id,))

    data = cursor.fetchone()

    if not data:
        return

    receipt = f"""
========================================
          TRAFFIC FINE RECEIPT
========================================

Fine ID       : {data[0]}

Name          : {data[1]}
Phone         : {data[2]}
Vehicle No    : {data[3]}
Vehicle Type  : {data[4]}

Violation     : {data[5]}
Fine Amount   : ₹{data[6]}

Fine Date     : {data[7]}
Due Date      : {data[8]}

Payment Status: {data[9]}

========================================
          THANK YOU
========================================
"""

    # Save receipt
    filename = f"{fine_id}_receipt.txt"

    with open(filename, "w", encoding="utf-8") as file:
        file.write(receipt)

    messagebox.showinfo(
        "Receipt Generated",
        f"Receipt saved as:\n{filename}"
    )


def show_statistics():
    cursor.execute("""
    SELECT COUNT(*), 
           COALESCE(SUM(amount), 0)
    FROM fines
    """)

    total_fines, total_amount = cursor.fetchone()

    cursor.execute("""
    SELECT COALESCE(SUM(amount), 0)
    FROM fines
    WHERE status = 'PAID'
    """)

    paid_amount = cursor.fetchone()[0]

    cursor.execute("""
    SELECT COALESCE(SUM(amount), 0)
    FROM fines
    WHERE status = 'UNPAID'
    """)

    unpaid_amount = cursor.fetchone()[0]

    messagebox.showinfo(
        "Fine Statistics",
        f"Total Fines : {total_fines}\n\n"
        f"Total Amount: ₹{total_amount}\n\n"
        f"Paid Amount : ₹{paid_amount}\n\n"
        f"Unpaid Amount: ₹{unpaid_amount}"
    )


# =========================
# TITLE
# =========================

title = tk.Label(
    root,
    text="AUTOMATIC FINE GENERATOR",
    font=("Arial", 24, "bold")
)

title.pack(pady=15)


# =========================
# INPUT FRAME
# =========================

input_frame = tk.LabelFrame(
    root,
    text="Fine Details",
    font=("Arial", 12, "bold"),
    padx=15,
    pady=15
)

input_frame.pack(
    padx=20,
    fill="x"
)


# Name
tk.Label(
    input_frame,
    text="Person Name:"
).grid(row=0, column=0, padx=10, pady=8)

tk.Entry(
    input_frame,
    textvariable=name_var,
    width=25
).grid(row=0, column=1)


# Phone
tk.Label(
    input_frame,
    text="Phone:"
).grid(row=0, column=2, padx=10)

tk.Entry(
    input_frame,
    textvariable=phone_var,
    width=25
).grid(row=0, column=3)


# Vehicle Number
tk.Label(
    input_frame,
    text="Vehicle Number:"
).grid(row=1, column=0, padx=10, pady=8)

tk.Entry(
    input_frame,
    textvariable=vehicle_no_var,
    width=25
).grid(row=1, column=1)


# Vehicle Type
tk.Label(
    input_frame,
    text="Vehicle Type:"
).grid(row=1, column=2, padx=10)

vehicle_combo = ttk.Combobox(
    input_frame,
    textvariable=vehicle_type_var,
    values=[
        "Bike",
        "Car",
        "Auto",
        "Bus",
        "Truck",
        "Other"
    ],
    state="readonly",
    width=22
)

vehicle_combo.grid(row=1, column=3)


# Violation
tk.Label(
    input_frame,
    text="Violation:"
).grid(row=2, column=0, padx=10, pady=8)

violation_combo = ttk.Combobox(
    input_frame,
    textvariable=violation_var,
    values=list(FINE_RULES.keys()),
    state="readonly",
    width=22
)

violation_combo.grid(row=2, column=1)

violation_combo.bind(
    "<<ComboboxSelected>>",
    calculate_fine
)


# Amount
tk.Label(
    input_frame,
    text="Fine Amount:"
).grid(row=2, column=2, padx=10)

tk.Entry(
    input_frame,
    textvariable=amount_var,
    width=25,
    state="readonly"
).grid(row=2, column=3)


# =========================
# BUTTONS
# =========================

button_frame = tk.Frame(root)

button_frame.pack(pady=15)


tk.Button(
    button_frame,
    text="GENERATE FINE",
    width=18,
    command=generate_fine
).grid(row=0, column=0, padx=5)


tk.Button(
    button_frame,
    text="CLEAR",
    width=15,
    command=clear_fields
).grid(row=0, column=1, padx=5)


tk.Button(
    button_frame,
    text="MARK AS PAID",
    width=15,
    command=mark_paid
).grid(row=0, column=2, padx=5)


tk.Button(
    button_frame,
    text="DELETE",
    width=15,
    command=delete_fine
).grid(row=0, column=3, padx=5)


tk.Button(
    button_frame,
    text="RECEIPT",
    width=15,
    command=generate_receipt
).grid(row=0, column=4, padx=5)


tk.Button(
    button_frame,
    text="STATISTICS",
    width=15,
    command=show_statistics
).grid(row=0, column=5, padx=5)


# =========================
# SEARCH
# =========================

search_frame = tk.Frame(root)

search_frame.pack(
    padx=20,
    pady=5,
    fill="x"
)

tk.Label(
    search_frame,
    text="Search:"
).pack(side="left")

tk.Entry(
    search_frame,
    textvariable=search_var,
    width=40
).pack(side="left", padx=10)

tk.Button(
    search_frame,
    text="SEARCH",
    command=search_fines
).pack(side="left")

tk.Button(
    search_frame,
    text="SHOW ALL",
    command=load_data
).pack(side="left", padx=5)


# =========================
# TABLE
# =========================

table_frame = tk.Frame(root)

table_frame.pack(
    padx=20,
    pady=10,
    fill="both",
    expand=True
)

columns = (
    "Fine ID",
    "Name",
    "Vehicle",
    "Violation",
    "Amount",
    "Fine Date",
    "Due Date",
    "Status"
)

tree = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings",
    height=12
)

for column in columns:

    tree.heading(
        column,
        text=column
    )

    tree.column(
        column,
        width=110
    )


tree.pack(
    side="left",
    fill="both",
    expand=True
)


scrollbar = ttk.Scrollbar(
    table_frame,
    orient="vertical",
    command=tree.yview
)

scrollbar.pack(
    side="right",
    fill="y"
)

tree.configure(
    yscrollcommand=scrollbar.set
)


# =========================
# LOAD DATABASE
# =========================

load_data()


# =========================
# CLOSE DATABASE
# =========================

def close_app():
    conn.close()
    root.destroy()


root.protocol(
    "WM_DELETE_WINDOW",
    close_app
)


# =========================
# START APPLICATION
# =========================

root.mainloop()
