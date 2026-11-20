from functools import wraps
import random

from flask import abort, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from . import app, db
from .models import Boardgame, Review, User
from .forms import BoardgameForm, LoginForm, RegisterForm, ReviewForm
from .dropbox import upload_images_to_dropbox


# Декоратор для проверки прав администратора
def admin_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return function(*args, **kwargs)
    return decorated_function


@app.route('/add_boardgame', methods=['GET', 'POST'])
@login_required
@admin_required
def add_boardgame():
    """Страница добавления новой игры (только для админа)."""
    form = BoardgameForm()

    if form.validate_on_submit():
        existing_game = Boardgame.query.filter_by(name=form.name.data).first()
        if existing_game:
            flash('Игра с таким названием уже существует!', 'danger')
            return render_template('add_boardgame.html', form=form)

        game = Boardgame(
            name=form.name.data,
            description=form.description.data,
            min_players=form.min_players.data,
            max_players=form.max_players.data,
            min_age=form.min_age.data,
            playtime_minutes=form.playtime_minutes.data,
            is_available=form.is_available.data
        )

        try:
            db.session.add(game)
            db.session.commit()
            flash(f'Игра "{game.name}" успешно добавлена!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при сохранении: {str(e)}', 'danger')

    return render_template('add_boardgame.html', form=form)


@app.route('/')
def index():
    """Главная страница: показывает случайную игру и её отзывы."""
    boardgames = Boardgame.query.all()
    if not boardgames:
        return render_template('index.html', boardgame=None, reviews=[])

    random_boardgame = random.choice(boardgames)

    reviews = Review.query.filter_by(
        boardgame_id=random_boardgame.id
    ).order_by(Review.timestamp.desc()).all()

    return render_template(
        'index.html', boardgame=random_boardgame, reviews=reviews
    )


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegisterForm()
    if form.validate_on_submit():
        # Проверка: занят ли логин
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            flash(
                'Пользователь с таким именем уже существует',
                category='danger'
            )
            return render_template('register.html', form=form)

        new_user = User(username=form.username.data)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()

        flash(
            'Регистрация прошла успешно! Теперь вы можете войти.',
            category='success'
        )
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Вы успешно вошли в систему!', category='success')
            # Если пользователь перекинут на вход со страницы
            # добавления отзыва, то возвращение его обратно
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))

        flash('Неправильное имя пользователя или пароль', category='danger')

    return render_template('login.html', form=form)


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    """Выход из системы."""
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))


@app.route('/add_review', methods=['GET', 'POST'])
@login_required
async def add_review():
    """Страница добавления нового отзыва (только для авторизованных)."""
    form = ReviewForm()

    form.boardgame_id.choices = [
        (
            boardgame.id, boardgame.name
        ) for boardgame in Boardgame.query.order_by('name').all()
    ]

    if form.validate_on_submit():
        review = Review(
            boardgame_id=form.boardgame_id.data,
            user_id=current_user.id,
            rating=form.rating.data,
            text=form.text.data,
            images=[]
        )

        if form.images.data:
            valid_images = [img for img in form.images.data if img.filename]
            if valid_images:
                images_urls = await upload_images_to_dropbox(valid_images)
                review.images = images_urls

        try:
            db.session.add(review)
            db.session.commit()
            flash('Ваш отзыв успешно добавлен!', category='success')
            return redirect(url_for('boardgame_view', id=review.boardgame_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при сохранении: {str(e)}', category='danger')

    return render_template('add_review.html', form=form)


@app.route('/delete_review/<int:id>', methods=['POST'])
@login_required
def delete_review(id):
    """Удаление отзыва (доступно автору или админу)."""
    review = Review.query.get_or_404(id)

    # Проверка прав: автор отзыва или администратор?
    if current_user.id != review.user_id and not current_user.is_admin:
        abort(403)

    boardgame_id = review.boardgame_id
    db.session.delete(review)
    db.session.commit()
    flash('Отзыв был успешно удален.', 'success')
    return redirect(url_for('boardgame_view', id=boardgame_id))


@app.route('/edit_review/<int:id>', methods=['GET', 'POST'])
@login_required
async def edit_review(id):
    """Редактирование отзыва (доступно автору или админу)."""
    review = Review.query.get_or_404(id)

    # Проверка прав: автор отзыва или администратор?
    if current_user.id != review.user_id and not current_user.is_admin:
        abort(403)

    form = ReviewForm(obj=review)
    form.boardgame_id.choices = [
        (
            boardgame.id, boardgame.name
        ) for boardgame in Boardgame.query.order_by('name').all()
    ]

    if form.validate_on_submit():
        review.rating = form.rating.data
        review.text = form.text.data
        review.boardgame_id = form.boardgame_id.data

        # Если пользователь загрузил новые картинки, замена старых
        if form.images.data and form.images.data[0].filename:
            valid_images = [img for img in form.images.data if img.filename]
            if valid_images:
                images_urls = await upload_images_to_dropbox(valid_images)
                review.images = images_urls

        try:
            db.session.commit()
            flash('Отзыв успешно обновлен!', 'success')
            return redirect(url_for('boardgame_view', id=review.boardgame_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при сохранении: {str(e)}', 'danger')

    # Флаг is_edit=True для шаблона
    return render_template('add_review.html', form=form, is_edit=True)


@app.route('/boardgames/<int:id>')
def boardgame_view(id):
    boardgame = Boardgame.query.get_or_404(id)
    reviews = Review.query.filter_by(
        boardgame_id=boardgame.id
    ).order_by(Review.timestamp.desc()).all()

    return render_template(
        'index.html', boardgame=boardgame, reviews=reviews
    )
