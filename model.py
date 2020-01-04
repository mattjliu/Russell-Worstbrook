from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from env import SECRET_KEY, USERS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.secret_key = SECRET_KEY

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    player = db.Column(db.String(50), nullable=False, default='Russell Westbrook')
    new_user = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return f'User({self.phone_number}, {self.player}, new_user: {self.new_user})'


if __name__ == '__main__':
    # Populate db using config file
    db.drop_all()
    db.create_all()

    for user in USERS:
        db.session.add(User(phone_number=user['phone_number'], player=user['player'], new_user=user['new_user']))

    db.session.commit()
