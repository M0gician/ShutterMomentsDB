from typing import Tuple

import re
import os
import requests
from datetime import date
from bs4 import BeautifulSoup

from src.updater import PhotoUpdater
from src.types import PhotoEntry


class GagosianUploader(PhotoUpdater):
    BASE_URL = "https://gagosian.com/artists/"
    BASE_DIR = os.getcwd()
    PHOTO_DIR = os.path.join(BASE_DIR, "photos")

    def __init__(self, artist_name: str):
        super().__init__()
        self.artist_name = artist_name
        self.url = self.BASE_URL + artist_name
        self.rqst = requests.get(self.url)
        self.soup = BeautifulSoup(self.rqst.content, 'html.parser')
        self.image_regex = re.compile(
            r'(https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*).jpg)'
        )

    @staticmethod
    def caption_parser(raw_caption: str) -> Tuple[str, str, str]:
        parts = raw_caption.split(',')
        artist_name = parts[0].strip()
        title = ','.join(parts[1:-1]).strip()
        year = parts[-1].strip()[:4]
        return artist_name, title, year
        

    def photo_crawler(self):
        print(f"Scraping photos of {self.artist_name} from gagosian.com ...")

        print("     Preparing images urls ...") 
        image_soups = self.soup.find_all('div', {'class': "slide__image"})
        image_urls = [
            tmp.find('img')['srcset'].split(',')[0] for tmp in image_soups
        ]
        image_urls = [
            self.image_regex.match(tmp).group() for tmp in image_urls
        ]
        
        print("     Preparing images captions ...") 
        captions_soups = self.soup.find_all('div', {'class': "slide__caption"})
        image_captions = [
            tmp.find('p', {'class': 'caption_line_1'}).get_text() for tmp in captions_soups
        ]
        image_captions = [
            self.caption_parser(raw_caption) for raw_caption in image_captions
        ]

        print("     Downloading images ...") 
        for i in range(len(image_urls)):
            image_url = image_urls[i]
            artist_name, title, year = image_captions[i]
            r = requests.get(image_url, allow_redirects=True)

            img_name = f"{artist_name}-{i}.jpg"
            img_path = os.path.join(self.PHOTO_DIR, img_name)
            if not os.path.exists(img_path):
                with open(img_path, "wb") as img:
                    img.write(r.content)
                    img.close()

            self.photos[i] = PhotoEntry(
                name=title,
                photographer=artist_name,
                file=img_path,
                genres='',
                date=date.fromisoformat(f"{year}-01-01")
            )
        print(f"     DONE! {len(image_urls)} images gathered") 


if __name__ == "__main__":
    uploader = GagosianUploader('jeff-wall')
    uploader.photo_crawler()
    uploader.upload()
