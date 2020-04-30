import logging
import os
from functools import partial

import pandas as pd
import pyproj
from gopro2gpx.main import extract
from gpxpy import parse as gpxpy_parse
from gpxpy.gpx import GPX
from moviepy.editor import VideoFileClip
from pymediainfo import MediaInfo
from shapely.geometry import Point
from shapely.ops import transform

from .exceptions import ETLError

logger = logging.getLogger()




def extract_gpx_from_gopro(media_path: str, *, format: str = "GPX", binary: bool = False) -> str:
    """ Extract gpx data from a Go-Pro file

    Parameters
    ----------
    media_path: path to Go-Pro media
    format: output format for spatial coordinates
    binary: whether media is binary

    Returns
    -------
    gpx_path: path of coordinates created file
    """
    # todo: should we infer whether or not input file is binary?
    gpx_path = f'{media_path}.{format.lower()}'

    try:
        extract(input_file=media_path, output_file=media_path, format=format, binary=binary, verbose=False,
                skip=True)  # keep skip to false to be able to catch errors
    except Exception as e:
        raise ETLError(f'Could not extract GPX because \n {e}')
    # Note: since the above function sometime fails silently, we cannot catch any Exception.
    # So we check if a GPX file could indeed be created, if not we raise an error.
    if not os.path.exists(gpx_path):
        raise ETLError(f'Could not extract GPX from file {media_path}')
    return gpx_path


def gpx_to_gps(gpx_path: str = None, gpx_data: GPX = None) -> pd.DataFrame:
    """ Convert GPX to GPS

    Parameters
    ----------
    gpx_path: path to a GPX file
    gpx_data:  GPX object that returns data from a parsed gpx file. If given ignore `gpx_path`

    Returns
    -------
    gps_data: list of dictionaries points with Time, Lat, Long, Elev

    Examples:
    --------
    > gps_data = gpx_to_gps('../gpssamples/hero6.gpx')
    > gps_data
                                   Latitude   Longitude  Elevation
        2018-01-24 19:27:58+00:00  33.126515 -117.327168    -17.228
        2018-01-24 19:27:59+00:00  33.126543 -117.327153    -18.199
        2018-01-24 19:28:00+00:00  33.126544 -117.327143    -18.183
        2018-01-24 19:28:01+00:00  33.126554 -117.327130    -18.172
        2018-01-24 19:28:02+00:00  33.126563 -117.327118    -18.162
        ...                         ...         ...         ...


    """
    if gpx_data is None:
        with open(gpx_path, 'r') as gpx_file:
            gpx_data = gpxpy_parse(gpx_file)

    gps_data = []
    for track in gpx_data.tracks:
        for segment in track.segments:
            for point in segment.points:
                # todo: check performance of pandas on big files
                point_info = pd.DataFrame({
                    "latitude": point.latitude,
                    "longitude": point.longitude,
                    "elevation": point.elevation,
                }, index=[point.time], )
                gps_data.append(point_info)
        gps_data = pd.concat(gps_data, axis=0)
    # sort index if not monotonic
    if not gps_data.index.is_monotonic:
        gps_data.sort_index(inplace=True)
    return gps_data


def get_media_info(media_path: str) -> dict:
    """ Extract metadata info about a media file

    Parameters
    ----------
    media_path: Path to media

    Returns
    -------
    info: dict with all media metadata

    """

    media_info = MediaInfo.parse(media_path)
    track_0 = media_info.tracks[0]
    info_track_0 = track_0.__dict__
    return info_track_0


def get_media_duration(media_path: str) -> float:
    """ Extract duration from a media file

    Parameters
    ----------
    media_path: Path to media

    Returns
    -------
    duration: duration of the media

    Notes:
    ------
    Taken from here:
    https://www.reddit.com/r/moviepy/comments/2bsnrq/is_it_possible_to_get_the_length_of_a_video/

    """
    clip = VideoFileClip(media_path)
    return clip.duration


def pyproj_transform(gps_row, source_epsg: int = 4326, target_epsg: int = 2154) -> str:
    """ Applies geometrical transformation to a row of GPS coordinate

    Parameters
    ----------
    gps_row: row of coordinates with key 'longitude' and 'latitude'
    source_epsg: projection source
    target_epsg: projection target

    Returns
    -------
    geo_target: string like 'Point (x, y, z)'

    """
    project = partial(
        pyproj.transform,
        pyproj.Proj(init=f"epsg:{source_epsg}"),  # source coordinate system
        pyproj.Proj(init=f"epsg:{target_epsg}"),
    )  # destination coordinate system

    geo_source = Point(gps_row.longitude, gps_row.latitude)
    geo_target = transform(project, geo_source).wkt
    return geo_target


def add_geom_to_gps_data(gps_data: pd.DataFrame, **kwargs):
    """ Add projection to a given geometry to a GPS list of points

    Parameters
    ----------
    gps_data: list of dict  with gps point containing Longitude and Latitude

    Examples
    --------
    > gps_data
                                   latitude   longitude  elevation
        2018-01-24 19:27:58+00:00  33.126515 -117.327168    -17.228
        2018-01-24 19:27:59+00:00  33.126543 -117.327153    -18.199
        2018-01-24 19:28:12+00:00  33.126616 -117.325690    -18.440
        2018-01-24 19:28:13+00:00  33.126540 -117.327072    -19.161
        2018-01-24 19:28:14+00:00  33.126539 -117.327218    -18.472
    > add_geom_to_gps_data(gps_data)
    > gps_data
                                                   geom
        2018-01-24 19:27:58+00:00  33.126515  ...  POINT (-6843671.309553764 12301224.24713064)
        2018-01-24 19:27:59+00:00  33.126543  ...  POINT (-6843668.109889416 12301222.98998321)
        2018-01-24 19:28:12+00:00  33.126616  ...  POINT (-6843653.244167816 12301083.64126886)
        2018-01-24 19:28:13+00:00  33.126540  ...  POINT (-6843668.018846542 12301215.23885827)
        2018-01-24 19:28:14+00:00  33.126539  ...  POINT (-6843668.778535692 12301229.22991498)

    """
    gps_data['geom'] = gps_data.apply(lambda gps_row: pyproj_transform(gps_row, **kwargs), axis=1)
