import os

from dotenv import load_dotenv


load_dotenv()


class Config(object):
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')
    SECRET_KEY = os.getenv('SECRET_KEY')

    # Настройки для Dropbox (OAuth 2.0)
    DROPBOX_APP_KEY = os.getenv('DROPBOX_APP_KEY')
    DROPBOX_APP_SECRET = os.getenv('DROPBOX_APP_SECRET')
    DROPBOX_REFRESH_TOKEN = os.getenv('DROPBOX_REFRESH_TOKEN')
