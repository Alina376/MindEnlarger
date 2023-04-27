from flask import Flask, render_template, redirect, url_for, request, abort

from data import db_session
from data.users import User
from data.modules import Module
from data.words import Word
from flask_login import LoginManager, login_user, logout_user, current_user
from forms.login import LoginForm
from forms.user import RegisterForm
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)


@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")


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
            login=form.login.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


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


@app.route('/logout')
def logout():
    logout_user()
    return redirect("/")


@app.route('/add_avatar', methods=['GET', 'POST'])
def add_avatar():
    if current_user.is_authenticated:
        if request.method == 'GET':
            return render_template('add_avatar.html')
        elif request.method == 'POST':
            f = request.files['file']
            with open('static/img/' + request.files['file'].filename, 'wb') as fpic:
                fpic.write(f.read())
            db_sess = db_session.create_session()
            user = db_sess.query(User).filter(User.id == current_user.id).one()
            user.avatar = request.files['file'].filename
            db_sess.commit()
            return redirect('/')
    else:
        return redirect('/error')


@app.route('/all_modules')
def all_modules():
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        modules = db_sess.query(Module).filter(current_user.id == Module.user_id).all()
        return render_template('modules.html', modules=modules)
    else:
        return redirect('/error')


@app.route('/add_module', methods=['GET', 'POST'])
def add_module():
    if current_user.is_authenticated:
        if request.method == 'GET':
            return render_template('add_module.html')
        elif request.method == 'POST':
            select = int(request.form.get('comp_select'))
            title = request.form.get('title')
            db_sess = db_session.create_session()
            module = Module()
            module.module_title = title
            module.user_id = current_user.id
            db_sess.add(module)
            db_sess.commit()
            return redirect(f'/add_words_to_module/{title}/{select}')
    else:
        return redirect('/error')


@app.route('/add_words_to_module/<module>/<select>', methods=['GET', 'POST'])
def add_words_to_module(module, select):
    if current_user.is_authenticated:
        select = int(select)
        if request.method == 'GET':
            forms = []
            for i in range(1, select + 1):
                forms.append([f'word{i}', f'translation{i}', str(i)])
            return render_template('add_words_to_module.html', forms=forms)
        elif request.method == 'POST':
            words = []
            for i in range(1, select + 1):
                words.append([request.form[f'word{i}'], request.form[f'translation{i}']])
            for i in range(select):
                db_sess = db_session.create_session()
                word = Word()
                word.word = words[i][0]
                word.translation = words[i][1]
                module_id = db_sess.query(Module).filter(Module.user_id == current_user.id, Module.module_title == module).first()
                if module_id:
                    pass
                else:
                    return redirect('/error')
                word.module_id = module_id.module_id
                db_sess.add(word)
                db_sess.commit()
            return redirect('/')
    else:
        return redirect('/error')


@app.route('/get_translation/', methods=['GET', 'POST'])
def get_translation():
    if current_user.is_authenticated:
        if request.method == 'POST':
            word = request.form['word']
            IAM_TOKEN = 'y0_AgAAAABX8WYwAATuwQAAAADhtX8n4q97oK6_THSGws4MkXqzzEsyGFY'
            target_language = 'ru'
            texts = word.split()

            body = {
                "targetLanguageCode": target_language,
                "texts": texts,
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": 'Api-Key AQVN3b8JsaeFGtvdUxTGNcqq86b-KwV7nX5zm2a8'
            }

            response = requests.post('https://translate.api.cloud.yandex.net/translate/v2/translate',
                                     json=body,
                                     headers=headers
                                     )
            if response:
                json_response = response.json()
                translation = json_response['translations'][0]['text']
                return redirect(f'/translated_word/{word}/{translation}')
        elif request.method == 'GET':
            return render_template('get_translation.html')
    else:
        return redirect('/error')


@app.route('/translated_word/<word>/<translation>')
def translated_word(word, translation):
    if current_user.is_authenticated:
        return render_template('translated_word.html', word=word, translation=translation)
    else:
        return redirect('/error')


@app.route('/edit_module/<title>', methods=['GET', 'POST'])
def edit_module(title):
    if current_user.is_authenticated:
        if request.method == 'GET':
            db_sess = db_session.create_session()
            module = db_sess.query(Module).filter(Module.user_id == current_user.id, Module.module_title == title).first()
            if module:
                pass
            else:
                return redirect('/error')
            words = db_sess.query(Word).filter(module.module_id == Word.module_id).all()
            words_and_translations = []
            for i in range(1, len(words) + 1):
                words_and_translations.append(
                    [f'word{i}', f'translation{i}', i, words[i - 1].word, words[i - 1].translation])
            return render_template('edit_module.html', title=title,
                                   forms=words_and_translations)
        elif request.method == 'POST':
            db_sess = db_session.create_session()
            module = db_sess.query(Module).filter(Module.user_id == current_user.id, Module.module_title == title).first()
            if module:
                module_id = module.module_id
                words = db_sess.query(Word).filter(module.module_id == Word.module_id).all()
                for i in range(1, len(words) + 1):
                    word = words[i - 1]
                    if word.word != request.form[f'word{i}'] or word.translation != request.form[f'translation{i}']:
                        word.word = request.form[f'word{i}']
                        word.translation = request.form[f'translation{i}']
            else:
                return redirect('/error')
            db_sess.commit()
            return redirect('/')
    else:
        return redirect('/error')


@app.route('/delete_module/<int:id>', methods=['GET', 'POST'])
def delete_module(id):
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        module = db_sess.query(Module).filter(Module.user_id == current_user.id, Module.module_id == id).first()
        if module:
            words = db_sess.query(Word).filter(module.module_id == Word.module_id).all()
            for word in words:
                db_sess.delete(word)
            db_sess.delete(module)
            db_sess.commit()
        else:
            return redirect('/error')
        return redirect('/all_modules')
    else:
        return redirect('/error')


@app.route('/study/<int:module_id>')
def study(module_id):
    if current_user.is_authenticated:
        db_sess = db_session.create_session()
        module = db_sess.query(Module).filter(Module.user_id == current_user.id, Module.module_id == module_id).first()
        if module:
            pass
        else:
            return redirect('/error')
        res = db_sess.query(Word).filter(Word.module_id == module_id).all()
        all_words = []
        for i in res:
            all_words.append([i.word, i.translation])
        return render_template('study.html', all_words=all_words)
    else:
        return redirect('/error')


@app.route('/error')
def error():
    return render_template('error.html')


if __name__ == '__main__':
    filename = 'users.db'
    db_session.global_init(f"db/{filename}")
    app.run(port=8084, host='127.0.0.1')
