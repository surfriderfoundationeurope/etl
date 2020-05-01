import logging
import os
from functools import partial

import numpy as np
import pandas as pd
import pyproj
from gopro2gpx.main import extract
from gpxpy import parse as gpxpy_parse
from gpxpy.gpx import GPX
from shapely.geometry import Point
from shapely.ops import transform

from .exceptions import ETLError

logger = logging.getLogger()


def extract_gpx_from_gopro(
        media_path: str, *, format: str = "GPX", binary: bool = False
) -> str:
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

    output_file = os.path.splitext(media_path)[0]  # get rid of suffix
    gpx_path = f"{output_file}.{format.lower()}"

    try:
        extract(
            input_file=media_path,
            output_file=output_file,
            format=format,
            binary=binary,
            verbose=False,
            skip=True,
        )  # keep skip to false to be able to catch errors
    except Exception as e:
        raise ETLError(f"Could not extract GPX because \n {e}")
    # Note: since the above function sometime fails silently, we cannot catch any Exception.
    # So we check if a GPX file could indeed be created, if not we raise an error.
    if not os.path.exists(gpx_path):
        raise ETLError(f"Could not extract GPX from file {media_path}")
    return gpx_path


def open_gpx_file(gpx_path: str) -> GPX:
    """ Open and parse a gpx file

    Parameters
    ----------
    gpx_path: path to a GPX file

    Returns
    -------
    GPX data
    """
    with open(gpx_path, "r") as gpx_file:
        gpx_data = gpxpy_parse(gpx_file)
    return gpx_data


def gpx_tracks_to_gps(gpx_data: GPX = None) -> pd.DataFrame:
    """ Convert GPX tracks to GPS

    Parameters
    ----------
    gpx_data:  GPX object that returns data from a parsed gpx file.

    Returns
    -------
    gps_data: dataframe where index are time and columns are latitude, longitude, elevation

    Examples
    ---------
    >>> gps_data = gpx_to_gps('../../data/osm_tracker/sample.gpx')
    >>> gps_data
                                   latitude   longitude    elevation
        2018-01-24 19:27:58+00:00  33.126515 -117.327168    -17.228
        2018-01-24 19:27:59+00:00  33.126543 -117.327153    -18.199
        2018-01-24 19:28:00+00:00  33.126544 -117.327143    -18.183
        2018-01-24 19:28:01+00:00  33.126554 -117.327130    -18.172
        2018-01-24 19:28:02+00:00  33.126563 -117.327118    -18.162


    """
    # Todo: check that it works for image GPX (no time I guess)

    gps_data = []
    for track in gpx_data.tracks:
        for segment in track.segments:
            for point in segment.points:
                # todo: check performance of pandas on big files
                gps_data.append(
                    [point.time, point.longitude, point.latitude, point.elevation]
                )

    gps_data = pd.DataFrame(
        gps_data, columns=["time", "longitude", "latitude", "elevation"]
    )
    gps_data.index = pd.to_datetime(gps_data.time)
    # remove tz for compatibility purpose with AI timestamp
    gps_data.index = gps_data.index.tz_convert(None)
    gps_data.drop("time", axis=1, inplace=True)
    if not gps_data.index.is_monotonic:
        gps_data.sort_index(inplace=True)
    return gps_data


def gpx_waypoints_to_gps(gpx_data: GPX = None) -> pd.DataFrame:
    """ Convert GPX waypoints to GPS

    Parameters
    ----------
    gpx_data:  GPX object that returns data from a parsed gpx file.

    Returns
    -------
    gps_data:  DataFrame where index are time and columns are latitude, longitude, trash_label

    Examples
    ---------
    >>> gps_data = gpx_to_gps('../../data/smartphone_video/sample.gpx')
    >>> gps_data
                                   longitude   latitude         trash_label
        time
        2019-04-01 12:24:28+00:00   0.097059  43.155730        Autre dechet
        2019-04-01 12:24:46+00:00   0.097036  43.155988        Autre dechet
        2019-04-01 12:24:46+00:00   0.097036  43.155988        Autre dechet
        2019-04-01 12:24:46+00:00   0.097036  43.155988   Bouteille boisson
        2019-04-01 12:25:04+00:00   0.096994  43.156326  Autres dechets +10

    """

    gps_data = []
    for waypoint in gpx_data.waypoints:
        gps_data.append(
            [waypoint.time, waypoint.longitude, waypoint.latitude, waypoint.name]
        )
    gps_data = pd.DataFrame(
        gps_data, columns=["time", "longitude", "latitude", "label"]
    )
    gps_data.index = gps_data.time
    gps_data.drop("time", axis=1, inplace=True)
    if not gps_data.index.is_monotonic:
        gps_data.sort_index(inplace=True)
    return gps_data


def pyproj_transform(
        longitude: float, latitude: float, source_epsg: int = 4326, target_epsg: int = 2154
) -> str:
    """ Applies geometrical transformation to a row of GPS coordinate

    Parameters
    ----------
    longitude: longitude coordinate
    latitude: latitude coordinate
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
    geo_source = Point(longitude, latitude)
    geo_target = transform(project, geo_source).wkt
    return geo_target


def add_geom_to_gps_data(gps_data: pd.DataFrame, **kwargs):
    """ Add projection to a given geometry to a GPS list of points

    Parameters
    ----------
    gps_data: list of dict  with gps point containing Longitude and Latitude

    Examples
    --------
    >>> gps_data
                                   latitude   longitude  elevation
        2018-01-24 19:27:58+00:00  33.126515 -117.327168    -17.228
        2018-01-24 19:27:59+00:00  33.126543 -117.327153    -18.199
        2018-01-24 19:28:12+00:00  33.126616 -117.325690    -18.440
        2018-01-24 19:28:13+00:00  33.126540 -117.327072    -19.161
        2018-01-24 19:28:14+00:00  33.126539 -117.327218    -18.472
    >>> add_geom_to_gps_data(gps_data)
    >>> gps_data
                                                   geom
        2018-01-24 19:27:58+00:00  33.126515  ...  POINT (-6843671.309553764 12301224.24713064)
        2018-01-24 19:27:59+00:00  33.126543  ...  POINT (-6843668.109889416 12301222.98998321)
        2018-01-24 19:28:12+00:00  33.126616  ...  POINT (-6843653.244167816 12301083.64126886)
        2018-01-24 19:28:13+00:00  33.126540  ...  POINT (-6843668.018846542 12301215.23885827)
        2018-01-24 19:28:14+00:00  33.126539  ...  POINT (-6843668.778535692 12301229.22991498)
    """
    # apply along axis the transformation from (lat, long) to geompoint(x, y, z)
    gps_data["geom"] = np.apply_along_axis(
        lambda gps_row: pyproj_transform(*gps_row, **kwargs),
        axis=1,
        arr=gps_data[["longitude", "latitude"]],
    )
    # NB: order 2 in speed comparison between numpy and pandas.
