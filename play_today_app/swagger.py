"""Шаблон спецификации Swagger (OpenAPI 2.0) для API приложения.

Описание общей информации и переиспользуемых схем (`definitions`).
"""

from .constants import (
    PASSWORD_MIN_LENGTH,
    PER_PAGE_DEFAULT,
    RATING_MAX,
    RATING_MIN,
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
)

PAGE_PARAM = {
    "name": "page",
    "in": "query",
    "type": "integer",
    "default": 1,
    "description": "Номер страницы (по умолчанию 1)",
}

PER_PAGE_PARAM = {
    "name": "per_page",
    "in": "query",
    "type": "integer",
    "default": PER_PAGE_DEFAULT,
    "description": f"Элементов на странице (по умолчанию {PER_PAGE_DEFAULT})",
}

ERROR_DEFINITION = {
    "type": "object",
    "properties": {
        "message": {
            "type": "string",
            "description": "Текст ошибки",
            "example": "Игра с указанным id не найдена",
        }
    },
}

USER_DEFINITION = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "example": 1},
        "username": {"type": "string", "example": "boardgamer"},
        "is_admin": {"type": "boolean", "example": False},
        "is_active": {"type": "boolean", "example": True},
    },
}

BOARDGAME_DEFINITION = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "example": 1},
        "name": {"type": "string", "example": "Каркассон"},
        "description": {"type": "string", "example": "Выкладываем мир"},
        "min_players": {"type": "integer", "example": 2},
        "max_players": {"type": "integer", "example": 5},
        "min_age": {"type": "integer", "example": 7},
        "playtime_minutes": {"type": "integer", "example": 40},
        "is_available": {"type": "boolean", "example": True},
        "average_rating": {
            "type": "number",
            "description": "Средний рейтинг по отзывам, 0 если их нет",
            "example": 8.5,
        },
    },
}

REVIEW_DEFINITION = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "example": 1},
        "text": {"type": "string", "example": "Отличная игра!"},
        "rating": {
            "type": "integer",
            "minimum": RATING_MIN,
            "maximum": RATING_MAX,
            "example": 9,
        },
        "author": {
            "type": "string",
            "nullable": True,
            "example": "boardgamer",
        },
        "timestamp": {
            "type": "string",
            "nullable": True,
            "example": "2026-11-23T10:15:30+00:00",
        },
        "boardgame_id": {"type": "integer", "example": 1},
        "boardgame_name": {"type": "string", "example": "Каркассон"},
    },
}

PAGINATION_DEFINITION = {
    "type": "object",
    "properties": {
        "page": {"type": "integer", "example": 1},
        "per_page": {"type": "integer", "example": PER_PAGE_DEFAULT},
        "total_pages": {"type": "integer", "example": 4},
        "total_items": {"type": "integer", "example": 37},
        "has_next": {"type": "boolean", "example": True},
        "has_prev": {"type": "boolean", "example": False},
    },
}

CREDENTIALS_DEFINITION = {
    "type": "object",
    "required": ["username", "password"],
    "properties": {
        "username": {
            "type": "string",
            "minLength": USERNAME_MIN_LENGTH,
            "maxLength": USERNAME_MAX_LENGTH,
        },
        "password": {
            "type": "string",
            "minLength": PASSWORD_MIN_LENGTH,
        },
    },
}

TOKEN_DEFINITION = {
    "type": "object",
    "properties": {
        "access_token": {
            "type": "string",
            "description": "JWT, действителен 1 час",
            "example": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        }
    },
}

MESSAGE_DEFINITION = {
    "type": "object",
    "properties": {
        "message": {"type": "string", "example": "OK"},
    },
}

JWT_ERROR_DEFINITION = {
    "type": "object",
    "properties": {
        "msg": {
            "type": "string",
            "description": "Описание ошибки от Flask-JWT-Extended",
            "example": "Missing Authorization Header",
        }
    },
}

REVIEW_CREATE_DEFINITION = {
    "type": "object",
    "required": ["text", "rating", "boardgame_id"],
    "properties": {
        "text": {"type": "string", "example": "Отличная игра!"},
        "rating": {
            "type": "integer",
            "minimum": RATING_MIN,
            "maximum": RATING_MAX,
            "example": 9,
        },
        "boardgame_id": {"type": "integer", "example": 1},
    },
}

REVIEW_PATCH_DEFINITION = {
    "type": "object",
    "properties": {
        "text": {"type": "string", "example": "Исправленный отзыв"},
        "rating": {
            "type": "integer",
            "minimum": RATING_MIN,
            "maximum": RATING_MAX,
            "example": 8,
        },
    },
}

BOARDGAME_PATCH_DEFINITION = {
    "type": "object",
    "description": "Любое количество полей игры",
    "properties": {
        "name": {"type": "string", "example": "Каркассон"},
        "description": {"type": "string", "example": "Новое описание"},
        "min_players": {"type": "integer", "example": 2},
        "max_players": {"type": "integer", "example": 5},
        "min_age": {"type": "integer", "example": 7},
        "playtime_minutes": {"type": "integer", "example": 40},
        "is_available": {"type": "boolean", "example": True},
    },
}

SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "Play Today API",
        "description": (
            "API сервиса подбора настольных игр: регистрация и вход, "
            "каталог игр, отзывы пользователей и административные "
            "эндпоинты. Доступ к защищённым эндпоинтам — по JWT-токену "
            "в заголовке Authorization."
        ),
        "version": "1.0.0",
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": (
                "Введите токен вида `Bearer <access_token>`. "
                "Его выдают /api/register/ и /api/login/."
            ),
        }
    },
    "parameters": {
        "Page": PAGE_PARAM,
        "PerPage": PER_PAGE_PARAM,
    },
    "definitions": {
        "Error": ERROR_DEFINITION,
        "JwtError": JWT_ERROR_DEFINITION,
        "User": USER_DEFINITION,
        "Boardgame": BOARDGAME_DEFINITION,
        "BoardgamePatch": BOARDGAME_PATCH_DEFINITION,
        "Review": REVIEW_DEFINITION,
        "ReviewCreate": REVIEW_CREATE_DEFINITION,
        "ReviewPatch": REVIEW_PATCH_DEFINITION,
        "Pagination": PAGINATION_DEFINITION,
        "Credentials": CREDENTIALS_DEFINITION,
        "Token": TOKEN_DEFINITION,
        "Message": MESSAGE_DEFINITION,
    },
}
