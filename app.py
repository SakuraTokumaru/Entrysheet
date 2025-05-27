from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from markupsafe import Markup, escape  # 修正: jinja2からmarkupsafeに変更

app = Flask(__name__)  # ここでFlaskアプリケーションを定義
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # SQLiteを使用
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.secret_key = 'your_secret_key'  # セッション用の秘密鍵

# ユーザーモデル
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EntryTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    theme = db.Column(db.String(200), nullable=False)  # テーマ
    content = db.Column(db.Text, nullable=True)  # 課題内容
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ログインしているかを確認するデコレータ
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("ログインが必要です。")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # パスワードをハッシュ化して保存
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # サインアップ後にログイン
        session['user_id'] = new_user.id
        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # ユーザーをデータベースから検索
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            return "Invalid email or password", 401
    return render_template('login.html')

@app.route('/index')
@login_required
def index():
    user = User.query.get(session['user_id'])  # ログインしているユーザーを取得
    companies = Company.query.filter_by(user_id=session['user_id']).all()
    return render_template('index.html', user=user, companies=companies)

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    session.pop('user_id', None)
    flash("ログアウトしました。")
    return redirect(url_for('login'))

@app.route('/entry', methods=['GET', 'POST'])
@login_required
def entry():
    if request.method == 'POST':
        company_name = request.form['company_name']
        new_company = Company(user_id=session['user_id'], name=company_name)
        db.session.add(new_company)
        db.session.commit()
        return redirect(url_for('entry'))

    companies = Company.query.filter_by(user_id=session['user_id']).all()
    return render_template('entry.html', companies=companies)

@app.route('/delete_company/<int:company_id>', methods=['POST'])
@login_required
def delete_company(company_id):
    company = Company.query.filter_by(id=company_id, user_id=session['user_id']).first()
    if company:
        db.session.delete(company)
        db.session.commit()
        flash("企業を削除しました。")
    else:
        flash("削除する企業が見つかりませんでした。")
    return redirect(url_for('entry'))

@app.route('/company/<int:company_id>', methods=['GET', 'POST'])
@login_required
def company_page(company_id):
    # 現在の企業を取得
    company = Company.query.filter_by(id=company_id, user_id=session['user_id']).first()
    if not company:
        flash("企業が見つかりません。")
        return redirect(url_for('entry'))

    if request.method == 'POST':
        # テーマを追加
        theme = request.form['theme']
        new_task = EntryTask(company_id=company.id, theme=theme)
        db.session.add(new_task)
        db.session.commit()
        flash("テーマを追加しました。")
        return redirect(url_for('company_page', company_id=company_id))

    # 現在の企業に関連する課題を取得
    tasks = EntryTask.query.filter_by(company_id=company.id).all()
    return render_template('company.html', company=company, tasks=tasks)

@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    # 課題を取得
    task = EntryTask.query.get_or_404(task_id)
    company = Company.query.get(task.company_id)

    # 現在のユーザーがこの企業にアクセスできるか確認
    if not company or company.user_id != session['user_id']:
        flash("アクセス権がありません。")
        return redirect(url_for('entry'))

    if request.method == 'POST':
        if 'delete' in request.form:
            # 課題を削除
            db.session.delete(task)
            db.session.commit()
            flash("課題を削除しました。")
            return redirect(url_for('company_page', company_id=company.id))
        else:
            # 課題内容を更新
            task.content = request.form['content']
            db.session.commit()
            flash("課題内容を更新しました。")
            return redirect(url_for('company_page', company_id=company.id))

    return render_template('edit_task.html', task=task, company=company)

# nl2brフィルタの修正
@app.template_filter('nl2br')
def nl2br(value):
    result = escape(value).replace('\n', Markup('<br>'))
    return Markup(result)

if __name__ == '__main__':
    app.debug = True
    app.run(host='localhost')


