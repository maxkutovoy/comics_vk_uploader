import os
import shutil
from pathlib import Path
from urllib.parse import unquote, urlsplit
import random

import requests
from dotenv import load_dotenv


def parse_filename(url):
    parsed_url = urlsplit(url)
    filename = os.path.split(unquote(parsed_url.path))[1]
    return filename


def get_number_of_comics():
    url = "https://xkcd.com/info.0.json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()['num']


def fetch_random_comic():
    number_of_comics = get_number_of_comics()
    random_comic_number = random.randint(1, number_of_comics)
    url = f'https://xkcd.com/{random_comic_number}/info.0.json'
    response = requests.get(url)
    response.raise_for_status()
    random_comic = response.json()
    return random_comic['img'], random_comic['alt']


def save_image(image_url, filename, image_dir):
    file_path = f"{image_dir}/{filename}"
    response = requests.get(image_url)
    response.raise_for_status()
    with open(file_path, "wb") as file:
        file.write(response.content)


def get_boot_server_url(token, group_id):
    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    payload = {
        'access_token': token,
        'v': '5.131',
        'group_id': group_id,
    }
    response = requests.post(url, params=payload)
    response.raise_for_status()
    boot_server_url = response.json()
    check_vk_response(boot_server_url)
    return boot_server_url['response']['upload_url']


def get_uploaded_image_data(boot_server_url, image_dir):
    with open(f'{image_dir}/{os.listdir(image_dir)[0]}', 'rb') as file:
        files = {
            'photo': file,
        }
        response = requests.post(boot_server_url, files=files)
    response.raise_for_status()
    uploaded_image_params = response.json()
    check_vk_response(uploaded_image_params)
    return uploaded_image_params['photo'], uploaded_image_params['server'], uploaded_image_params['hash']


def save_image_to_wall(
        token,
        group_id,
        uploaded_image_id,
        uploaded_image_server,
        uploaded_image_hash,
):
    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    params = {
        'access_token': token,
        'group_id': group_id,
        'photo': uploaded_image_id,
        'server': uploaded_image_server,
        'hash': uploaded_image_hash,
        'v': '5.131',
    }
    response = requests.post(url, params)
    response.raise_for_status()
    saved_image_data = response.json()
    check_vk_response(saved_image_data)
    return saved_image_data['response'][0]['owner_id'], saved_image_data['response'][0]['id']


def post_image(token, group_id, image_description, owner_id, media_id):
    url = 'https://api.vk.com/method/wall.post'
    params = {
        'owner_id': f'-{group_id}',
        'message': image_description,
        'attachments': f'photo{owner_id}_{media_id}',
        'from_group': 1,
        'access_token': token,
        'v': '5.131'
    }
    response = requests.post(url, params=params)
    response.raise_for_status()
    check_vk_response(response.json())


def check_vk_response(response):
    if 'error' in response:
        error_code = response['error']['error_code']
        error_msg = response['error']['error_msg']
        raise requests.exceptions.HTTPError(error_code, error_msg)


def main():
    load_dotenv()
    vk_token = os.getenv('VK_TOKEN')
    group_id = os.getenv('GROUP_ID')
    image_dir = os.getenv('IMAGE_DIR', 'files')
    image_url, comic_description = fetch_random_comic()
    comic_title = parse_filename(image_url)
    Path(image_dir).mkdir(parents=True, exist_ok=True)
    try:
        save_image(image_url, comic_title, image_dir)
        boot_server_url = get_boot_server_url(vk_token, group_id)
        uploaded_image_id, uploaded_image_server, uploaded_image_hash = get_uploaded_image_data(boot_server_url,
                                                                                                image_dir)
        owner_id, media_id = save_image_to_wall(
            vk_token,
            group_id,
            uploaded_image_id,
            uploaded_image_server,
            uploaded_image_hash,
        )
        post_image(vk_token, group_id, comic_description, owner_id, media_id)
    finally:
        shutil.rmtree(image_dir, ignore_errors=True)


if __name__ == '__main__':
    main()
