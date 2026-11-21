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
    TextAreaField
)
from wtforms.validators import DataRequired, Length, EqualTo, NumberRange


class RegisterForm(FlaskForm):
    """Форма регистрации нового пользователя."""
    username = StringField(
        label='Ваше имя (логин)',
        validators=[DataRequired(message='Обязательное поле'), Length(3, 64)]
    )
    password = PasswordField(
        label='Пароль',
        validators=[DataRequired(message='Обязательное поле'), Length(min=6)]
    )
    password_confirm = PasswordField(
        label='Повторите пароль',
        validators=[
            DataRequired(),
            EqualTo('password', message='Пароли должны совпадать')
        ]
    )
    submit = SubmitField(label='Зарегистрироваться')


class LoginForm(FlaskForm):
    """Форма входа."""
    username = StringField(
        label='Ваше имя (логин)',
        validators=[DataRequired()]
    )
    password = PasswordField(label='Пароль', validators=[DataRequired()])
    submit = SubmitField(label='Войти')


class ReviewForm(FlaskForm):
    """Форма для добавления отзыва на настольную игру."""

    # Выбор игры из списка (заполняется динамически в views.py)
    boardgame_id = SelectField(
        label='Выберите настольную игру',
        coerce=int,  # Превращает строку из HTML в число (int) для базы данных
        validators=[DataRequired(message='Выберите игру')]
    )

    rating = RadioField(
        label='Оценка (от 1 до 10)',
        choices=[(i, str(i)) for i in range(1, 11)],
        coerce=int,
        validators=[DataRequired(message='Поставьте оценку')]
    )

    text = TextAreaField(
        label='Напишите отзыв',
        validators=[
            DataRequired(message='Обязательное поле'),
            Length(min=10, message='Отзыв должен быть не короче 10 символов')
        ]
    )

    images = MultipleFileField(
        label='Прикрепите фотографии',
        validators=[
            FileAllowed(
                ['jpg', 'jpeg', 'png', 'gif', 'bmp'],
                message=(
                    'Выберите файлы с расширением '
                    '.jpg, .jpeg, .png, .gif или .bmp'
                )
            )
        ]
    )

    submit = SubmitField(label='Опубликовать отзыв')


class BoardgameForm(FlaskForm):
    """Форма для добавления новой настольной игры (только для админа)."""
    name = StringField(
        label='Название игры',
        validators=[DataRequired(message='Обязательное поле'), Length(1, 128)]
    )
    description = TextAreaField(
        label='Описание',
        validators=[DataRequired(message='Обязательное поле')]
    )
    min_players = IntegerField(
        label='Мин. игроков',
        validators=[DataRequired(), NumberRange(min=1)]
    )
    max_players = IntegerField(
        label='Макс. игроков',
        validators=[DataRequired(), NumberRange(min=1)]
    )
    min_age = IntegerField(
        label='Мин. возраст',
        validators=[DataRequired(), NumberRange(min=0)]
    )
    playtime_minutes = IntegerField(
        label='Время партии (мин)',
        validators=[DataRequired(), NumberRange(min=1)]
    )
    is_available = BooleanField(label='Доступна для игр', default=True)
    submit = SubmitField(label='Добавить игру')
