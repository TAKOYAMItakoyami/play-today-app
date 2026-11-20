import csv
import click
from flask.cli import with_appcontext

from . import app, db
from .models import Boardgame


@app.cli.command('load_boardgames')
@click.argument('filename', default='boardgames.csv')
@with_appcontext
def load_boardgames_command(filename):
    """Загружает настольные игры из CSV-файла в базу данных."""
    try:
        with open(filename, mode='r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            counter = 0
            for row in reader:
                # Проверяем, нет ли уже такой игры в базе (по имени)
                existing_game = Boardgame.query.filter_by(
                    name=row['name']
                ).first()
                if existing_game:
                    click.echo(
                        f"Игра '{row['name']}' уже есть в базе. Пропускаем."
                    )
                    continue

                game = Boardgame(
                    name=row['name'],
                    description=row['description'],
                    min_players=int(row['min_players']),
                    max_players=int(row['max_players']),
                    min_age=int(row['min_age']),
                    playtime_minutes=int(row['playtime_minutes']),
                    is_available=(row['is_available'].strip().lower() == 'true')
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
