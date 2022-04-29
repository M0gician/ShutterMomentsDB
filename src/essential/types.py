from datetime import date
from dataclasses import dataclass


@dataclass
class PhotoEntry:
    name: str
    photographer: str
    file: str
    genres: str
    date: date

@dataclass
class PaletteEntry:
    name: str
    photographer: str
    style: str
    palettes: str
