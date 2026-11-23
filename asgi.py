from asgiref.wsgi import WsgiToAsgi
from play_today_app import app

# Оборачивает WSGI-приложение Flask в ASGI-совместимый middleware
application = WsgiToAsgi(app)