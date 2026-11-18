import random

from flask import render_template, redirect, url_for, flash

from . import app, db
from .models import Boardgame, Review
from .forms import ReviewForm
from .dropbox import upload_images_to_dropbox


@app.route('/')
def index():
    """Главная страница: показывает случайную игру и её отзывы."""
    boardgames = Boardgame.query.all()
    if not boardgames:
        return render_template('index.html', boardgame=None, reviews=[])

    random_boardgame = random.choice(boardgames)

    # Отзывы для этой игры, отсортированные от новых к старым
    reviews = Review.query.filter_by(
        boardgame_id=random_boardgame.id
    ).order_by(Review.timestamp.desc()).all()

    return render_template(
        'index.html', boardgame=random_boardgame, reviews=reviews
    )


@app.route('/add', methods=['GET', 'POST'])
async def add_review():
    """Страница добавления нового отзыва."""
    form = ReviewForm()

    # Заполняет выпадающий список играми из базы
    form.boardgame_id.choices = [
        (
            boardgame.id, boardgame.name
        ) for boardgame in Boardgame.query.order_by('name').all()
    ]

    if form.validate_on_submit():
        review = Review(
            boardgame_id=form.boardgame_id.data,
            author=form.author.data,
            rating=form.rating.data,
            text=form.text.data,
            images=[]  # Для ссылок Dropbox
        )

        if form.images.data:
            valid_images = [img for img in form.images.data if img.filename]

            if valid_images:
                images_urls = await upload_images_to_dropbox(valid_images)
                review.images = images_urls

        try:
            db.session.add(review)
            db.session.commit()
            flash('Ваш отзыв успешно добавлен!', 'success')
            return redirect(url_for('boardgame_view', id=review.boardgame_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при сохранении: {str(e)}', 'danger')

    return render_template('add_review.html', form=form)


@app.route('/boardgames/<int:id>')
def boardgame_view(id):
    boardgame = Boardgame.query.get_or_404(id)
    reviews = Review.query.filter_by(
        boardgame_id=boardgame.id
    ).order_by(Review.timestamp.desc()).all()

    return render_template(
        'index.html', boardgame=boardgame, reviews=reviews
    )
