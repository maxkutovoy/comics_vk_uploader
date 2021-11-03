from pprint import pprint
from pathlib import Path

import requests

import os
from urllib.parse import unquote, urlsplit

from tldextract import extract


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
    pprint(current_comic)

    directory = 'files'
    image_url = current_comic['img']
    filename = pars_filename(image_url)
    Path(directory).mkdir(parents=True, exist_ok=True)
    file_path = f"{directory}/{filename}"

    response = requests.get(image_url)
    response.raise_for_status()
    with open(file_path, "wb") as file:
        file.write(response.content)


def main():
    fetch_comic_book()


if __name__ == '__main__':
    main()
