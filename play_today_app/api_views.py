from functools import wraps
from http import HTTPStatus

from flask import jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
)

from . import app, csrf, db
from .constants import (
    ADMIN_BAN_FORBIDDEN_ERROR,
    ADMIN_RIGHTS_REQUIRED_ERROR,
    BOARDGAME_ID_NOT_FOUND_ERROR,
    BOARDGAME_NOT_FOUND_ERROR,
    DB_ERROR_PREFIX,
    GAME_NAME_TAKEN_ERROR,
    MISSING_REVIEW_FIELDS_ERROR,
    NO_CREDENTIALS_ERROR,
    NO_JSON_BODY_ERROR,
    PAGE_DEFAULT,
    PASSWORD_MIN_LENGTH,
    PASSWORD_TOO_SHORT_ERROR,
    PER_PAGE_DEFAULT,
    REVIEW_DELETE_FORBIDDEN_ERROR,
    REVIEW_EDIT_FORBIDDEN_ERROR,
    REVIEW_NOT_FOUND_ERROR,
    STATUS_BLOCKED,
    STATUS_UNBLOCKED,
    USER_BLOCKED_ERROR,
    USER_NOT_FOUND_ERROR,
    USERNAME_INVALID_ERROR,
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
    USERNAME_TAKEN_ERROR,
    WRONG_CREDENTIALS_ERROR,
)
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
                ADMIN_RIGHTS_REQUIRED_ERROR, HTTPStatus.FORBIDDEN
            )

        return function(*args, **kwargs)

    return decorated_function


@app.route("/api/register/", methods=["POST"])
@csrf.exempt
def api_register():
    """Регистрация нового пользователя через API.

    ---
    tags:
      - Auth
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/Credentials'
    responses:
      201:
        description: Пользователь создан
        schema:
          type: object
          properties:
            message:
              type: string
            access_token:
              type: string
            user:
              $ref: '#/definitions/User'
      400:
        description: Ошибка валидации
        schema:
          $ref: '#/definitions/Error'
    """
    data = request.get_json(silent=True)

    if not data or "username" not in data or "password" not in data:
        raise InvalidAPIUsage(NO_CREDENTIALS_ERROR)

    username = data["username"].strip()
    password = data["password"]

    # Валидация
    if not (USERNAME_MIN_LENGTH <= len(username) <= USERNAME_MAX_LENGTH):
        raise InvalidAPIUsage(USERNAME_INVALID_ERROR)
    if len(password) < PASSWORD_MIN_LENGTH:
        raise InvalidAPIUsage(PASSWORD_TOO_SHORT_ERROR)

    if User.query.filter_by(username=username).first():
        raise InvalidAPIUsage(
            USERNAME_TAKEN_ERROR,
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
            f"{DB_ERROR_PREFIX}{str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR
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
    """Авторизация в API и выдача JWT-токена.

    ---
    tags:
      - Auth
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/Credentials'
    responses:
      200:
        description: Успешный вход
        schema:
          $ref: '#/definitions/Token'
      400:
        description: Ошибка валидации
        schema:
          $ref: '#/definitions/Error'
      401:
        description: Неверный логин или пароль
        schema:
          $ref: '#/definitions/Error'
      403:
        description: Пользователь заблокирован
        schema:
          $ref: '#/definitions/Error'
    """
    data = request.get_json(silent=True)

    if not data or "username" not in data or "password" not in data:
        raise InvalidAPIUsage(NO_CREDENTIALS_ERROR)

    user = User.query.filter_by(username=data["username"]).first()

    if not user or not user.check_password(data["password"]):
        raise InvalidAPIUsage(WRONG_CREDENTIALS_ERROR, HTTPStatus.UNAUTHORIZED)

    if not user.is_active:
        raise InvalidAPIUsage(USER_BLOCKED_ERROR, HTTPStatus.FORBIDDEN)

    # Создание токена
    access_token = create_access_token(identity=str(user.id))

    return jsonify({"access_token": access_token}), HTTPStatus.OK


@app.route("/api/boardgames/", methods=["GET"])
def get_boardgames():
    """Получить список всех игр (с пагинацией).

    ---
    tags:
      - Boardgames
    parameters:
      - $ref: '#/parameters/Page'
      - $ref: '#/parameters/PerPage'
    responses:
      200:
        description: Страница со списком игр
        schema:
          type: object
          properties:
            boardgames:
              type: array
              items:
                $ref: '#/definitions/Boardgame'
            pagination:
              $ref: '#/definitions/Pagination'
    """
    page = request.args.get("page", PAGE_DEFAULT, type=int)
    per_page = request.args.get("per_page", PER_PAGE_DEFAULT, type=int)

    pagination = Boardgame.query.paginate(
        page=page, per_page=per_page, error_out=False
    )

    return (
        jsonify(
            {
                "boardgames": [game.to_dict() for game in pagination.items],
                "pagination": get_pagination_meta(pagination),
            }
        ),
        HTTPStatus.OK,
    )


@app.route("/api/boardgames/<int:id>/", methods=["GET"])
def get_boardgame(id):
    """Получить информацию об игре и её отзывах (с пагинацией).

    ---
    tags:
      - Boardgames
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: Идентификатор игры
      - $ref: '#/parameters/Page'
      - $ref: '#/parameters/PerPage'
    responses:
      200:
        description: Игра и страница её отзывов
        schema:
          type: object
          properties:
            boardgame:
              $ref: '#/definitions/Boardgame'
            reviews:
              type: array
              items:
                $ref: '#/definitions/Review'
            pagination:
              $ref: '#/definitions/Pagination'
      404:
        description: Игра не найдена
        schema:
          $ref: '#/definitions/Error'
    """
    boardgame = Boardgame.query.get(id)
    if not boardgame:
        raise InvalidAPIUsage(BOARDGAME_NOT_FOUND_ERROR, HTTPStatus.NOT_FOUND)

    page = request.args.get("page", PAGE_DEFAULT, type=int)
    per_page = request.args.get("per_page", PER_PAGE_DEFAULT, type=int)

    pagination = (
        Review.query.filter_by(boardgame_id=boardgame.id)
        .order_by(Review.timestamp.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return (
        jsonify(
            {
                "boardgame": boardgame.to_dict(),
                "reviews": [review.to_dict() for review in pagination.items],
                "pagination": get_pagination_meta(pagination),
            }
        ),
        HTTPStatus.OK,
    )


@app.route("/api/boardgames/<int:id>/", methods=["PATCH"])
@csrf.exempt  # Отключает CSRF для API
@admin_required_api
def update_boardgame_api(id):
    """Обновить игру (частично).

    ---
    tags:
      - Boardgames
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: Идентификатор игры
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/BoardgamePatch'
    responses:
      200:
        description: Обновлённая игра
        schema:
          type: object
          properties:
            boardgame:
              $ref: '#/definitions/Boardgame'
      400:
        description: Нет JSON-тела или название уже занято
        schema:
          $ref: '#/definitions/Error'
      401:
        description: JWT-токен не передан
        schema:
          $ref: '#/definitions/JwtError'
      422:
        description: JWT-токен недействителен
        schema:
          $ref: '#/definitions/JwtError'
      403:
        description: Недостаточно прав
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Игра не найдена
        schema:
          $ref: '#/definitions/Error'
    """
    boardgame = Boardgame.query.get(id)
    if not boardgame:
        raise InvalidAPIUsage(BOARDGAME_NOT_FOUND_ERROR, HTTPStatus.NOT_FOUND)

    data = request.get_json(silent=True)
    if data is None:
        raise InvalidAPIUsage(NO_JSON_BODY_ERROR)

    if "name" in data and data["name"] != boardgame.name:
        if Boardgame.query.filter_by(name=data["name"]).first():
            raise InvalidAPIUsage(
                GAME_NAME_TAKEN_ERROR, HTTPStatus.BAD_REQUEST
            )

    boardgame.from_dict(data)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InvalidAPIUsage(
            f"{DB_ERROR_PREFIX}{str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    return jsonify({"boardgame": boardgame.to_dict()}), HTTPStatus.OK


@app.route("/api/boardgames/<int:id>/", methods=["DELETE"])
@csrf.exempt
@admin_required_api
def delete_boardgame_api(id):
    """Удалить игру и все её отзывы.

    ---
    tags:
      - Boardgames
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: Идентификатор игры
    responses:
      204:
        description: Игра удалена
      401:
        description: JWT-токен не передан
        schema:
          $ref: '#/definitions/JwtError'
      422:
        description: JWT-токен недействителен
        schema:
          $ref: '#/definitions/JwtError'
      403:
        description: Недостаточно прав
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Игра не найдена
        schema:
          $ref: '#/definitions/Error'
      500:
        description: Ошибка базы данных
        schema:
          $ref: '#/definitions/Error'
    """
    boardgame = Boardgame.query.get(id)
    if not boardgame:
        raise InvalidAPIUsage(BOARDGAME_NOT_FOUND_ERROR, HTTPStatus.NOT_FOUND)

    try:
        db.session.delete(boardgame)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InvalidAPIUsage(
            f"{DB_ERROR_PREFIX}{str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    return "", HTTPStatus.NO_CONTENT


@app.route("/api/reviews/", methods=["POST"])
@csrf.exempt
@jwt_required()
def create_review():
    """Создать отзыв на игру.

    ---
    tags:
      - Reviews
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/ReviewCreate'
    responses:
      201:
        description: Отзыв создан
        schema:
          type: object
          properties:
            review:
              $ref: '#/definitions/Review'
      400:
        description: Нет JSON-тела или не хватает полей
        schema:
          $ref: '#/definitions/Error'
      401:
        description: JWT-токен не передан
        schema:
          $ref: '#/definitions/JwtError'
      422:
        description: JWT-токен недействителен
        schema:
          $ref: '#/definitions/JwtError'
      404:
        description: Игра не найдена
        schema:
          $ref: '#/definitions/Error'
      500:
        description: Ошибка базы данных
        schema:
          $ref: '#/definitions/Error'
    """
    data = request.get_json(silent=True)

    if data is None:
        raise InvalidAPIUsage(NO_JSON_BODY_ERROR)

    if (
        "text" not in data
        or "rating" not in data
        or "boardgame_id" not in data
    ):
        raise InvalidAPIUsage(MISSING_REVIEW_FIELDS_ERROR)

    boardgame = Boardgame.query.get(data["boardgame_id"])
    if not boardgame:
        raise InvalidAPIUsage(
            BOARDGAME_ID_NOT_FOUND_ERROR, HTTPStatus.NOT_FOUND
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
            f"{DB_ERROR_PREFIX}{str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    return jsonify({"review": review.to_dict()}), HTTPStatus.CREATED


@app.route("/api/reviews/<int:id>/", methods=["PATCH"])
@csrf.exempt
@jwt_required()
def update_review(id):
    """Изменить свой отзыв (или любой — для администратора).

    ---
    tags:
      - Reviews
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: Идентификатор отзыва
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/ReviewPatch'
    responses:
      200:
        description: Обновлённый отзыв
        schema:
          type: object
          properties:
            review:
              $ref: '#/definitions/Review'
      400:
        description: В запросе отсутствует JSON тело
        schema:
          $ref: '#/definitions/Error'
      401:
        description: JWT-токен не передан
        schema:
          $ref: '#/definitions/JwtError'
      422:
        description: JWT-токен недействителен
        schema:
          $ref: '#/definitions/JwtError'
      403:
        description: Чужой отзыв менять нельзя
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Отзыв не найден
        schema:
          $ref: '#/definitions/Error'
    """
    review = Review.query.get(id)
    if not review:
        raise InvalidAPIUsage(REVIEW_NOT_FOUND_ERROR, HTTPStatus.NOT_FOUND)

    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)

    # Проверка прав
    if review.user_id != current_user_id and not user.is_admin:
        raise InvalidAPIUsage(
            REVIEW_EDIT_FORBIDDEN_ERROR, HTTPStatus.FORBIDDEN
        )

    data = request.get_json(silent=True)
    if data is None:
        raise InvalidAPIUsage(NO_JSON_BODY_ERROR)

    if "text" in data:
        review.text = data["text"]
    if "rating" in data:
        review.rating = data["rating"]

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InvalidAPIUsage(
            f"{DB_ERROR_PREFIX}{str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    return jsonify({"review": review.to_dict()}), HTTPStatus.OK


@app.route("/api/reviews/<int:id>/", methods=["DELETE"])
@csrf.exempt
@jwt_required()
def delete_review_api(id):
    """Удалить свой отзыв (или любой — для администратора).

    ---
    tags:
      - Reviews
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: Идентификатор отзыва
    responses:
      204:
        description: Отзыв удалён
      401:
        description: JWT-токен не передан
        schema:
          $ref: '#/definitions/JwtError'
      422:
        description: JWT-токен недействителен
        schema:
          $ref: '#/definitions/JwtError'
      403:
        description: Чужой отзыв удалять нельзя
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Отзыв не найден
        schema:
          $ref: '#/definitions/Error'
      500:
        description: Ошибка базы данных
        schema:
          $ref: '#/definitions/Error'
    """
    review = Review.query.get(id)
    if not review:
        raise InvalidAPIUsage(REVIEW_NOT_FOUND_ERROR, HTTPStatus.NOT_FOUND)

    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)

    if review.user_id != current_user_id and not user.is_admin:
        raise InvalidAPIUsage(
            REVIEW_DELETE_FORBIDDEN_ERROR, HTTPStatus.FORBIDDEN
        )

    try:
        db.session.delete(review)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InvalidAPIUsage(
            f"{DB_ERROR_PREFIX}{str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    return "", HTTPStatus.NO_CONTENT


@app.route("/api/users/<int:id>/toggle-status/", methods=["PATCH"])
@csrf.exempt
@admin_required_api
def toggle_user_status_api(id):
    """Забанить/Разбанить пользователя.

    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: Идентификатор пользователя
    responses:
      200:
        description: Результат изменения статуса
        schema:
          $ref: '#/definitions/Message'
      401:
        description: JWT-токен не передан
        schema:
          $ref: '#/definitions/JwtError'
      422:
        description: JWT-токен недействителен
        schema:
          $ref: '#/definitions/JwtError'
      403:
        description: Нужны права администратора
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Пользователь не найден
        schema:
          $ref: '#/definitions/Error'
    """
    user = User.query.get(id)
    if not user:
        raise InvalidAPIUsage(USER_NOT_FOUND_ERROR, HTTPStatus.NOT_FOUND)

    if user.is_admin:
        raise InvalidAPIUsage(ADMIN_BAN_FORBIDDEN_ERROR, HTTPStatus.FORBIDDEN)

    user.is_active = not user.is_active
    status = STATUS_UNBLOCKED if user.is_active else STATUS_BLOCKED

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise InvalidAPIUsage(
            f"{DB_ERROR_PREFIX}{str(e)}", HTTPStatus.INTERNAL_SERVER_ERROR
        )

    return (
        jsonify({"message": f"Пользователь {user.username} {status}"}),
        HTTPStatus.OK,
    )


@app.route("/api/users/", methods=["GET"])
@admin_required_api
def get_users_api():
    """Получить список всех пользователей (только админ, с пагинацией).

    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - $ref: '#/parameters/Page'
      - $ref: '#/parameters/PerPage'
    responses:
      200:
        description: Страница со списком пользователей
        schema:
          type: object
          properties:
            users:
              type: array
              items:
                $ref: '#/definitions/User'
            pagination:
              $ref: '#/definitions/Pagination'
      401:
        description: JWT-токен не передан
        schema:
          $ref: '#/definitions/JwtError'
      422:
        description: JWT-токен недействителен
        schema:
          $ref: '#/definitions/JwtError'
      403:
        description: Нужны права администратора
        schema:
          $ref: '#/definitions/Error'
    """
    page = request.args.get("page", PAGE_DEFAULT, type=int)
    per_page = request.args.get("per_page", PER_PAGE_DEFAULT, type=int)

    pagination = User.query.paginate(
        page=page, per_page=per_page, error_out=False
    )

    return (
        jsonify(
            {
                "users": [user.to_dict() for user in pagination.items],
                "pagination": get_pagination_meta(pagination),
            }
        ),
        HTTPStatus.OK,
    )


@app.route("/api/users/me/", methods=["GET"])
@jwt_required()
def get_current_user_api():
    """Получить информацию о себе и свои отзывы (с пагинацией).

    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - $ref: '#/parameters/Page'
      - $ref: '#/parameters/PerPage'
    responses:
      200:
        description: Профиль и страница отзывов
        schema:
          type: object
          properties:
            user:
              $ref: '#/definitions/User'
            reviews:
              type: array
              items:
                $ref: '#/definitions/Review'
            pagination:
              $ref: '#/definitions/Pagination'
      401:
        description: JWT-токен не передан
        schema:
          $ref: '#/definitions/JwtError'
      422:
        description: JWT-токен недействителен
        schema:
          $ref: '#/definitions/JwtError'
      404:
        description: Пользователь не найден
        schema:
          $ref: '#/definitions/Error'
    """
    current_user_id = int(get_jwt_identity())
    user = User.query.get(current_user_id)

    if not user:
        raise InvalidAPIUsage(USER_NOT_FOUND_ERROR, HTTPStatus.NOT_FOUND)

    page = request.args.get("page", PAGE_DEFAULT, type=int)
    per_page = request.args.get("per_page", PER_PAGE_DEFAULT, type=int)

    pagination = user.reviews.order_by(Review.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return (
        jsonify(
            {
                "user": user.to_dict(),
                "reviews": [review.to_dict() for review in pagination.items],
                "pagination": get_pagination_meta(pagination),
            }
        ),
        HTTPStatus.OK,
    )
