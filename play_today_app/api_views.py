from functools import wraps
from http import HTTPStatus

from flask import jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
)

from . import app, csrf, db
from .error_handlers import InvalidAPIUsage
from .models import Boardgame, Review, User


def get_pagination_meta(pagination):
    """Вспомогательная функция для формирования метаданных пагинации."""
    return {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total_pages": pagination.pages,
        "total_items": pagination.total,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    }


def admin_required_api(function):
    """Декоратор: требует JWT токен и права администратора."""

    @wraps(function)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))

        if not user or not user.is_admin:
            raise InvalidAPIUsage(
                "Требуются права администратора", HTTPStatus.FORBIDDEN
            )

        return function(*args, **kwargs)

    return decorated_function


@app.route("/api/register/", methods=["POST"])
@csrf.exempt
def api_register():
    """Регистрация нового пользователя через API."""
    data = request.get_json(silent=True)

    if not data or "username" not in data or "password" not in data:
        raise InvalidAPIUsage("Не указаны username или password")

    username = data["username"].strip()
    password = data["password"]

    # Валидация
    if len(username) < 3 or len(username) > 64:
        raise InvalidAPIUsage("Логин должен быть от 3 до 64 символов")
    if len(password) < 6:
        raise InvalidAPIUsage("Пароль должен быть не короче 6 символов")

    if User.query.filter_by(username=username).first():
        raise InvalidAPIUsage(
            "Пользователь с таким именем уже существует",
            HTTPStatus.BAD_REQUEST,
        )

    new_user = User(username=username)
    new_user.set_password(password)

    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InvalidAPIUsage(
            f"Ошибка базы данных: {str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    access_token = create_access_token(identity=str(new_user.id))

    return (
        jsonify(
            {
                "message": "Пользователь успешно зарегистрирован",
                "access_token": access_token,
                "user": {"id": new_user.id, "username": new_user.username},
            }
        ),
        HTTPStatus.CREATED,
    )


@app.route("/api/login/", methods=["POST"])
@csrf.exempt
def api_login():
    """Авторизация в API и выдача JWT-токена."""
    data = request.get_json(silent=True)

    if not data or "username" not in data or "password" not in data:
        raise InvalidAPIUsage("Не указаны username или password")

    user = User.query.filter_by(username=data["username"]).first()

    if not user or not user.check_password(data["password"]):
        raise InvalidAPIUsage(
            "Неверный логин или пароль", HTTPStatus.UNAUTHORIZED
        )

    if not user.is_active:
        raise InvalidAPIUsage(
            "Пользователь заблокирован", HTTPStatus.FORBIDDEN
        )

    # Создание токена
    access_token = create_access_token(identity=str(user.id))

    return jsonify({"access_token": access_token}), HTTPStatus.OK


@app.route("/api/boardgames/", methods=["GET"])
def get_boardgames():
    """Получить список всех игр (с пагинацией)."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    pagination = Boardgame.query.paginate(
        page=page, per_page=per_page, error_out=False
    )

    return (
        jsonify({
            "boardgames": [game.to_dict() for game in pagination.items],
            "pagination": get_pagination_meta(pagination)
        }),
        HTTPStatus.OK,
    )


@app.route("/api/boardgames/<int:id>/", methods=["GET"])
def get_boardgame(id):
    """Получить информацию об игре и её отзывах (с пагинацией)."""
    boardgame = Boardgame.query.get(id)
    if not boardgame:
        raise InvalidAPIUsage(
            "Игра с указанным id не найдена", HTTPStatus.NOT_FOUND
        )

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    pagination = (
        Review.query.filter_by(boardgame_id=boardgame.id)
        .order_by(Review.timestamp.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return (
        jsonify({
            "boardgame": boardgame.to_dict(),
            "reviews": [review.to_dict() for review in pagination.items],
            "pagination": get_pagination_meta(pagination)
        }),
        HTTPStatus.OK,
    )


@app.route("/api/boardgames/<int:id>/", methods=["PATCH"])
@csrf.exempt  # Отключает CSRF для API
@admin_required_api
def update_boardgame_api(id):
    """Обновить игру (частично)."""
    boardgame = Boardgame.query.get(id)
    if not boardgame:
        raise InvalidAPIUsage(
            "Игра с указанным id не найдена", HTTPStatus.NOT_FOUND
        )

    data = request.get_json(silent=True)
    if data is None:
        raise InvalidAPIUsage("В запросе отсутствует JSON тело")

    if "name" in data and data["name"] != boardgame.name:
        if Boardgame.query.filter_by(name=data["name"]).first():
            raise InvalidAPIUsage(
                "Игра с таким названием уже существует", HTTPStatus.BAD_REQUEST
            )

    boardgame.from_dict(data)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InvalidAPIUsage(
            f"Ошибка базы данных: {str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    return jsonify({"boardgame": boardgame.to_dict()}), HTTPStatus.OK


@app.route("/api/boardgames/<int:id>/", methods=["DELETE"])
@csrf.exempt
@admin_required_api
def delete_boardgame_api(id):
    """Удалить игру и все её отзывы."""
    boardgame = Boardgame.query.get(id)
    if not boardgame:
        raise InvalidAPIUsage(
            "Игра с указанным id не найдена", HTTPStatus.NOT_FOUND
        )

    try:
        db.session.delete(boardgame)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InvalidAPIUsage(
            f"Ошибка базы данных: {str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    return "", HTTPStatus.NO_CONTENT


@app.route("/api/reviews/", methods=["POST"])
@csrf.exempt
@jwt_required()
def create_review():
    data = request.get_json(silent=True)

    if data is None:
        raise InvalidAPIUsage("В запросе отсутствует JSON тело")

    if (
        "text" not in data
        or "rating" not in data
        or "boardgame_id" not in data
    ):
        raise InvalidAPIUsage(
            "В запросе отсутствуют обязательные поля: "
            "text, rating, boardgame_id"
        )

    boardgame = Boardgame.query.get(data["boardgame_id"])
    if not boardgame:
        raise InvalidAPIUsage(
            "Игра с указанным boardgame_id не найдена", HTTPStatus.NOT_FOUND
        )

    current_user_id = get_jwt_identity()

    review = Review(
        text=data["text"],
        rating=data["rating"],
        boardgame_id=data["boardgame_id"],
        user_id=int(current_user_id),
    )

    try:
        db.session.add(review)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InvalidAPIUsage(
            f"Ошибка базы данных: {str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    return jsonify({"review": review.to_dict()}), HTTPStatus.CREATED


@app.route("/api/reviews/<int:id>/", methods=["PATCH"])
@csrf.exempt
@jwt_required()
def update_review(id):
    review = Review.query.get(id)
    if not review:
        raise InvalidAPIUsage(
            "Отзыв с указанным id не найден", HTTPStatus.NOT_FOUND
        )

    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)

    # Проверка прав
    if review.user_id != current_user_id and not user.is_admin:
        raise InvalidAPIUsage(
            "Вы не можете редактировать чужой отзыв", HTTPStatus.FORBIDDEN
        )

    data = request.get_json(silent=True)
    if data is None:
        raise InvalidAPIUsage("В запросе отсутствует JSON тело")

    if "text" in data:
        review.text = data["text"]
    if "rating" in data:
        review.rating = data["rating"]

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InvalidAPIUsage(
            f"Ошибка базы данных: {str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    return jsonify({"review": review.to_dict()}), HTTPStatus.OK


@app.route("/api/reviews/<int:id>/", methods=["DELETE"])
@csrf.exempt
@jwt_required()
def delete_review_api(id):
    review = Review.query.get(id)
    if not review:
        raise InvalidAPIUsage(
            "Отзыв с указанным id не найден", HTTPStatus.NOT_FOUND
        )

    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)

    if review.user_id != current_user_id and not user.is_admin:
        raise InvalidAPIUsage(
            "Вы не можете удалить чужой отзыв", HTTPStatus.FORBIDDEN
        )

    try:
        db.session.delete(review)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InvalidAPIUsage(
            f"Ошибка базы данных: {str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    return "", HTTPStatus.NO_CONTENT


@app.route("/api/users/<int:id>/toggle-status/", methods=["PATCH"])
@csrf.exempt
@admin_required_api
def toggle_user_status_api(id):
    """Забанить/Разбанить пользователя."""
    user = User.query.get(id)
    if not user:
        raise InvalidAPIUsage("Пользователь не найден", HTTPStatus.NOT_FOUND)

    if user.is_admin:
        raise InvalidAPIUsage(
            "Нельзя забанить администратора", HTTPStatus.FORBIDDEN
        )

    user.is_active = not user.is_active
    status = "разблокирован" if user.is_active else "заблокирован"

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InvalidAPIUsage(
            f"Ошибка базы данных: {str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    return (
        jsonify({"message": f"Пользователь {user.username} {status}"}),
        HTTPStatus.OK,
    )


@app.route("/api/users/", methods=["GET"])
@admin_required_api
def get_users_api():
    """Получить список всех пользователей (только админ, с пагинацией)."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    pagination = User.query.paginate(
        page=page, per_page=per_page, error_out=False
    )

    return (
        jsonify({
            "users": [user.to_dict() for user in pagination.items],
            "pagination": get_pagination_meta(pagination)
        }),
        HTTPStatus.OK,
    )


@app.route("/api/users/me/", methods=["GET"])
@jwt_required()
def get_current_user_api():
    """Получить информацию о себе и свои отзывы (с пагинацией)."""
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)

    if not user:
        raise InvalidAPIUsage("Пользователь не найден", HTTPStatus.NOT_FOUND)

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    pagination = user.reviews.order_by(Review.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return (
        jsonify({
            "user": user.to_dict(),
            "reviews": [review.to_dict() for review in pagination.items],
            "pagination": get_pagination_meta(pagination)
        }),
        HTTPStatus.OK,
    )
