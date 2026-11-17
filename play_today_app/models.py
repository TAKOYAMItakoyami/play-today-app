from datetime import datetime, timezone
from sqlalchemy import CheckConstraint

from . import db


class Boardgame(db.Model):
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


class Review(db.Model):
    """Модель отзыва на игру."""
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    __table_args__ = (
        CheckConstraint(
            'rating >= 1 AND rating <= 10', name='check_rating_range'
        ),
    )

    author = db.Column(db.String(64), nullable=False)
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
            author=self.author,
            timestamp=self.timestamp.isoformat() if self.timestamp else None,
            boardgame_id=self.boardgame_id,
            boardgame_name=self.boardgame.name if self.boardgame else None
        )

    def from_dict(self, data):
        for field in ['text', 'rating', 'author', 'boardgame_id']:
            if field in data:
                setattr(self, field, data[field])
