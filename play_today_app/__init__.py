from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_jwt_extended import JWTManager
from datetime import timedelta
from settings import Config


app = Flask(__name__)
app.config.from_object(Config)

# Настройки для JWT
app.config["JWT_SECRET_KEY"] = app.config['SECRET_KEY']
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

csrf = CSRFProtect(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

jwt = JWTManager(app)

login_manager = LoginManager(app)
# Перенаправление неавторизованного юзера на эндпоинт 'login'
login_manager.login_view = 'login'
login_manager.login_message = (
    'Для доступа к этой странице необходимо войти в систему.'
)
login_manager.login_message_category = 'warning'

# Загрузка пользователя по id для Flask-Login
from .models import User  # noqa


# На каждом запросе нужно заново достать пользователя из базы
# по id — потому что в cookie лежит только id.
@login_manager.user_loader
def load_user(user_id):
    user = db.session.get(User, int(user_id))
    # Если пользователь забанен, то сессия аннулируется
    if user and not user.is_active:
        return None
    return user

from . import api_views, cli_commands, error_handlers, models, views  # noqa
