import asyncio
import json
import re
from http import HTTPStatus

import aiohttp
from flask import current_app  # Для доступа к конфигу

from .constants import BEARER_PREFIX, DROPBOX_DL_PARAM, DROPBOX_RAW_PARAM

# Эндпоинты Dropbox
TOKEN_LINK = "https://api.dropboxapi.com/oauth2/token"
UPLOAD_LINK = "https://content.dropboxapi.com/2/files/upload"
SHARING_LINK = (
    "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings"
)


async def get_dropbox_access_token(session):
    """Асинхронно получает новый access_token, используя refresh_token."""
    data = {
        "grant_type": "refresh_token",
        "refresh_token": current_app.config["DROPBOX_REFRESH_TOKEN"],
    }
    auth = aiohttp.BasicAuth(
        current_app.config["DROPBOX_APP_KEY"],
        current_app.config["DROPBOX_APP_SECRET"],
    )

    async with session.post(TOKEN_LINK, data=data, auth=auth) as response:
        if response.status != HTTPStatus.OK:
            error_data = await response.json()
            raise Exception(f"Не удалось обновить Dropbox токен: {error_data}")

        token_data = await response.json()
        return token_data["access_token"]


async def upload_images_to_dropbox(images):
    if not images:
        return []

    tasks = []
    async with aiohttp.ClientSession() as session:
        # 1. Получение свежего access_token-а
        access_token = await get_dropbox_access_token(session)

        for image in images:
            tasks.append(
                asyncio.ensure_future(
                    upload_image_and_get_url(session, image, access_token)
                )
            )
        urls = await asyncio.gather(*tasks)
    return urls


async def upload_image_and_get_url(session, image, access_token):
    """Асинхронная функция загрузки изображений и получения на них ссылок."""
    # Сброс указателя и очистка имени файла
    image.seek(0)
    safe_filename = re.sub(r"[^a-zA-Z0-9_.-]", "_", image.filename)

    dropbox_args = json.dumps(
        {
            "autorename": True,
            "mode": "add",
            "path": f"/{safe_filename}",
        }
    )

    headers = {
        "Authorization": f"{BEARER_PREFIX}{access_token}",
        "Content-Type": "application/octet-stream",
        "Dropbox-API-Arg": dropbox_args,
    }

    async with session.post(
        UPLOAD_LINK, headers=headers, data=image.read()
    ) as response:
        data = await response.json()
        if response.status != HTTPStatus.OK:
            raise Exception(
                f"Ошибка загрузки в Dropbox: {data.get('error_summary')}"
            )
        path = data["path_lower"]

    # Создание публичной ссылки
    headers = {
        "Authorization": f"{BEARER_PREFIX}{access_token}",
        "Content-Type": "application/json",
    }
    async with session.post(
        SHARING_LINK, headers=headers, json={"path": path}
    ) as response:
        data = await response.json()
        if "url" not in data:
            if "shared_link_already_exists" in data.get("error", {}):
                data = data["error"]["shared_link_already_exists"]["metadata"]
            else:
                raise Exception(
                    f"Ошибка создания ссылки: {data.get('error_summary')}"
                )
        url = data["url"]
        url = url.replace(DROPBOX_DL_PARAM, DROPBOX_RAW_PARAM)
    return url
