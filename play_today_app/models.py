from typing import TYPE_CHECKING

from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import CheckConstraint

from . import db


if TYPE_CHECKING:
    from flask_sqlalchemy.model import Model   # для MyPy
else:
    Model = db.Model


class User(UserMixin, Model):
    """Модель пользователя."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Связь с отзывами (один ко многим)
    reviews = db.relationship('Review', backref='author', lazy='dynamic')

    def set_password(self, password):
        """Хеширует и сохраняет пароль."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Проверяет, совпадает ли пароль с хешем."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return dict(
            id=self.id,
            username=self.username,
            is_admin=self.is_admin,
            is_active=self.is_active
        )


class Boardgame(Model):
    """Модель настольной игры."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    min_players = db.Column(db.Integer, nullable=False, default=1)
    max_players = db.Column(db.Integer, nullable=False)
    min_age = db.Column(db.Integer, nullable=False, default=0)
    playtime_minutes = db.Column(db.Integer, nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)

    reviews = db.relationship(
        'Review',
        backref='boardgame',
        lazy='select',
        cascade='all, delete-orphan'
    )

    @property
    def average_rating(self):
        """Вычисляет средний рейтинг игры на основе её отзывов."""
        if not self.reviews:
            return 0.0

        return round(
            sum(review.rating for review in self.reviews) / len(self.reviews),
            1
        )

    def to_dict(self):
        return dict(
            id=self.id,
            name=self.name,
            description=self.description,
            min_players=self.min_players,
            max_players=self.max_players,
            min_age=self.min_age,
            playtime_minutes=self.playtime_minutes,
            is_available=self.is_available,
            average_rating=self.average_rating
        )

    def from_dict(self, data):
        fields = [
            'name', 'description', 'min_players', 'max_players',
            'min_age', 'playtime_minutes', 'is_available'
        ]
        for field in fields:
            if field in data:
                setattr(self, field, data[field])


class Review(Model):
    """Модель отзыва на игру."""
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    __table_args__ = (
        CheckConstraint(
            'rating >= 1 AND rating <= 10', name='check_rating_range'
        ),
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='SET NULL'), 
        nullable=True
    )
    images = db.Column(db.JSON)
    timestamp = db.Column(
        db.DateTime(timezone=True),
        index=True,
        default=lambda: datetime.now(timezone.utc)
    )

    boardgame_id = db.Column(
        db.Integer, db.ForeignKey('boardgame.id'), nullable=False
    )

    def to_dict(self):
        return dict(
            id=self.id,
            text=self.text,
            rating=self.rating,
            author=self.author.username if self.author else None,
            timestamp=self.timestamp.isoformat() if self.timestamp else None,
            boardgame_id=self.boardgame_id,
            boardgame_name=self.boardgame.name if self.boardgame else None
        )

    def from_dict(self, data):
        for field in ['text', 'rating', 'boardgame_id']:
            if field in data:
                setattr(self, field, data[field])
