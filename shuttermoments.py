import argparse

from src.uploaders.gagosian_uploader import GagosianUploader
from src.uploaders.moma_uploader import MOMAUploader

def main():
    parser = argparse.ArgumentParser(description='ShutterMoments DB automated tool! Collect photos of artists from online sourses')
    parser.add_argument(
        'source', choices=['gagosian', 'moma'], help='Photo source website'
    )
    parser.add_argument(
        '-n', '--name', type=str, required=True, help='Artist name'
    )
    parser.add_argument(
        '-p', '--page', type=int, required=False, help='Maximum page number to scrape', default=1
    )
    args = parser.parse_args()

    if args.source == 'gagosian':
        uploader = GagosianUploader(artist_name=args.name)
    elif args.source == 'moma':
        uploader = MOMAUploader(artist_name=args.name, max_page=args.page)
    else:
        raise ValueError(f'Unknown source: {args.source}')
    
    uploader.photo_crawler()
    uploader.upload()


if __name__ == "__main__":
    main()
