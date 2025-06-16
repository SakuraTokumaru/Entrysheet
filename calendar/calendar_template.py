import tkinter as tk
from tkinter import simpledialog, messagebox
import sqlite3
import calendar
from datetime import datetime

# SQLiteデータベースの初期化
conn = sqlite3.connect("schedule.db")
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS events (date TEXT PRIMARY KEY, details TEXT)''')
conn.commit()

class CalendarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("カレンダーアプリ")

        self.current_year = datetime.now().year
        self.current_month = datetime.now().month

        self.create_widgets()
        self.display_calendar(self.current_year, self.current_month)

    def create_widgets(self):
        self.header = tk.Label(self.root, text=f"{self.current_year}年 {self.current_month}月", font=("Arial", 14))
        self.header.pack()

        self.cal_frame = tk.Frame(self.root)
        self.cal_frame.pack()

    def display_calendar(self, year, month):
        for widget in self.cal_frame.winfo_children():
            widget.destroy()

        cal = calendar.monthcalendar(year, month)
        days = ["月", "火", "水", "木", "金", "土", "日"]

        for i, day in enumerate(days):
            tk.Label(self.cal_frame, text=day, font=("Arial", 12), width=5).grid(row=0, column=i)

        for row, week in enumerate(cal):
            for col, day in enumerate(week):
                if day != 0:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    event = self.get_event(date_str)

                    text = str(day)
                    if event:
                        text += f"\n📌 {event[:5]}…"  # 予定の冒頭を表示（省略形）

                    btn = tk.Button(self.cal_frame, text=text, font=("Arial", 10), width=8, height=3,
                                    command=lambda d=day: self.add_event(year, month, d))
                    btn.grid(row=row + 1, column=col)

    def get_event(self, date):
        cursor.execute("SELECT details FROM events WHERE date=?", (date,))
        result = cursor.fetchone()
        return result[0] if result else ""

    def add_event(self, year, month, day):
        date_str = f"{year}-{month:02d}-{day:02d}"
        current_event = self.get_event(date_str)
        
        event = simpledialog.askstring("予定追加", f"{year}年{month}月{day}日の予定を入力:", initialvalue=current_event)
        if event is not None:  # None はキャンセルボタンを押した場合
            cursor.execute("INSERT OR REPLACE INTO events (date, details) VALUES (?, ?)", (date_str, event))
            conn.commit()
            self.display_calendar(year, month)  # 更新後にカレンダーを再描画

root = tk.Tk()
app = CalendarApp(root)
root.mainloop()
conn.close()