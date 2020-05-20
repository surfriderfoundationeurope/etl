# Parse GPX file
import os
import gpxpy
import gpxpy.gpx
import json
import subprocess
import datetime
from datetime import datetime
from datetime import timedelta
from shapely.geometry import Point
from functools import partial
import pyproj
from shapely.ops import transform
from tqdm import tqdm
from gopro2gpx.main import extract
from .exceptions import ETLError


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


def parse_gpx(gpx_path:str)->object:
    """Parse a gpx file to extract gps information

    Arguments:
        gpx_path {str} -- the path of a gpx file

    Returns:
        gpx_data -- the gpx data as a gpxpy object
    """
    gpx_file = open(gpx_path,'r',encoding='utf-8')
    gpx_data = gpxpy.parse(gpx_file)
    return gpx_data

def get_gps_point_list(gpx_data:object)->list:
    """Get a list of GPS point from a gpx_data object

    Arguments:
        gpx_data {object} -- the gpx data as a gpxpy object

    Returns:
        point_list -- a list of GPS points
    """
    point_list = []
    for track in gpx_data.tracks:
        for segment in track.segments:
            for point in segment.points:
                point_info = {'Time': point.time, 'Latitude': point.latitude,
                              'Longitude': point.longitude, 'Elevation': point.elevation}
                point_list.append(point_info)
    return point_list


def create_time(time:datetime)->datetime:
    """Create time by adding 1 second to time input

    Arguments:
        time {datetime} -- a time value

    Returns:
        new_time -- the new time created by adding 1 second
    """
    new_time = time
    new_time = new_time + timedelta(seconds=1)
    return new_time


def create_latitude(lat1:float, lat2:float)->float:
    """Create latitude as the average of lat1 and lat2

    Arguments:
        lat1 {float} -- a first latitude value
        lat2 {float} -- a second latitute value

    Returns:
        new_latitude -- the average latitude
    """
    new_latitude = (lat1+lat2)/2
    new_latitude = round(new_latitude, 6)
    return new_latitude


def create_longitude(long1:float, long2:float)->float:
    """Create longitude as the average of long1 and long2

    Arguments:
        long1 {float} -- a first longitude value
        long2 {float} -- a second longitude value

    Returns:
        new_longitude -- the average longitude
    """
    new_longitude = (long1+long2)/2
    new_longitude = round(new_longitude, 6)
    return new_longitude


def create_elevation(elev1:float, elev2:float)->float:

    new_elevation = (elev1+elev2)/2
    new_elevation = round(new_elevation, 6)
    return new_elevation


def fill_gps(input_gps_list:list, video_length:float)->list:
    """Fill an input gps list when there are missing value with regard to time(second)

    Arguments:
        input_gps_list {list} -- a list of gps point
        video_length {float} -- the length of related video from which gps point are taken from

    Returns:
        filled_gps -- the list of gps point filled with regard to time
    """
    filled_gps = input_gps_list.copy()
    gps_length = len(filled_gps)
    iteration_length = int(
        (filled_gps[gps_length-1]['Time'] - filled_gps[0]['Time']).total_seconds())
    # this section output a filled gps list of length iteration_length+1 = Delta T between last gps timestamp and first one
    i = 0
    while i < (iteration_length):
        delta = filled_gps[i+1]['Time']-filled_gps[i]['Time']
        delta = int(delta.total_seconds())
        if delta > 1:  # adding a newly created element at index i+1
            missing_time = createTime(filled_gps[i]['Time'])
            missing_latitude = createLatitude(
                filled_gps[i]['Latitude'], filled_gps[i+1]['Latitude'])
            missing_longitude = createLongitude(
                filled_gps[i]['Longitude'], filled_gps[i+1]['Longitude'])
            missing_elevation = createElevation(
                filled_gps[i]['Elevation'], filled_gps[i+1]['Elevation'])
            new_gps = {'Time': missing_time, 'Latitude': missing_latitude,
                       'Longitude': missing_longitude, 'Elevation': missing_elevation}
            filled_gps.insert(i+1, new_gps)
        i = i+1
    # this section add missing point at the end of the list, in case filled_gps initial Delta time length is less than actual video length
    if len(filled_gps) < video_length:
        j = 0
        while len(filled_gps) < video_length:
            filled_gps.insert(len(filled_gps), filled_gps[len(filled_gps)-1])
            j = j+1

    return filled_gps


def long_lat_to_shape_point(gps_long_lat_point:dict)->dict:
    """Convert a long/lat of gps point to shape obect from shapely

    Arguments:
        gps_long_lat_point {dict} -- a gps point with long/lat coordinates

    Returns:
        gps_shape_point -- a gps point with shape representation of long/lat
    """
    gps_shape_point = {'Time': gps_long_lat_point['Time'], 'the_geom': Point(
        gps_long_lat_point['Longitude'], gps_long_lat_point['Latitude']),'Latitude':gps_long_lat_point['Latitude'],'Longitude':gps_long_lat_point['Longitude'], 'Elevation': gps_long_lat_point['Elevation']}
    return gps_shape_point



def transform_geo(gps_shape_point:dict)->str:
    """Transform a gps geometry representation from 4326 to 2154

    Arguments:
        gps_shape_point {dict} -- a gps point with long/lat represented as shape Point

    Returns:
        geo2 -- the shape point in geometry 2154
    """
    project = partial(
        pyproj.transform,
        pyproj.Proj(init='epsg:4326'),  # source coordinate system
        pyproj.Proj(init='epsg:2154'))  # destination coordinate system

    geo1 = gps_shape_point['the_geom']
    geo2 = transform(project, geo1)
    return geo2

