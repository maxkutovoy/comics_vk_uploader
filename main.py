import os
from pathlib import Path
from pprint import pprint
from urllib.parse import unquote, urlsplit

import requests
from dotenv import load_dotenv
from tldextract import extract

load_dotenv()


def define_filename_prefix(url):
    extracted_url = extract(url)
    return extracted_url.domain


def pars_filename(url):
    parsed_url = urlsplit(url)
    filename = os.path.split(unquote(parsed_url.path))[1]
    return filename


def fetch_comic_book():
    url = "https://xkcd.com/info.0.json"
    response = requests.get(url)
    response.raise_for_status()
    current_comic = response.json()
    print(current_comic['alt'])

    directory = 'files'
    image_url = current_comic['img']
    filename = pars_filename(image_url)
    Path(directory).mkdir(parents=True, exist_ok=True)
    file_path = f"{directory}/{filename}"

    response = requests.get(image_url)
    response.raise_for_status()
    with open(file_path, "wb") as file:
        file.write(response.content)


def get_upload_server():
    method = 'photos.getWallUploadServer'
    url = f"https://api.vk.com/method/{method}"
    payload = {
        'access_token': os.getenv('VK_TOKEN'),
        'v': '5.131',
        'group_id': os.getenv('GROUP_ID'),
    }
    response = requests.get(url, params=payload)
    response.raise_for_status()
    pprint(response.json())
    info = response.json()
    upload_url = info['response']['upload_url']

    upload_params = {
        'group_id': os.getenv('GROUP_ID')
    }

    upload_response = requests.post(upload_url, upload_params)
    comic_name = os.listdir('files')[0]

    with open(f'files/{comic_name}', 'rb') as file:
        url = upload_url
        files = {
            'photo': file,
        }
        response = requests.post(url, files=files)
        response.raise_for_status()
        pprint(response.json())
        upload_server_info = response.json()

    method = 'photos.saveWallPhoto'
    url = f"https://api.vk.com/method/{method}"
    params = {
        'access_token': os.getenv('VK_TOKEN'),
        'group_id': os.getenv('GROUP_ID'),
        'photo': upload_server_info['photo'],
        'server': upload_server_info['server'],
        'hash': upload_server_info['hash'],
        'v': '5.131',
    }
    save_response = requests.post(url, params)
    save_response.raise_for_status()
    pprint(save_response.json())
    response = save_response.json()
    media_id, owner_id = response['response'][0]['id'], response['response'][0]['owner_id']
    print(media_id, owner_id)

    group_id = os.getenv('GROUP_ID')
    params = {
        'owner_id': f'-{group_id}',
        'message': 'Здесь будет описание',
        'attachments': f'photo{owner_id}_{media_id}',
        'from_group': 1,
        'access_token': os.getenv('VK_TOKEN'),
        'v': '5.95'
    }
    url = f'https://api.vk.com/method/wall.post'
    response = requests.post(url, params=params).json()


def main():
    # fetch_comic_book()
    get_upload_server()


if __name__ == '__main__':
    main()
