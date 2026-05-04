"""
Student Task & Priority Manager
================================
A tkinter-based task management application for secondary school students.
Supports login/signup, task creation with priority levels, due dates,
completion tracking, and filtering.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import hashlib
from datetime import datetime, date

# ─────────────────────────────────────────────
#  COLOUR CONSTANTS  (matches your design)
# ─────────────────────────────────────────────
SIDEBAR_BG    = "#3d2b6b"   # deep purple sidebar
SIDEBAR_SEL   = "#c0392b"   # red highlight for active item
SIDEBAR_FG    = "#ffffff"
TOPBAR_BG     = "#5b3fa0"   # medium purple topbar
CONTENT_BG    = "#f0f0f5"   # light grey content area
CARD_BG       = "#ffffff"
ACCENT_PURPLE = "#7c5cbf"
BTN_ADD       = "#7c5cbf"
BTN_LOGIN     = "#3d5af1"
HIGH_COLOR    = "#e74c3c"   # red  – high priority flag
MED_COLOR     = "#f39c12"   # orange – medium priority
LOW_COLOR     = "#27ae60"   # green  – low priority
DONE_COLOR    = "#27ae60"   # green tick
TEXT_DARK     = "#1a1a2e"
TEXT_MID      = "#555577"

PRIORITY_COLORS = {"High": HIGH_COLOR, "Medium": MED_COLOR, "Low": LOW_COLOR}
PRIORITY_ICONS  = {"High": "🚩", "Medium": "⚡", "Low": "✅"}

DATA_FILE  = "tasks.json"
USERS_FILE = "users.json"

# ─────────────────────────────────────────────
#  DATA HELPERS
# ─────────────────────────────────────────────

def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────

class TaskManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Student Task Manager")
        self.geometry("880x580")
        self.resizable(True, True)
        self.configure(bg=SIDEBAR_BG)

        # State
        self.current_user  = None
        self.current_view  = "all"
        self.tasks         = []          # list of task dicts
        self.users         = load_json(USERS_FILE, {})

        # Build layout frames
        self._build_topbar()
        self._build_sidebar()
        self._build_content()

        # Start on login screen
        self._show_login()

    # ── TOP BAR ──────────────────────────────

    def _build_topbar(self):
        self.topbar = tk.Frame(self, bg=TOPBAR_BG, height=48)
        self.topbar.pack(side="top", fill="x")
        self.topbar.pack_propagate(False)

        tk.Label(self.topbar, text="TASK MANAGER", bg=TOPBAR_BG,
                 fg=SIDEBAR_FG, font=("Georgia", 15, "bold")).pack(side="left", padx=16, pady=10)

        # Right-side buttons
        self.btn_add = tk.Button(self.topbar, text="＋ Add Task",
                                 bg=BTN_ADD, fg="white",
                                 font=("Arial", 10, "bold"), bd=0,
                                 padx=12, pady=4, cursor="hand2",
                                 command=self._open_add_task)

        self.btn_filter = tk.Button(self.topbar, text="Filter ▾",
                                    bg=TOPBAR_BG, fg="white",
                                    font=("Arial", 10), bd=1,
                                    relief="solid", padx=10, pady=4,
                                    cursor="hand2",
                                    command=self._toggle_filter)

        self.btn_auth = tk.Button(self.topbar, text="Login / Signup",
                                  bg=BTN_LOGIN, fg="white",
                                  font=("Arial", 10, "bold"), bd=0,
                                  padx=12, pady=4, cursor="hand2",
                                  command=self._show_login)

        # Pack right-to-left
        self.btn_auth.pack(side="right", padx=6, pady=8)
        self.btn_filter.pack(side="right", padx=4, pady=8)
        self.btn_add.pack(side="right", padx=4, pady=8)

        # Active filter label
        self.filter_var = tk.StringVar(value="All")
        self.filter_label = tk.Label(self.topbar, textvariable=self.filter_var,
                                     bg=TOPBAR_BG, fg="#ddccff",
                                     font=("Arial", 9))
        self.filter_label.pack(side="right", padx=2)

    # ── SIDEBAR ───────────────────────────────

    def _build_sidebar(self):
        self.sidebar = tk.Frame(self, bg=SIDEBAR_BG, width=180)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.nav_btns = {}
        nav_items = [
            ("all",       "☰  All Tasks"),
            ("high",      "🚩  High Priority"),
            ("completed", "✅  Completed Tasks"),
            ("upcoming",  "📅  Upcoming"),
        ]
        for key, label in nav_items:
            btn = tk.Button(self.sidebar, text=label, anchor="w",
                            bg=SIDEBAR_BG, fg=SIDEBAR_FG,
                            font=("Arial", 11), bd=0,
                            padx=18, pady=12, cursor="hand2",
                            activebackground=SIDEBAR_SEL,
                            activeforeground="white",
                            command=lambda k=key: self._switch_view(k))
            btn.pack(fill="x")
            self.nav_btns[key] = btn

        self._highlight_nav("all")

    def _highlight_nav(self, active_key):
        for key, btn in self.nav_btns.items():
            btn.configure(bg=SIDEBAR_SEL if key == active_key else SIDEBAR_BG)

    # ── CONTENT AREA ─────────────────────────

    def _build_content(self):
        self.content = tk.Frame(self, bg=CONTENT_BG)
        self.content.pack(side="left", fill="both", expand=True)

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    # ── VIEWS ─────────────────────────────────

    def _switch_view(self, view_key):
        if not self.current_user:
            messagebox.showinfo("Login Required", "Please log in to view your tasks.")
            return
        self.current_view = view_key
        self._highlight_nav(view_key)
        self._show_tasks_view(view_key)

    def _show_tasks_view(self, view_key):
        self._clear_content()
        self.filter_var.set("All")

        titles = {
            "all":       "All Tasks",
            "high":      "High Priority Tasks",
            "completed": "Completed Tasks",
            "upcoming":  "Upcoming Tasks",
        }

        # Header
        header = tk.Frame(self.content, bg=CONTENT_BG)
        header.pack(fill="x", padx=24, pady=(20, 8))
        tk.Label(header, text=titles[view_key], bg=CONTENT_BG,
                 fg=TEXT_DARK, font=("Georgia", 18, "bold")).pack(side="left")

        # Scrollable task list
        canvas = tk.Canvas(self.content, bg=CONTENT_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content, orient="vertical", command=canvas.yview)
        self.task_frame = tk.Frame(canvas, bg=CONTENT_BG)

        self.task_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.task_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=4)
        scrollbar.pack(side="right", fill="y")

        # Mouse wheel
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        self._render_tasks(view_key)

    def _render_tasks(self, view_key, filter_priority=None):
        # Clear old cards
        for w in self.task_frame.winfo_children():
            w.destroy()

        tasks = self.tasks

        # Filter by view
        if view_key == "high":
            tasks = [t for t in tasks if t["priority"] == "High" and not t["done"]]
        elif view_key == "completed":
            tasks = [t for t in tasks if t["done"]]
        elif view_key == "upcoming":
            today = date.today()
            tasks = [t for t in tasks
                     if not t["done"] and t.get("due_date")]
            tasks = sorted(tasks, key=lambda t: t["due_date"])

        # Filter by priority dropdown
        if filter_priority and filter_priority != "All":
            tasks = [t for t in tasks if t["priority"] == filter_priority]

        if not tasks:
            tk.Label(self.task_frame, text="No tasks found.",
                     bg=CONTENT_BG, fg=TEXT_MID,
                     font=("Arial", 12)).pack(pady=40)
            return

        for i, task in enumerate(tasks):
            self._build_task_card(self.task_frame, task, i)

    def _build_task_card(self, parent, task, index):
        card = tk.Frame(parent, bg=CARD_BG, bd=0,
                        highlightthickness=1,
                        highlightbackground="#d8d8e8",
                        cursor="arrow")
        card.pack(fill="x", padx=4, pady=4)

        # Priority colour strip
        pri_color = PRIORITY_COLORS.get(task["priority"], "#999")
        strip = tk.Frame(card, bg=pri_color, width=5)
        strip.pack(side="left", fill="y")

        # Icon + text
        icon = PRIORITY_ICONS.get(task["priority"], "•")
        icon_lbl = tk.Label(card, text=icon, bg=CARD_BG,
                            fg=pri_color, font=("Arial", 14))
        icon_lbl.pack(side="left", padx=(10, 6), pady=12)

        info = tk.Frame(card, bg=CARD_BG)
        info.pack(side="left", fill="x", expand=True, pady=8)

        font_task = ("Arial", 11, "bold")
        fg_task   = TEXT_MID if task["done"] else TEXT_DARK
        name_text = ("✔  " if task["done"] else "") + task["name"]
        tk.Label(info, text=name_text, bg=CARD_BG,
                 fg=fg_task, font=font_task, anchor="w").pack(anchor="w")

        due = task.get("due_date", "")
        due_text = f"Due {due}" if due else "No due date"
        tk.Label(info, text=due_text, bg=CARD_BG,
                 fg=TEXT_MID, font=("Arial", 9), anchor="w").pack(anchor="w")

        subject = task.get("subject", "")
        if subject:
            tk.Label(info, text=subject, bg=CARD_BG,
                     fg=ACCENT_PURPLE, font=("Arial", 8), anchor="w").pack(anchor="w")

        # Checkbox / Done toggle
        chk_var = tk.BooleanVar(value=task["done"])
        chk = tk.Checkbutton(card, variable=chk_var, bg=CARD_BG,
                              activebackground=CARD_BG,
                              command=lambda t=task, v=chk_var: self._toggle_done(t, v))
        chk.pack(side="right", padx=8)

        # Delete button
        del_btn = tk.Button(card, text="🗑", bg=CARD_BG, fg="#cc4444",
                            font=("Arial", 11), bd=0, cursor="hand2",
                            command=lambda t=task: self._delete_task(t))
        del_btn.pack(side="right", padx=4)

    def _toggle_done(self, task, var):
        task["done"] = var.get()
        self._save_tasks()
        self._render_tasks(self.current_view)

    def _delete_task(self, task):
        if messagebox.askyesno("Delete Task", f"Delete \"{task['name']}\"?"):
            self.tasks.remove(task)
            self._save_tasks()
            self._render_tasks(self.current_view)

    # ── FILTER ────────────────────────────────

    def _toggle_filter(self):
        menu = tk.Menu(self, tearoff=0)
        for p in ["All", "High", "Medium", "Low"]:
            menu.add_command(label=p,
                command=lambda pr=p: self._apply_filter(pr))
        x = self.btn_filter.winfo_rootx()
        y = self.btn_filter.winfo_rooty() + self.btn_filter.winfo_height()
        menu.tk_popup(x, y)

    def _apply_filter(self, priority):
        self.filter_var.set(priority)
        self._render_tasks(self.current_view, filter_priority=priority)

    # ── ADD TASK DIALOG ───────────────────────

    def _open_add_task(self):
        if not self.current_user:
            messagebox.showinfo("Login Required", "Please log in first.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Add New Task")
        dialog.geometry("400x360")
        dialog.configure(bg=CONTENT_BG)
        dialog.grab_set()
        dialog.resizable(False, False)

        tk.Label(dialog, text="Add New Task", bg=CONTENT_BG,
                 fg=TEXT_DARK, font=("Georgia", 14, "bold")).pack(pady=(20, 12))

        def field(label_text, widget_factory):
            row = tk.Frame(dialog, bg=CONTENT_BG)
            row.pack(fill="x", padx=30, pady=4)
            tk.Label(row, text=label_text, bg=CONTENT_BG,
                     fg=TEXT_DARK, font=("Arial", 10), width=12,
                     anchor="w").pack(side="left")
            w = widget_factory(row)
            w.pack(side="left", fill="x", expand=True)
            return w

        name_entry    = field("Task Name:", lambda p: tk.Entry(p, font=("Arial", 10)))
        subject_entry = field("Subject:", lambda p: tk.Entry(p, font=("Arial", 10)))
        due_entry     = field("Due Date:", lambda p: tk.Entry(p, font=("Arial", 10)))

        # Priority radio
        pri_frame = tk.Frame(dialog, bg=CONTENT_BG)
        pri_frame.pack(fill="x", padx=30, pady=6)
        tk.Label(pri_frame, text="Priority:", bg=CONTENT_BG,
                 fg=TEXT_DARK, font=("Arial", 10), width=12, anchor="w").pack(side="left")
        pri_var = tk.StringVar(value="Medium")
        for p, c in PRIORITY_COLORS.items():
            tk.Radiobutton(pri_frame, text=p, variable=pri_var, value=p,
                           bg=CONTENT_BG, fg=c,
                           activebackground=CONTENT_BG,
                           selectcolor=CONTENT_BG,
                           font=("Arial", 10, "bold")).pack(side="left", padx=6)

        # Hint for due date
        tk.Label(dialog, text="Due Date format: YYYY-MM-DD (e.g. 2025-12-01)",
                 bg=CONTENT_BG, fg=TEXT_MID, font=("Arial", 8)).pack()

        def submit():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Missing", "Please enter a task name.", parent=dialog)
                return
            self.tasks.append({
                "name":     name,
                "subject":  subject_entry.get().strip(),
                "due_date": due_entry.get().strip(),
                "priority": pri_var.get(),
                "done":     False,
                "user":     self.current_user,
            })
            self._save_tasks()
            self._render_tasks(self.current_view)
            dialog.destroy()

        tk.Button(dialog, text="Add Task", bg=BTN_ADD, fg="white",
                  font=("Arial", 11, "bold"), bd=0, padx=20, pady=8,
                  cursor="hand2", command=submit).pack(pady=16)

    # ── LOGIN / SIGNUP ────────────────────────

    def _show_login(self):
        self._clear_content()
        self.current_view = "login"
        self._highlight_nav("all")  # nothing highlighted

        # Outer centring frame
        outer = tk.Frame(self.content, bg=CONTENT_BG)
        outer.pack(expand=True)

        # Card
        card = tk.Frame(outer, bg=CARD_BG, bd=0,
                        highlightthickness=1, highlightbackground="#ccccdd",
                        padx=40, pady=36)
        card.pack(padx=60, pady=60)

        tk.Label(card, text="Login", bg=CARD_BG,
                 fg=TEXT_DARK, font=("Georgia", 18, "bold")).pack(pady=(0, 20))

        # Username
        u_frame = tk.Frame(card, bg=CARD_BG)
        u_frame.pack(fill="x", pady=6)
        tk.Label(u_frame, text="👤", bg=CARD_BG, font=("Arial", 12)).pack(side="left", padx=(0, 6))
        u_entry = tk.Entry(u_frame, font=("Arial", 11), bd=1, relief="solid",
                           width=24)
        u_entry.insert(0, "Username")
        u_entry.pack(side="left")
        u_entry.bind("<FocusIn>",  lambda e: u_entry.delete(0, "end") if u_entry.get() == "Username" else None)
        u_entry.bind("<FocusOut>", lambda e: u_entry.insert(0, "Username") if not u_entry.get() else None)

        # Password
        p_frame = tk.Frame(card, bg=CARD_BG)
        p_frame.pack(fill="x", pady=6)
        tk.Label(p_frame, text="🔒", bg=CARD_BG, font=("Arial", 12)).pack(side="left", padx=(0, 6))
        p_entry = tk.Entry(p_frame, font=("Arial", 11), bd=1, relief="solid",
                           width=24, show="•")
        p_entry.pack(side="left")

        msg_var = tk.StringVar()
        tk.Label(card, textvariable=msg_var, bg=CARD_BG,
                 fg="#c0392b", font=("Arial", 9)).pack()

        def do_login():
            u = u_entry.get().strip()
            p = p_entry.get().strip()
            if u == "Username" or not u or not p:
                msg_var.set("Please enter username and password.")
                return
            if u in self.users and self.users[u] == hash_pw(p):
                self.current_user = u
                self._load_tasks()
                self.btn_auth.configure(text=f"  {u}  ▾")
                self._switch_view("all")
            else:
                msg_var.set("Incorrect username or password.")

        tk.Button(card, text="Log In", bg=BTN_LOGIN, fg="white",
                  font=("Arial", 11, "bold"), bd=0, padx=0, pady=8,
                  cursor="hand2", width=24,
                  command=do_login).pack(pady=12)

        tk.Button(card, text="Create an account", bg=CARD_BG,
                  fg=BTN_LOGIN, font=("Arial", 10), bd=0,
                  cursor="hand2",
                  command=self._show_signup).pack()

        # Allow Enter key
        self.bind("<Return>", lambda e: do_login())

    def _show_signup(self):
        self._clear_content()

        outer = tk.Frame(self.content, bg=CONTENT_BG)
        outer.pack(expand=True)

        card = tk.Frame(outer, bg=CARD_BG, bd=0,
                        highlightthickness=1, highlightbackground="#ccccdd",
                        padx=40, pady=36)
        card.pack(padx=60, pady=60)

        tk.Label(card, text="Create Account", bg=CARD_BG,
                 fg=TEXT_DARK, font=("Georgia", 18, "bold")).pack(pady=(0, 20))

        fields = {}
        for lbl in ["Username", "Password", "Confirm Password"]:
            f = tk.Frame(card, bg=CARD_BG)
            f.pack(fill="x", pady=5)
            tk.Label(f, text=lbl, bg=CARD_BG, fg=TEXT_DARK,
                     font=("Arial", 10), width=16, anchor="w").pack(side="left")
            e = tk.Entry(f, font=("Arial", 11), bd=1, relief="solid",
                         show="•" if "Password" in lbl else "", width=20)
            e.pack(side="left")
            fields[lbl] = e

        msg_var = tk.StringVar()
        tk.Label(card, textvariable=msg_var, bg=CARD_BG,
                 fg="#c0392b", font=("Arial", 9)).pack()

        def do_signup():
            u = fields["Username"].get().strip()
            p = fields["Password"].get().strip()
            c = fields["Confirm Password"].get().strip()
            if not u or not p:
                msg_var.set("Please fill all fields.")
                return
            if p != c:
                msg_var.set("Passwords do not match.")
                return
            if u in self.users:
                msg_var.set("Username already taken.")
                return
            self.users[u] = hash_pw(p)
            save_json(USERS_FILE, self.users)
            self.current_user = u
            self._load_tasks()
            self.btn_auth.configure(text=f"  {u}  ▾")
            self._switch_view("all")

        tk.Button(card, text="Sign Up", bg=BTN_LOGIN, fg="white",
                  font=("Arial", 11, "bold"), bd=0, padx=0, pady=8,
                  cursor="hand2", width=22, command=do_signup).pack(pady=12)

        tk.Button(card, text="← Back to Login", bg=CARD_BG,
                  fg=BTN_LOGIN, font=("Arial", 10), bd=0,
                  cursor="hand2", command=self._show_login).pack()

    # ── PERSISTENCE ───────────────────────────

    def _save_tasks(self):
        all_tasks = load_json(DATA_FILE, [])
        # Remove current user's tasks, re-add updated list
        other_tasks = [t for t in all_tasks if t.get("user") != self.current_user]
        save_json(DATA_FILE, other_tasks + self.tasks)

    def _load_tasks(self):
        all_tasks = load_json(DATA_FILE, [])
        self.tasks = [t for t in all_tasks if t.get("user") == self.current_user]


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = TaskManagerApp()
    app.mainloop()