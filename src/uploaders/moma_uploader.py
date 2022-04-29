from typing import Tuple, List

import os
import requests
from tqdm import tqdm
from datetime import date, datetime
from bs4 import BeautifulSoup

from src.essential.updater import PhotoUpdater
from src.essential.types import PhotoEntry


class MOMAUploader(PhotoUpdater):
    BASE_URL = "https://www.moma.org"
    BASE_SEARCH_URL_PREFIX = "https://www.moma.org/collection/?utf8=%E2%9C%93&q="
    BASE_SEARCH_URL_SUFFIX = "&classifications=any&date_begin=Pre-1850&date_end=2022&with_images=1"
    BASE_DIR = os.getcwd()
    PHOTO_DIR = os.path.join(BASE_DIR, "photos")
    DATE_PREFIX = ('Seasons of', 'c.')

    def __init__(self, artist_name: str, max_page: int):
        super().__init__()
        self.artist_name = artist_name
        self.max_page = max_page
        self.img_urls = self.gather_single_image_urls()

    @staticmethod
    def caption_parser(raw_caption: str) -> Tuple[str, str, str]:
        parts = raw_caption.split(',')
        artist_name = parts[0].strip()
        title = ','.join(parts[1:-1]).strip()
        year = parts[-1].strip()[:4]
        return artist_name, title, year
        
    def gather_single_image_urls(self) -> List[str]:
        img_urls = set()
        for page_number in range(1, self.max_page+1):
            artist_name = "+".join(self.artist_name.split(' '))
            search_url = self.BASE_SEARCH_URL_PREFIX + artist_name + self.BASE_SEARCH_URL_SUFFIX
            search_url += f"&page={page_number}"

            rqst = requests.get(search_url)
            search_soup = BeautifulSoup(rqst.content, 'html.parser')
            img_urls.update(
                [
                    self.BASE_URL+tmp['href'] 
                    for tmp in search_soup.find_all(
                        'a', {'class': "grid-item__link"}
                    )
                ]
            )
        return list(img_urls)

    def photo_crawler(self):
        print(f"Scraping photos of {self.artist_name} from moma.org ...")

        for i, img_url in enumerate(tqdm(self.img_urls)):
            rqst = requests.get(img_url)
            soup = BeautifulSoup(rqst.content, 'html.parser')
            img_src = soup.find_all('picture', {'class': r"picture:center"})[0].find('img')['src']
            img_src = self.BASE_URL + img_src
        
            captions = soup.find_all('span', {'class': r"typography"})
            artist_name = captions[0].text.strip()
            if artist_name.lower() != self.artist_name.lower():
                continue
            title = captions[1].text.strip()
            year = captions[2].text.strip()
            # Remove unnecessary prefixes
            for prefix in self.DATE_PREFIX:
                if year.startswith(prefix):
                    year = year[len(prefix):].strip()
                    break
            # Handle different year formats
            if len(year) == 4:
                year = date.fromisoformat(f"{year}-01-01")
            elif str.count(year, '-') == 1:
                year = date.fromisoformat(f"{year[:4]}-01-01")
            elif str.count(year, '-') == 2:
                year = date.fromisoformat(year)
            elif ',' in year:
                if not year[0].isdigit():
                    year = datetime.strptime(year, '%B %d, %Y').date()
                else:
                    year = date.fromisoformat(f"{year[:4]}-01-01")
            elif ',' not in year:
                if not year[0].isdigit():
                    year = datetime.strptime(year, '%B %Y').date()
            else:
                raise ValueError(f"Unknown year format: {year}")

            r = requests.get(img_src, allow_redirects=True)
            img_name = f"{artist_name}-{i}.jpg"
            img_path = os.path.join(self.PHOTO_DIR, img_name)
            if not os.path.exists(img_path):
                with open(img_path, "wb") as img:
                    img.write(r.content)
                    img.close()

            self.photos[i] = PhotoEntry(
                name=title,
                photographer=self.artist_name,
                file=img_path,
                genres='',
                date=year
            )
        print(f"     DONE! {len(self.photos)} images gathered") 


if __name__ == "__main__":
    uploader = MOMAUploader('Henri Cartier-Bresson', max_page=7)
    uploader.photo_crawler()
    uploader.upload()
