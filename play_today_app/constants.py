from datetime import timedelta

# Пользователь
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 64
PASSWORD_MIN_LENGTH = 6

# Настольные игры
GAME_NAME_MIN_LENGTH = 1
GAME_NAME_MAX_LENGTH = 128
MIN_PLAYERS_DEFAULT = 1
MIN_AGE_DEFAULT = 0
PLAYTIME_MIN_MINUTES = 1

# Отзывы
RATING_MIN = 1
RATING_MAX = 10
REVIEW_TEXT_MIN_LENGTH = 10
RATING_AVERAGE_PRECISION = 1
EMPTY_AVERAGE_RATING = 0.0

ALLOWED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "gif", "bmp"]

# Поля, которые принимает API при создании/изменении сущностей
REVIEW_REQUIRED_FIELDS = ("text", "rating", "boardgame_id")
BOARDGAME_EDITABLE_FIELDS = (
    "name",
    "description",
    "min_players",
    "max_players",
    "min_age",
    "playtime_minutes",
    "is_available",
)

# Пагинация
PAGE_DEFAULT = 1
PER_PAGE_DEFAULT = 10
PER_PAGE_ADMIN_DEFAULT = 100

# JWT
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

# Категории flash-сообщений (классы Bootstrap)
FLASH_SUCCESS = "success"
FLASH_DANGER = "danger"
FLASH_INFO = "info"
FLASH_WARNING = "warning"

# Статусы блокировки пользователя
STATUS_BLOCKED = "заблокирован"
STATUS_UNBLOCKED = "разблокирован"

# Сообщения об ошибках API
DB_ERROR_PREFIX = "Ошибка базы данных: "
SAVE_ERROR_PREFIX = "Ошибка при сохранении: "
DELETE_ERROR_PREFIX = "Ошибка при удалении: "
NO_JSON_BODY_ERROR = "В запросе отсутствует JSON тело"
NO_CREDENTIALS_ERROR = "Не указаны username или password"
USERNAME_INVALID_ERROR = (
    f"Логин должен быть от {USERNAME_MIN_LENGTH} "
    f"до {USERNAME_MAX_LENGTH} символов"
)
PASSWORD_TOO_SHORT_ERROR = (
    f"Пароль должен быть не короче {PASSWORD_MIN_LENGTH} символов"
)
USERNAME_TAKEN_ERROR = "Пользователь с таким именем уже существует"
USER_NOT_FOUND_ERROR = "Пользователь не найден"
USER_BLOCKED_ERROR = "Пользователь заблокирован"
WRONG_CREDENTIALS_ERROR = "Неверный логин или пароль"
ADMIN_RIGHTS_REQUIRED_ERROR = "Требуются права администратора"
ADMIN_BAN_FORBIDDEN_ERROR = "Нельзя забанить администратора"
BOARDGAME_NOT_FOUND_ERROR = "Игра с указанным id не найдена"
BOARDGAME_ID_NOT_FOUND_ERROR = "Игра с указанным boardgame_id не найдена"
GAME_NAME_TAKEN_ERROR = "Игра с таким названием уже существует"
REVIEW_NOT_FOUND_ERROR = "Отзыв с указанным id не найден"
REVIEW_EDIT_FORBIDDEN_ERROR = "Вы не можете редактировать чужой отзыв"
REVIEW_DELETE_FORBIDDEN_ERROR = "Вы не можете удалить чужой отзыв"
MISSING_REVIEW_FIELDS_ERROR = (
    "В запросе отсутствуют обязательные поля: "
    + ", ".join(REVIEW_REQUIRED_FIELDS)
)

# Сообщения и подписи форм
REQUIRED_FIELD_MESSAGE = "Обязательное поле"
REVIEW_TEXT_TOO_SHORT_MESSAGE = (
    f"Отзыв должен быть не короче {REVIEW_TEXT_MIN_LENGTH} символов"
)
ALLOWED_EXTENSIONS_MESSAGE = (
    "Выберите файлы с расширением "
    + ", ".join(f".{ext}" for ext in ALLOWED_IMAGE_EXTENSIONS)
)
RATING_FIELD_LABEL = f"Оценка (от {RATING_MIN} до {RATING_MAX})"

# CLI-команды
DEFAULT_CSV_FILENAME = "boardgames.csv"
CSV_TRUE_VALUE = "true"

# Dropbox
BEARER_PREFIX = "Bearer "
DROPBOX_DL_PARAM = "&dl=0"
DROPBOX_RAW_PARAM = "&raw=1"
