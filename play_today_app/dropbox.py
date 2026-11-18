import asyncio
import json

import aiohttp

from . import app

# Заголовок для авторизации пользователя.
AUTH_HEADER = f'Bearer {app.config["DROPBOX_TOKEN"]}'
# Эндпоинт для загрузки изображений.
UPLOAD_LINK = 'https://content.dropboxapi.com/2/files/upload'
# Эндпоинт для создания ссылки на изображение. Его можно найти
SHARING_LINK = ('https://api.dropboxapi.com/2/'
                'sharing/create_shared_link_with_settings')


async def upload_images_to_dropbox(images):
    if images is not None:
        # Пустой список для асинхронных задач.
        tasks = []
        # Инициализировать единую сессию для работы с aiohttp.
        async with aiohttp.ClientSession() as session:
            for image in images:
                tasks.append(
                    asyncio.ensure_future(
                        upload_image_and_get_url(session, image)
                    )
                )
            # Запуск выполнения задач.
            urls = await asyncio.gather(*tasks)
        return urls


# Асинхронная функция загрузки изображений и получения на них ссылок.
async def upload_image_and_get_url(session, image):
    dropbox_args = json.dumps({
        'autorename': True,
        'mode': 'add',
        'path': f'/{image.filename}',
    })
    async with session.post(
        UPLOAD_LINK,
        headers={
            'Authorization': AUTH_HEADER,
            'Content-Type': 'application/octet-stream',
            'Dropbox-API-Arg': dropbox_args
        },
        data=image.read()
    ) as response:
        data = await response.json()
        path = data['path_lower']
    async with session.post(
        SHARING_LINK,
        headers={
            'Authorization': AUTH_HEADER,
            'Content-Type': 'application/json',
        },
        json={'path': path}
    ) as response:
        data = await response.json()
        if 'url' not in data:
            data = data['error']['shared_link_already_exists']['metadata']
        url = data['url']
        url = url.replace('&dl=0', '&raw=1')
    return url
