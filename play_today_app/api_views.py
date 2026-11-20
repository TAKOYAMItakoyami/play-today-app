from http import HTTPStatus
from flask import jsonify

from . import app
from .models import Boardgame, Review


@app.route('/api/boardgames/', methods=['GET'])
def get_boardgames():
    """Временный эндпоинт для получения списка всех игр."""
    boardgames = Boardgame.query.all()
    return jsonify(
        {'boardgames': [game.to_dict() for game in boardgames]}
    ), HTTPStatus.OK


@app.route('/api/boardgames/<int:id>/reviews/', methods=['GET'])
def get_boardgame_reviews(id):
    """Временный эндпоинт для получения отзывов конкретной игры."""
    boardgame = Boardgame.query.get_or_404(id)
    reviews = Review.query.filter_by(boardgame_id=boardgame.id).all()
    return jsonify(
        {'reviews': [review.to_dict() for review in reviews]}
    ), HTTPStatus.OK
