import os
from flask import Flask, render_template, redirect, request, make_response, session, abort, jsonify, url_for
from data import db_session, news_api
from data.users import User
from data.news import News
from data.equipment import Equipment
from forms.user import RegisterForm, LoginForm
from forms.news import NewsForm
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_restful import reqparse, abort, Api, Resource
from data import news_resources, equipment_resources
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
api = Api(app)

self_picture = []
file_filename = []


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/", methods=['GET', 'POST'])
def index():
    global self_picture, file_filename
    if current_user.is_authenticated:
        if self_picture and current_user.id == self_picture[-1] and len(self_picture) != 1:
            try:
                os.remove(f'static/images/{file_filename[self_picture.index(current_user.id)]}')
            except Exception:
                pass
        elif self_picture and current_user.id in self_picture and len(self_picture) != 1:
            name = file_filename[self_picture.index(current_user.id)]
            s_pict = current_user.id
            file_filename.pop(self_picture.index(current_user.id))
            self_picture.pop(self_picture.index(current_user.id))
            self_picture.append(s_pict)
            file_filename.append(name)

    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        equipment = db_sess.query(Equipment).filter(Equipment.user_id == current_user.id).first()
        if equipment:
            info_equipment = equipment.info_equipment
            type_tank = info_equipment
        else:
            type_tank = 'Green_tank.png'

        news = db_sess.query(News).filter(
            (News.user == current_user) | (News.is_private != True))
        if request.method == "POST":
            file = request.files['photo']
            path = f'static/images/{file.filename}'
            file.save(path)
            file_filename.append(file.filename)
            type_tank = file.filename
            self_tank = 1
            add_equipment(type_tank, self_tank)
    else:
        type_tank = 'Green_tank.png'
        news = db_sess.query(News).filter(News.is_private != True)
    return render_template("index.html", news=news, type_tank=type_tank)


@app.route('/open_news')
def open_news():
    db_sess = db_session.create_session()
    if current_user.is_authenticated:
        news = db_sess.query(News).filter(
            (News.user == current_user) | (News.is_private != True))
    else:
        news = db_sess.query(News).filter(News.is_private != True)
    return render_template("open_news.html", news=news)


@app.route('/shop')
def shop():
    db_sess = db_session.create_session()
    equipment = 0
    if current_user.is_authenticated:
        equipment = db_sess.query(Equipment).filter((Equipment.user == current_user))
    return render_template("shop.html", equipment=equipment)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/news', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.is_private = form.is_private.data
        current_user.news.append(news)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('news.html', title='Добавление новости',
                           form=form)


@app.route('/news&<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == current_user
                                          ).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.is_private.data = news.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        news = db_sess.query(News).filter(News.id == id,
                                          News.user == current_user
                                          ).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            news.is_private = form.is_private.data
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('news.html',
                           title='Редактирование новости',
                           form=form
                           )


@app.route('/news_delete&<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.id == id,
                                      News.user == current_user
                                      ).first()
    if news:
        db_sess.delete(news)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/equipment&<info_equipment>', methods=['GET', 'POST'])
@login_required
def add_equipment(info_equipment, self_tank=None):
    global self_picture
    db_sess = db_session.create_session()
    equipment = db_sess.query(Equipment).filter(Equipment.user_id == current_user.id).first()
    if not equipment:
        db_sess = db_session.create_session()
        equipment = Equipment()
        equipment.id = current_user.id
        equipment.user_id = current_user.id
        equipment.info_equipment = info_equipment
        img = open(f'static/images/{info_equipment}', 'rb').read()
        equipment.image_equipment = img

        current_user.equipment.append(equipment)
        db_sess.merge(current_user)
        db_sess.commit()
    elif equipment:
        db_sess = db_session.create_session()
        equipment = db_sess.query(Equipment).filter(Equipment.user_id == current_user.id).first()
        equipment.info_equipment = info_equipment
        img = open(f'static/images/{info_equipment}', 'rb').read()
        equipment.image_equipment = img

        db_sess.commit()
    else:
        abort(404)

    if self_tank:
        self_picture.append(current_user.id)
    return redirect('/')


@app.route('/forum')
def forum():
    return render_template('forum.html', title='Форум')


@app.route('/support')
def support():
    return render_template('support.html', title='Форум')


@app.route('/donate')
def donate():
    return render_template('donate.html', title='Донат')


@app.route('/send', methods=['GET', 'POST'])
def send_email():
    letter = request.form['letter']
    sender = 'tankistsniper123456@gmail.com'
    password = 'mktfsmsfxjxdfpjw'

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()

    try:
        server.login(sender, password)
        msg = MIMEText(letter)
        msg["Subject"] = "CLICK ME PLEASE!"
        server.sendmail(sender, sender, msg.as_string())

        return render_template('support.html', title='Форум')
    except Exception as _ex:
        return f"{_ex}\nCheck your login or password please!"


def main():
    db_session.global_init("db/blogs.db")
    app.register_blueprint(news_api.blueprint)
    api.add_resource(news_resources.NewsListResource, '/api/v2/news')
    api.add_resource(news_resources.NewsResource, '/api/v2/news&<int:news_id>')
    api.add_resource(equipment_resources.NewsResource_eqiupment, '/api/equipment&<int:user_id>')
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


if __name__ == '__main__':
    main()
