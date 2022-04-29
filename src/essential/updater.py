
from typing import Dict

import os
import requests
import mimetypes

from tqdm import tqdm
from notion.client import NotionClient
from notion.block import EmbedOrUploadBlock
from notion.operations import build_operation
from notion.collection import CollectionRowBlock

from .types import PhotoEntry
from .consts import TOKEN, PHOTO_DATABASE_URL


class PhotoUpdater:
    def __init__(self):
        self.client = NotionClient(token_v2=TOKEN)
        self.photo_db = self.client.get_collection_view(PHOTO_DATABASE_URL)
        self.photos: Dict[int, PhotoEntry] = {}

    def photo_crawler(self) -> None:
        raise NotImplementedError
    
    def upload_file_to_row_property(
        self,
        row: CollectionRowBlock,
        path: str,
        property_name: str
    ) -> None:
        mimetype = mimetypes.guess_type(path)[0] or "text/plain"
        filename = os.path.split(path)[-1]
        data = self.client.post("getUploadFileUrl", {"bucket": "secure", "name": filename, "contentType": mimetype}, ).json()
        # Return url, signedGetUrl, signedPutUrl
        mangled_property_name = [e["id"] for e in row.schema if e["name"] == property_name][0]

        with open(path, "rb") as f:
            response = requests.put(data["signedPutUrl"], data=f, headers={"Content-type": mimetype})
            response.raise_for_status()
        simpleurl = data['signedGetUrl'].split('?')[0]
        op1 = build_operation(id=row.id, path=["properties", mangled_property_name], args=[[filename, [["a", simpleurl]]]], table="block", command="set")
        file_id = simpleurl.split("/")[-2]
        op2 = build_operation(id=row.id, path=["file_ids"], args={"id": file_id}, table="block", command="listAfter")
        self.client.submit_transaction([op1, op2])
    
    def upload(self) -> None:
        print("Creating new entries and Uploading photos ...")
        for entry in tqdm(self.photos.values()):
            # Create a new DB entry for each new photo
            row: CollectionRowBlock = self.photo_db.collection.add_row()
            # Fill properties
            row.name = entry.name
            row.photographer = entry.photographer
            row.genres = entry.genres
            # Convert ISO time to a python datetime object
            row.date = entry.date
            # Upload the photo from local path
            row.file = 'img'
            self.upload_file_to_row_property(row, entry.file, "File")
            # Add photo that page as well
            embedded_image = row.children.add_new(
                EmbedOrUploadBlock, caption=row.name,
            )
            embedded_image.upload_file(path=entry.file)
        print("Done!")
