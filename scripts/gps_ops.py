# Parse GPX file
import json
import os
import subprocess
from datetime import timedelta
from functools import partial

import pyproj
from shapely.geometry import Point
from shapely.ops import transform
from tqdm import tqdm
from pymediainfo import MediaInfo


def goproToGPX(video_name):
    """
    goproToGPX function extracts GPX file from raw GoPro video
    GPX extraction is delegated to shell scripts that calls gopro2gpx python helper
    Input: the name of a video locally available within /tmp
    Output: the path of the GPX generated file
    """
    gopro2gpx_script = ["./gopro2gpx_param.sh", video_name]
    result = subprocess.Popen(gopro2gpx_script, stdout=subprocess.PIPE)
    output = []
    i = 0
    for line in result.stdout:
        print(line)
        output.append(line)
    path = "/tmp/" + video_name + ".gpx"
    return path


def goproToGPX(video_name):
    result = os.system(
        f"python /tmp/gopro2gpx/gopro2gpx.py -s -vvv /tmp/{video_name} /tmp/{video_name}"
    )
    path = "/tmp/" + video_name + ".gpx"
    return path


def gpx_to_gps(gpx_data) -> list:
    """ Convert GPX to GPS

    Parameters
    ----------
    gpx_data:  GPX object that returns data from a parsed gpx file

    Returns
    -------
    gps_data: list of dictionaries points with Time, Lat, Long, Elev

    """

    gps_data = []
    for track in gpx_data.tracks:
        for segment in track.segments:
            for point in segment.points:
                point_info = {
                    "Time": point.time,
                    "Latitude": point.latitude,
                    "Longitude": point.longitude,
                    "Elevation": point.elevation,
                }
                gps_data.append(point_info)
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

    """
    media_info = get_media_info(media_path)
    duration = media_info.get('Duration')
    return duration


def createTime(time):
    """
    createTime function creates a timestamp by adding 1 seconds to input
    Input: a time value, as datetime python format
    Output: the newly created timestamp
    """
    new_time = time
    new_time = new_time + timedelta(seconds=1)
    return new_time


def createLatitude(lat1, lat2):
    """
    createLatitude function creates a new Latitude by averaging two others
    Input: lat1 and lat2, 2 x latitudes
    Output: the average latitude
    """
    new_latitude = (lat1 + lat2) / 2
    new_latitude = round(new_latitude, 6)
    return new_latitude


def createLongitude(long1, long2):
    """
    createLongitude function creates a new Longitude by averaging two others
    Input: long1 and long2, 2 x Longitudes
    Output: the average Longitude
    """
    new_longitude = (long1 + long2) / 2
    new_longitude = round(new_longitude, 6)
    return new_longitude


def createElevation(elev1, elev2):
    """
    createElevation function creates a new Elevation by averaging two others
    Input: elev1 and elev2, 2 x Elevations
    Output: the average Elevation
    """
    new_elevation = (elev1 + elev2) / 2
    new_elevation = round(new_elevation, 6)
    return new_elevation


def fillGPS(inputGPSList, videoLength):
    """
    fillGPS function will complete a list of GPS point, by filling in missing points in time series
    Input: 
     - a GPS point list, that comes from the output of the gpsPointList function
     - the related video length, from which GPS data is extracted. Value is given by getDuration
    Output:
    """
    filledGps = inputGPSList.copy()
    gps_length = len(filledGps)
    iteration_length = int(
        (filledGps[gps_length - 1]["Time"] - filledGps[0]["Time"]).total_seconds()
    )
    ## this section output a filled gps list of length iteration_length+1 = Delta T between last gps timestamp and first one
    i = 0
    while i < (iteration_length):
        delta = filledGps[i + 1]["Time"] - filledGps[i]["Time"]
        delta = int(delta.total_seconds())
        if delta > 1:  # adding a newly created element at index i+1
            missing_time = createTime(filledGps[i]["Time"])
            missing_latitude = createLatitude(
                filledGps[i]["Latitude"], filledGps[i + 1]["Latitude"]
            )
            missing_longitude = createLongitude(
                filledGps[i]["Longitude"], filledGps[i + 1]["Longitude"]
            )
            missing_elevation = createElevation(
                filledGps[i]["Elevation"], filledGps[i + 1]["Elevation"]
            )
            new_gps = {
                "Time": missing_time,
                "Latitude": missing_latitude,
                "Longitude": missing_longitude,
                "Elevation": missing_elevation,
            }
            filledGps.insert(i + 1, new_gps)
        i = i + 1
    ## this section add missing point at the end of the list, in case filledGps initial Delta time length is less than actual video length
    if len(filledGps) < videoLength:
        j = 0
        while len(filledGps) < videoLength:
            filledGps.insert(len(filledGps), filledGps[len(filledGps) - 1])
            j = j + 1

    return filledGps


def points_to_shape(gps_points: list) -> list:
    """ Add shape to gps point

    Parameters
    ----------
    gps_points: list of dict  with gps point containing Longitude and Latitude

    Returns
    -------
    gps_list: same with each point having key "the_geom"
    """
    for gps_point in gps_points:
        gps_point['the_geom'] = Point(gps_point["Longitude"], gps_point["Latitude"])
    return gps_points


def point_to_2154(gps_point: dict) -> Point:
    """Convert a GPS point from a geo representation to another

    Parameters
    ----------
    gps_point:  GPS shape point with key "the_geom"

    Returns
    -------
    geo2: GPS shape point with the target geometry, here 2154

    """
    project = partial(
        pyproj.transform,
        pyproj.Proj(init="epsg:4326"),  # source coordinate system
        pyproj.Proj(init="epsg:2154"),
    )  # destination coordinate system

    geo1 = gps_point["the_geom"]
    geo2 = transform(project, geo1)
    return geo2


def points_to_2154(gps_points: list) -> list:
    """ Add 2154 geometry to gps shape point

    Parameters
    ----------
    gps_shape_points: GPS shape point list where GPS point source geometry is 4326

    Returns
    -------
    gps_list: GPS shape point list where GPS point target geometry is 2154
    """
    for gps_point in gps_points:
        gps_point["the_geom"] = point_to_2154(gps_point)
    return gps_points
