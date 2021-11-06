import os
from pathlib import Path
from urllib.parse import unquote, urlsplit
import random

import requests
from dotenv import load_dotenv


def pars_filename(url):
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
    return response.json()


def check_dir(directory):
    Path(directory).mkdir(parents=True, exist_ok=True)
    return directory


def save_image(image_url, filename, image_dir):
    directory = check_dir(image_dir)
    file_path = f"{directory}/{filename}"
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
    response = requests.post(url, params=payload).json()
    if 'error' in response:
        raise requests.exceptions.HTTPError(response['error']['error_msg'])
    return response['response']['upload_url']


def get_uploaded_image_data(token, group_id, image_dir):
    url = get_boot_server_url(token, group_id)
    comic_name = os.listdir(image_dir)[0]
    with open(f'{image_dir}/{comic_name}', 'rb') as file:
        files = {
            'photo': file,
        }
        response = requests.post(url, files=files).json()
    if 'error' in response:
        raise requests.exceptions.HTTPError(response['error']['error_msg'])
    return response


def save_image_to_wall(token, group_id, image_dir):
    uploaded_image_data = get_uploaded_image_data(token, group_id, image_dir)
    url = 'https://api.vk.com/method/photos.saveWallPhoto'
    params = {
        'access_token': token,
        'group_id': group_id,
        'photo': uploaded_image_data['photo'],
        'server': uploaded_image_data['server'],
        'hash': uploaded_image_data['hash'],
        'v': '5.131',
    }
    response = requests.post(url, params).json()
    if 'error' in response:
        raise requests.exceptions.HTTPError(response['error']['error_msg'])
    return response


def post_image(token, group_id, image_description, image_dir):
    url = 'https://api.vk.com/method/wall.post'
    saved_image_data = save_image_to_wall(token, group_id, image_dir)
    owner_id = saved_image_data['response'][0]['owner_id']
    media_id = saved_image_data['response'][0]['id']
    params = {
        'owner_id': f'-{group_id}',
        'message': image_description,
        'attachments': f'photo{owner_id}_{media_id}',
        'from_group': 1,
        'access_token': token,
        'v': '5.131'
    }
    response = requests.post(url, params=params).json()
    if 'error' in response:
        raise requests.exceptions.HTTPError(response['error']['error_msg'])


def main():
    load_dotenv()
    vk_token = os.getenv('VK_TOKEN')
    group_id = os.getenv('GROUP_ID')
    image_dir = os.getenv('IMAGE_DIR', 'files')
    random_comic = fetch_random_comic()
    image_url = random_comic['img']
    comic_description = random_comic['alt']
    comic_title = pars_filename(image_url)
    try:
        save_image(image_url, comic_title, image_dir)
        post_image(vk_token, group_id, comic_description, image_dir)
    except ValueError:
        raise ValueError('error')
    finally:
        os.remove(f'{image_dir}/{comic_title}')


if __name__ == '__main__':
    main()
