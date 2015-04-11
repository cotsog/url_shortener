from app import db

ROLE_USER = 0
ROLE_ADMIN = 1


class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	nick = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	role = db.Column(db.SmallInteger, default=ROLE_USER)
	urls = db.relationship('ShortUrl', backref='creator', lazy='dynamic')

	def __repr__(self):
		return '<User {0}>'.format(self.nick)


class ShortUrl(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	url = db.Column(db.String(20))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	full_url = db.relationship('FullUrl', backref='short_url', uselist=False)

	def __repr__(self):
		return '<ShortUrl: {0}>'.format(self.url)


class FullUrl(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	url = db.Column(db.String(1024))
	short_url_id = db.Column(db.Integer, db.ForeignKey('short_url.id'))

	def __repr__(self):
		return '<Full url: {0}>'.format(self.url)


