from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import (
    RadioField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField
)
from wtforms.validators import DataRequired, Length


class ReviewForm(FlaskForm):
    """Форма для добавления отзыва на настольную игру."""

    # Выбор игры из списка (заполняется динамически в views.py)
    boardgame_id = SelectField(
        'Выберите настольную игру',
        coerce=int,  # Превращает строку из HTML в число (int) для базы данных
        validators=[DataRequired(message='Выберите игру')]
    )

    author = StringField(
        'Ваше имя',
        validators=[
            DataRequired(message='Обязательное поле'),
            Length(1, 64, message='Имя не должно превышать 64 символа')
        ]
    )

    rating = RadioField(
        'Оценка (от 1 до 10)',
        choices=[(i, str(i)) for i in range(1, 11)],
        coerce=int,
        validators=[DataRequired(message='Поставьте оценку')]
    )

    text = TextAreaField(
        'Напишите отзыв',
        validators=[
            DataRequired(message='Обязательное поле'),
            Length(min=10, message='Отзыв должен быть не короче 10 символов')
        ]
    )

    images = MultipleFileField(
        'Прикрепите фотографии',
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

    submit = SubmitField('Опубликовать отзыв')
