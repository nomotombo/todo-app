import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header

USER_FILE = "users.json"
TASK_FILE = "tasks.json"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SENDER_EMAIL = "yuriasunshine0218@gmail.com"
SENDER_PASSWORD = "dgey hlpj ugow ylwe"


def send_email(to_email, subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(users):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def load_tasks():
    if not os.path.exists(TASK_FILE):
        return {}
    with open(TASK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tasks(data):
    with open(TASK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("ログイン")
        self.root.geometry("300x220")

        self.users = load_users()

        tk.Label(root, text="メールアドレス").pack(pady=5)
        self.email = tk.Entry(root, width=30)
        self.email.pack()

        tk.Label(root, text="パスワード").pack(pady=5)
        self.password = tk.Entry(root, show="*", width=30)
        self.password.pack()

        tk.Button(root, text="ログイン", command=self.login).pack(pady=8)
        tk.Button(root, text="新規登録", command=self.register).pack()

    def login(self):
        email = self.email.get().strip()
        pw = self.password.get().strip()

        if email in self.users and self.users[email] == pw:
            self.root.destroy()

            todo_root = tk.Tk()
            TodoApp(todo_root, email)
            todo_root.mainloop()
        else:
            messagebox.showerror("エラー", "ログイン失敗")

    def register(self):
        email = self.email.get().strip()
        pw = self.password.get().strip()

        if email == "" or pw == "":
            messagebox.showwarning("警告", "メールアドレスとパスワードを入力してください")
            return

        if email in self.users:
            messagebox.showerror("エラー", "既に存在します")
            return

        self.users[email] = pw
        save_users(self.users)

        messagebox.showinfo("成功", "登録完了")


class TodoApp:
    def __init__(self, root, user):
        self.root = root
        self.user = user

        self.root.title(f"ToDoアプリ - {user}")
        self.root.geometry("750x500")

        all_tasks = load_tasks()
        self.tasks = all_tasks.get(user, [])

        frame = tk.Frame(root)
        frame.pack(pady=10)

        self.entry = tk.Entry(frame, width=25)
        self.entry.pack(side=tk.LEFT, padx=5)

        self.date = DateEntry(frame, date_pattern="yyyy-mm-dd")
        self.date.pack(side=tk.LEFT, padx=5)

        self.hour = tk.Spinbox(frame, from_=0, to=23, width=3, format="%02.0f")
        self.hour.pack(side=tk.LEFT)

        tk.Label(frame, text=":").pack(side=tk.LEFT)

        self.minute = tk.Spinbox(frame, from_=0, to=59, width=3, format="%02.0f")
        self.minute.pack(side=tk.LEFT)

        tk.Button(frame, text="追加", command=self.add).pack(side=tk.LEFT, padx=5)

        self.listbox = tk.Listbox(root, width=90)
        self.listbox.pack(pady=10)

        tk.Button(root, text="完了", command=self.complete).pack(pady=5)
        tk.Button(root, text="削除", command=self.delete).pack(pady=5)

        self.update()
        self.check_deadline()

    def save(self):
        data = load_tasks()
        data[self.user] = self.tasks
        save_tasks(data)

    def add(self):
        text = self.entry.get().strip()

        if text == "":
            messagebox.showwarning("警告", "タスクを入力してください")
            return

        d = self.date.get_date()
        h = int(self.hour.get())
        m = int(self.minute.get())

        deadline = datetime(d.year, d.month, d.day, h, m)

        self.tasks.append({
            "text": text,
            "deadline": deadline.strftime("%Y-%m-%d %H:%M"),
            "done": False,
            "notified": False
        })

        self.entry.delete(0, tk.END)
        self.save()
        self.update()

    def complete(self):
        selected = self.listbox.curselection()

        if not selected:
            messagebox.showwarning("警告", "タスクを選択してください")
            return

        self.tasks[selected[0]]["done"] = True
        self.save()
        self.update()

    def delete(self):
        selected = self.listbox.curselection()

        if not selected:
            messagebox.showwarning("警告", "タスクを選択してください")
            return

        self.tasks.pop(selected[0])
        self.save()
        self.update()

    def update(self):
        self.listbox.delete(0, tk.END)
        now = datetime.now()

        for task in self.tasks:
            if "done" not in task:
                task["done"] = task.get("completed", False)

            if "notified" not in task:
                task["notified"] = False

            status = "完了" if task["done"] else "未完了"
            text = f"[{status}] {task['text']} 期限:{task['deadline']}"
            self.listbox.insert(tk.END, text)

            index = self.listbox.size() - 1
            deadline = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")

            if not task["done"] and timedelta(0) <= deadline - now <= timedelta(days=1):
                self.listbox.itemconfig(index, fg="red")

    def check_deadline(self):
        now = datetime.now()
        changed = False

        for task in self.tasks:
            deadline = datetime.strptime(task["deadline"], "%Y-%m-%d %H:%M")

            if (
                not task["done"]
                and not task.get("notified", False)
                and timedelta(0) <= deadline - now <= timedelta(days=1)
            ):
                try:
                    send_email(
                        self.user,
                        "Todo deadline notification",
                        f"Task deadline is near.\n\nTask: {task['text']}\nDeadline: {task['deadline']}"
                    )

                    task["notified"] = True
                    changed = True

                except Exception as e:
                    print("メール送信エラー:", e)

        if changed:
            self.save()
            self.update()

        self.root.after(60000, self.check_deadline)


if __name__ == "__main__":
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()