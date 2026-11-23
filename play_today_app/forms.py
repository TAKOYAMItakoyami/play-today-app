from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import (
    BooleanField,
    IntegerField,
    PasswordField,
    RadioField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, EqualTo, Length, NumberRange

from .constants import (
    ALLOWED_EXTENSIONS_MESSAGE,
    ALLOWED_IMAGE_EXTENSIONS,
    GAME_NAME_MAX_LENGTH,
    GAME_NAME_MIN_LENGTH,
    MIN_AGE_DEFAULT,
    MIN_PLAYERS_DEFAULT,
    PASSWORD_MIN_LENGTH,
    PLAYTIME_MIN_MINUTES,
    RATING_FIELD_LABEL,
    RATING_MAX,
    RATING_MIN,
    REQUIRED_FIELD_MESSAGE,
    REVIEW_TEXT_MIN_LENGTH,
    REVIEW_TEXT_TOO_SHORT_MESSAGE,
    USERNAME_MAX_LENGTH,
    USERNAME_MIN_LENGTH,
)


class RegisterForm(FlaskForm):
    """Форма регистрации нового пользователя."""

    username = StringField(
        label="Ваше имя (логин)",
        validators=[
            DataRequired(message=REQUIRED_FIELD_MESSAGE),
            Length(USERNAME_MIN_LENGTH, USERNAME_MAX_LENGTH),
        ],
    )
    password = PasswordField(
        label="Пароль",
        validators=[
            DataRequired(message=REQUIRED_FIELD_MESSAGE),
            Length(min=PASSWORD_MIN_LENGTH),
        ],
    )
    password_confirm = PasswordField(
        label="Повторите пароль",
        validators=[
            DataRequired(),
            EqualTo("password", message="Пароли должны совпадать"),
        ],
    )
    submit = SubmitField(label="Зарегистрироваться")


class LoginForm(FlaskForm):
    """Форма входа."""

    username = StringField(
        label="Ваше имя (логин)", validators=[DataRequired()]
    )
    password = PasswordField(label="Пароль", validators=[DataRequired()])
    submit = SubmitField(label="Войти")


class ReviewForm(FlaskForm):
    """Форма для добавления отзыва на настольную игру."""

    # Выбор игры из списка (заполняется динамически в views.py)
    boardgame_id = SelectField(
        label="Выберите настольную игру",
        coerce=int,  # Превращает строку из HTML в число (int) для базы данных
        validators=[DataRequired(message="Выберите игру")],
    )

    rating = RadioField(
        label=RATING_FIELD_LABEL,
        choices=[(i, str(i)) for i in range(RATING_MIN, RATING_MAX + 1)],
        coerce=int,
        validators=[DataRequired(message="Поставьте оценку")],
    )

    text = TextAreaField(
        label="Напишите отзыв",
        validators=[
            DataRequired(message=REQUIRED_FIELD_MESSAGE),
            Length(
                min=REVIEW_TEXT_MIN_LENGTH,
                message=REVIEW_TEXT_TOO_SHORT_MESSAGE,
            ),
        ],
    )

    images = MultipleFileField(
        label="Прикрепите фотографии",
        validators=[
            FileAllowed(
                ALLOWED_IMAGE_EXTENSIONS,
                message=ALLOWED_EXTENSIONS_MESSAGE,
            )
        ],
    )

    submit = SubmitField(label="Опубликовать отзыв")


class BoardgameForm(FlaskForm):
    """Форма для добавления новой настольной игры (только для админа)."""

    name = StringField(
        label="Название игры",
        validators=[
            DataRequired(message=REQUIRED_FIELD_MESSAGE),
            Length(GAME_NAME_MIN_LENGTH, GAME_NAME_MAX_LENGTH),
        ],
    )
    description = TextAreaField(
        label="Описание",
        validators=[DataRequired(message=REQUIRED_FIELD_MESSAGE)],
    )
    min_players = IntegerField(
        label="Мин. игроков",
        validators=[DataRequired(), NumberRange(min=MIN_PLAYERS_DEFAULT)],
    )
    max_players = IntegerField(
        label="Макс. игроков",
        validators=[DataRequired(), NumberRange(min=MIN_PLAYERS_DEFAULT)],
    )
    min_age = IntegerField(
        label="Мин. возраст",
        validators=[DataRequired(), NumberRange(min=MIN_AGE_DEFAULT)],
    )
    playtime_minutes = IntegerField(
        label="Время партии (мин)",
        validators=[DataRequired(), NumberRange(min=PLAYTIME_MIN_MINUTES)],
    )
    is_available = BooleanField(label="Доступна для игр", default=True)
    submit = SubmitField(label="Добавить игру")
