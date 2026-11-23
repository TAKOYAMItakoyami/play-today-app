import csv
import os

import click
from flask.cli import with_appcontext

from . import app, db
from .constants import CSV_TRUE_VALUE, DEFAULT_CSV_FILENAME
from .models import Boardgame, User


@app.cli.command("load_boardgames")
@click.argument("filename", default=DEFAULT_CSV_FILENAME)
@with_appcontext
def load_boardgames_command(filename):
    """Загружает настольные игры из CSV-файла в базу данных."""
    try:
        with open(filename, mode="r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            counter = 0
            for row in reader:
                existing_game = Boardgame.query.filter_by(
                    name=row["name"]
                ).first()
                if existing_game:
                    click.echo(
                        f"Игра '{row['name']}' уже есть в базе. Пропускаем."
                    )
                    continue

                game = Boardgame(
                    name=row["name"],
                    description=row["description"],
                    min_players=int(row["min_players"]),
                    max_players=int(row["max_players"]),
                    min_age=int(row["min_age"]),
                    playtime_minutes=int(row["playtime_minutes"]),
                    is_available=(
                        row["is_available"].strip().lower() == CSV_TRUE_VALUE
                    ),
                )
                db.session.add(game)
                counter += 1

            db.session.commit()
            click.echo(f"Успешно загружено игр: {counter}")

    except FileNotFoundError:
        click.echo(f"Ошибка: Файл '{filename}' не найден в корне проекта.")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Произошла ошибка при загрузке: {e}")


@app.cli.command("create_first_superuser")
@with_appcontext
def create_admin_command():
    """Создает администратора (суперюзера) на основе данных из .env."""
    # Проверка: есть ли уже хоть один суперюзер (администратор)
    existing_admin = User.query.filter_by(is_admin=True).first()
    if existing_admin:
        click.echo(f"Администратор уже существует: {existing_admin.username}")
        return

    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")

    missing = [
        name
        for name, value in (
            ("ADMIN_USERNAME", username),
            ("ADMIN_PASSWORD", password),
        )
        if not value
    ]
    if missing:
        raise click.ClickException(
            "Не заданы переменные окружения: "
            + ", ".join(missing)
            + ". Создайте .env (например, из .env.example) и укажите их."
        )

    admin = User(username=username, is_admin=True)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()

    click.echo(f"Суперпользователь '{username}' успешно создан!")
