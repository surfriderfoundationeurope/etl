# Parse GPX file
import os
import gpxpy
import gpxpy.gpx
import json
import subprocess
import datetime
import pandas as pd
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


def get_gpx_name(file_name:str)->str:
    """Get gpx file name associated with a video

    Arguments:
        file_name {str} -- a video name for which gpx file name to be created

    Returns:
        gpx_file_name -- the name of the gpx file associated with a video
    """
    file_prefix = os.path.splitext(file_name)[0]
    gpx_file_name = file_prefix + '.gpx'
    return gpx_file_name

def get_json_name(file_name:str)->str:
    """Get json file name associated with a video

    Arguments:
        file_name {str} -- a video name for which json file name to be created

    Returns:
        json_file_name -- the name of the json file associated with a video
    """
    file_prefix = os.path.splitext(file_name)[0]
    json_file_name = file_prefix + '.json'
    return json_file_name

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

def parse_json(json_path:str)->dict:
    """Parse a JSON file produced by Plastic Origin Mobile App

    Args:
        json_path (str): the path of a json file produced by mobile app

    Returns:
        dict: the json data as a dictionnary
    """
    with open(json_path) as json_file:
        json_data = json.load(json_file)
    return json_data

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


def get_json_gps_list(json_data:dict)->list:
    """Get a list of GPS point from a json_data object

    Args:
        json_data (dict): the gps data as a json dict

    Returns:
        list: a list of GPS point
    """
    point_list = []
    for point in json_data['positions']:
        # clean & cast time to datetime
        time = datetime.strptime(point['date'][:19].replace("T"," "),'%Y-%m-%d %H:%M:%S')
        point_info = {'Time': time, 'Latitude': point['lat'],
                              'Longitude': point['lng'], 'Elevation': 0}
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
            missing_time = create_time(filled_gps[i]['Time'])
            missing_latitude = create_latitude(
                filled_gps[i]['Latitude'], filled_gps[i+1]['Latitude'])
            missing_longitude = create_longitude(
                filled_gps[i]['Longitude'], filled_gps[i+1]['Longitude'])
            missing_elevation = create_elevation(
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

def get_df_trash_gps(df_predictions:pd.DataFrame,gps_points_filled:list)->pd.DataFrame:
    """Get GPS information of a Trash as a Dataframe

    Arguments:
        df_predictions {pd.DataFrame} -- an AI prediction as a Dataframe (using get_df_predictio from utils.ai)
        gps_points_filled {list} -- a list filled list of GPS points

    Returns:
        df_trash_gps -- the gps coordinates of all trashes detected by AI as a Dataframe
    """
    geo_2154_trash_gps_list = []
    time_indexes = df_predictions['time_index']
    for time_index in time_indexes:
        trash_gps = gps_points_filled[time_index]
        shape_trash_gps = long_lat_to_shape_point(trash_gps)
        geo_2154 = transform_geo(shape_trash_gps)
        geo_2154_trash_gps = {'Time': shape_trash_gps['Time'], 'the_geom': geo_2154,'Latitude':shape_trash_gps['Latitude'],'Longitude':shape_trash_gps['Longitude'], 'Elevation': shape_trash_gps['Elevation']}
        geo_2154_trash_gps_list.append(geo_2154_trash_gps)
        df_trash_gps = pd.DataFrame(geo_2154_trash_gps_list)
    return df_trash_gps


def get_df_manual_gps(gpx_data_waypoints:list)->pd.DataFrame:
    """Get GPS coordinate as a DataFrame from a manually collected trash gpx file

    Arguments:
        gpx_data_waypoints {list} -- the waypoints list from an OSM track gpx_data parsing

    Returns:
        df_manual_gps -- the gps info as a DataFrame associated with manually collected trash 
    """
    gps_list = []
    for waypoint in gpx_data_waypoints:
        gps_point = {'Time': waypoint.time, 'Latitude': waypoint.latitude,
                              'Longitude': waypoint.longitude, 'Elevation': waypoint.elevation}
        shape_gps_point = long_lat_to_shape_point(gps_point)
        geo_2154 = transform_geo(shape_gps_point)
        geo_2154_gps_point = {'Time': shape_gps_point['Time'],'the_geom':geo_2154, 'Latitude':shape_gps_point['Latitude'],'Longitude': shape_gps_point['Longitude'], 'Elevation':shape_gps_point['Elevation']}
        gps_list.append(geo_2154_gps_point)
    df_manual_gps = pd.DataFrame(gps_list)
    return df_manual_gps


def get_df_json_manual_gps(json_data:dict)->pd.DataFrame:
    """Get GPS coordinate as a DataFrame from a manually collected trash JSON file

    Args:
        json_data (dict): the json data from the Plastic Origin Mobile app

    Returns:
        pd.DataFrame: the gps info as a DataFrame associated with manually collected trash
    """
    gps_list = []
    for trash in json_data['trashes']:
        time = datetime.strptime(trash['date'][:19].replace("T"," "),'%Y-%m-%d %H:%M:%S')
        gps_point = {'Time': time, 'Latitude': trash['lat'],'Longitude': trash['lng'], 'Elevation': 0}
        shape_gps_point = long_lat_to_shape_point(gps_point)
        geo_2154 = transform_geo(shape_gps_point)
        geo_2154_gps_point = {'Time': shape_gps_point['Time'],'the_geom':geo_2154, 'Latitude':shape_gps_point['Latitude'],'Longitude': shape_gps_point['Longitude'], 'Elevation':shape_gps_point['Elevation']}
        gps_list.append(geo_2154_gps_point)
    df_manual_gps = pd.DataFrame(gps_list)
    return df_manual_gps
