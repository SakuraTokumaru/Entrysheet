from flask import Flask, render_template, request, redirect, url_for
import calendar
from datetime import datetime

app = Flask(__name__)
events = {}

@app.route('/')
def index():
    # クエリパラメータから year, month を取得（int型）。なければ現在の年月
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    now = datetime.now()
    if not year:
        year = now.year
    if not month:
        month = now.month

    cal = calendar.Calendar(firstweekday=6)  # 日曜始まり
    month_days = cal.monthdayscalendar(year, month)  # 月の日付を週単位のリストで取得

    return render_template(
        'calendar.html',
        year=year,
        month=month,
        month_days=month_days,
        events=events
    )

@app.route('/add_event', methods=['POST'])
def add_event():
    date = request.form.get('date')
    event_text = request.form.get('event')
    year = request.form.get('year')
    month = request.form.get('month')

    if date and event_text:
        if date not in events:
            events[date] = []
        events[date].append(event_text)

    # 追加後は元の年月ページに戻す
    if year and month:
        return redirect(url_for('index', year=year, month=month))
    else:
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
