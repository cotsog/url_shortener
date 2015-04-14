from app import app, db, login_manager, openid, dehydrate, saturate, BASE_URL, URLS_PER_PAGE
from flask import render_template, flash, \
    redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, \
    current_user, login_required, UserMixin
from .forms import LinkForm, LoginForm
from .models import User, ShortUrl, FullUrl, ROLE_USER, ROLE_ADMIN
from sqlalchemy.sql.expression import func
from bs4 import BeautifulSoup as BS
from urllib.request import urlopen


class UserClass(UserMixin):
    def __init__(self, name, id, active=True):
        self.name = name
        self.id = id
        self.active = active

    def is_active(self):
        return self.active

    def get_id(self):
        return str(self.id)


def get_title(url):
    bs = BS(urlopen(url))
    return str(bs('title')[0].string)


@app.route('/', methods = ['GET', 'POST'])
@app.route('/index', methods = ['GET', 'POST'])
@login_required
def index():
    form = LinkForm()
    if form.validate_on_submit():
        user_db = User.query.get(g.user.get_id())
        if user_db is None:
            raise Exception('User not found in database')
        flash("Url: " + form.url.data)

        query = db.session.query(func.max(ShortUrl.id).label('max_id'))
        id = query.one().max_id
        id = int(id) + 1 if id else 1
        url = BASE_URL + 's/' + dehydrate(id)

        short_url = ShortUrl(url=url, creator=user_db, delete_after_first_usage=form.delete_after_usage.data)

        title = get_title(form.url.data)

        full_url = FullUrl(url=form.url.data, short_url=short_url, title=title)

        db.session.add(short_url)
        db.session.add(full_url)
        db.session.commit()

        flash('Short url: {0}'.format(short_url.url))

        return redirect('/')
    return render_template('index.html', title="Main", form=form)


@app.route('/profile')
@app.route('/profile/<int:page>')
@login_required
def my_profile(page=1):
    user_db = User.query.get(g.user.get_id())
    paginate = user_db.urls.paginate(page, URLS_PER_PAGE, False)
    full_urls_db = []
    for url in paginate.items:
        full_urls_db.append(url.full_url)

    short_urls = list(map(lambda x: x.url, paginate.items))
    full_urls = list(map(lambda x: x.url, full_urls_db))
    titles = list(map(lambda x: x.title, full_urls_db))
    urls = list(zip(short_urls, full_urls, titles))

    def get_title(url):
        bs = BS(urlopen(url))
        return str(bs('title')[0].string)

    return render_template('profile.html', urls=urls, nick=g.user.name, paginate=paginate)


@app.route('/login', methods = ['GET', 'POST'])
@openid.loginhandler
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        flash('Login requested for OpenID="' + form.openid.data + 
            '", remember_me=' + str(form.remember_me.data))
        return openid.try_login(form.openid.data, ask_for=['nickname', 'email'])
    return render_template('login.html', 
        title = 'Sign In',
        form = form,
        providers = app.config['OPENID_PROVIDERS'])


@app.route('/logout')
@login_required
def logout():
    if g.user is None or not g.user.is_authenticated():
        return redirect(url_for('index'))
    logout_user()
    return redirect(url_for('index'))


@openid.after_login
def after_login(response):
    if response.email is None or response.email == "":
        flash('Invalid login. Please try again')
        return redirect(url_for('login'))
    user_db = User.query.filter_by(email=response.email).first()
    if user_db is None:
        nick = response.nickname
        if nick is None or nick == "":
            nick = response.email.split('@')[0]
        user_db = User(nick=nick, email=response.email, role=ROLE_USER)
        db.session.add(user_db)
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    
    user = UserClass(user_db.nick, user_db.id)

    login_user(user, remember=remember_me)
    return redirect(request.args.get('next') or url_for('index'))


@app.route('/s/<short_url>')
def redirect_to(short_url):
    try:
        id = saturate(short_url)
    except:
        return redirect(url_for('index'))
    short_url_db = ShortUrl.query.get(id)

    if short_url_db is None:
        flash('Url "{0}" not registered'.format(short_url))
        return redirect(url_for('index'))

    full_url_db = short_url_db.full_url

    if short_url_db.delete_after_first_usage:
        db.session.delete(short_url_db)
        db.session.delete(full_url_db)
        db.session.commit()
    return redirect(full_url_db.url)


@app.route('/delete/<short_url>')
@login_required
def delete(short_url):
    id = saturate(short_url)
    short_url_db = ShortUrl.query.get(id)
    if short_url_db is None:
        flash('Url "{0}" is not registered'.format(short_url))
        return redirect(url_for('index'))

    full_url_db = short_url_db.full_url

    db.session.delete(short_url_db)
    db.session.delete(full_url_db)
    db.session.commit()

    return redirect(url_for('index'))


@login_manager.user_loader
def user_loader(id):
    id = int(id)
    user_db = User.query.get(id)
    if user_db is None:
        return user_db
    return UserClass(user_db.nick, user_db.id)


@app.before_request
def before_request():
    g.user = current_user
