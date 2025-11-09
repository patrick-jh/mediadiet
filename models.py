from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        """Hash and store the password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify a password against the stored hash."""
        return check_password_hash(self.password_hash, password)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    media_type = db.Column(db.String(50), nullable=False)
    genre = db.Column(db.String(50))
    year_released = db.Column(db.Integer)
    rating = db.Column(db.Integer)
    notes = db.Column(db.Text)
    dnf = db.Column(db.Boolean, default=False)
    recommended = db.Column(db.Boolean, default=False)
    foreign = db.Column(db.Boolean, default=False)
    country = db.Column(db.String(100))
    source = db.Column(db.String(100))
    date = db.Column(db.Date, nullable=False)
