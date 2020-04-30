import logging
import os
from .exceptions import ETLError

logger = logging.getLogger()


def infer_media_source(media_path: str):
    # get media extension and check it's readable & co.
    _, media_extension = os.path.splitext(media_path)
    media_source = None
    if media_extension.lower() == 'gpx':
        logger.debug('Received media from source OSM Tracker')
        media_source = 'osm_tracker'

    elif media_extension.lower() in ['mov', 'mp4']:
        # look for gpx data
        if os.path.exists(media_path.replace(media_extension, 'gpx')):
            media_source = 'smartphone_video'
        else:
            media_source = 'gopro'
            # todo: sanity-check: Are there some GPX indeed data ?

    elif media_extension.lower() in ['jpg', 'jpeg']:  # Todo/question: png ?
        media_source = 'smartphone_photo'
    else:
        raise ETLError(f'Unknown media extension {media_extension}')
    return media_source
