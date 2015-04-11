from flask.ext.wtf import Form
from flask.ext.wtf.html5 import URLField
from wtforms import TextField, BooleanField
from wtforms.validators import required, url

class LinkForm(Form):
	url = URLField(validators=[required(), url()])
	delete_after_usage = BooleanField('delete_after_usage', default=False)


class LoginForm(Form):
	openid = TextField('open_id', validators=[required()])
	remember_me = BooleanField('remember_me', default=False)
