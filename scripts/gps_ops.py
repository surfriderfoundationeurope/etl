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

def goproToGPX(video_name):
    '''
    goproToGPX function extracts GPX file from raw GoPro video
    GPX extraction is delegated to shell scripts that calls gopro2gpx python helper
    Input: the name of a video locally available within /tmp
    Output: the path of the GPX generated file
    '''
    gopro2gpx_script = ['./gopro2gpx_param.sh',video_name]
    result = subprocess.Popen(gopro2gpx_script, stdout=subprocess.PIPE)
    output = []
    i = 0
    for line in result.stdout:
        print(line)
        output.append(line)
    path='/tmp/'+video_name+'.gpx'
    return path


def gpsPointList(gpxdata):
    ''' 
    gpsPointList function extract gps points from gpx file
    Input: gpxdata is a gpxpy object that returns data from a parsed gpx file
    Output: gpsPointList return a list of dictionnary points with Time, Lat, Long, Elev
    '''

    point_list = []
    for track in gpxdata.tracks:
        for segment in track.segments: 
            for point in segment.points:
                point_info = {'Time':point.time,'Latitude':point.latitude,'Longitude':point.longitude,'Elevation':point.elevation}
                point_list.append(point_info)
    return point_list


def getMediaInfo(mediafile):
    '''
    getMediaInfo function extract metadata info about a media file, using mediainfo shell command
    Input: a media file like a video
    Output: the metadata about the media
    '''
    cmd = "mediainfo --Output=JSON %s"%(mediafile)
    proc = subprocess.Popen(cmd, shell=True,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    data = json.loads(stdout)
    return data


def getDuration(mediafile):
    '''
    getDuration function get the duration of a mediafile, typically a video
    Input: a mediafile, on which we then extract the mediainfo
    Output: the duration of the media
    '''
    data = getMediaInfo(mediafile)
    duration = float(data['media']['track'][0]['Duration'])
    return duration


def createTime(time):
    '''
    createTime function creates a timestamp by adding 1 seconds to input
    Input: a time value, as datetime python format
    Output: the newly created timestamp
    '''
    new_time = time
    new_time = new_time + timedelta(seconds=1)
    return new_time

def createLatitude(lat1,lat2):
    '''
    createLatitude function creates a new Latitude by averaging two others
    Input: lat1 and lat2, 2 x latitudes
    Output: the average latitude
    '''
    new_latitude = (lat1+lat2)/2
    new_latitude = round(new_latitude,6)
    return new_latitude

def createLongitude(long1,long2):
    '''
    createLongitude function creates a new Longitude by averaging two others
    Input: long1 and long2, 2 x Longitudes
    Output: the average Longitude
    '''
    new_longitude = (long1+long2)/2
    new_latitude = round(new_longitude,6)
    return new_longitude

def createElevation(elev1,elev2):
    '''
    createElevation function creates a new Elevation by averaging two others
    Input: elev1 and elev2, 2 x Elevations
    Output: the average Elevation
    '''
    new_elevation = (elev1+elev2)/2
    new_elevation = round(new_elevation,6)
    return new_elevation


def fillGPS(inputGPSList,videoLength):
    '''
    fillGPS function will complete a list of GPS point, by filling in missing points in time series
    Input: 
     - a GPS point list, that comes from the output of the gpsPointList function
     - the related video length, from which GPS data is extracted. Value is given by getDuration
    Output:
    '''
    filledGps = inputGPSList.copy()
    gps_length = len(filledGps)
    iteration_length = int((filledGps[gps_length-1]['Time'] - filledGps[0]['Time']).total_seconds())
    ## this section output a filled gps list of length iteration_length+1 = Delta T between last gps timestamp and first one
    i = 0
    while i < (iteration_length):
        delta = filledGps[i+1]['Time']-filledGps[i]['Time']
        delta = int(delta.total_seconds())
        if delta > 1: # adding a newly created element at index i+1
            missing_time = createTime(filledGps[i]['Time'])
            missing_latitude = createLatitude(filledGps[i]['Latitude'],filledGps[i+1]['Latitude'])
            missing_longitude = createLongitude(filledGps[i]['Longitude'],filledGps[i+1]['Longitude'])
            missing_elevation = createElevation(filledGps[i]['Elevation'],filledGps[i+1]['Elevation'])
            new_gps = {'Time':missing_time,'Latitude':missing_latitude,'Longitude':missing_longitude,'Elevation':missing_elevation}
            filledGps.insert(i+1,new_gps)
        i = i+1
    ## this section add missing point at the end of the list, in case filledGps initial Delta time length is less than actual video length
    if len(filledGps) < videoLength:
        j = 0
        while len(filledGps) < videoLength:
            filledGps.insert(len(filledGps),filledGps[len(filledGps)-1])
            j = j+1

    return filledGps


def longLat2shapePoint(gpsLongLatPoint):
    '''
    longLat2shapePoint function creats a GPS point with a 'the_geom' key instead of Long/Lat pair
    Input: a GPS Point with 'Longitude' and 'Latitude' keys
    Output: a dictionnary for a GPS data with key 'the_geom' built from Long/Lat
    '''
    gpsShapePoint = {'Time':gpsLongLatPoint['Time'],'the_geom':Point(gpsLongLatPoint['Longitude'],gpsLongLatPoint['Latitude']),'Elevation':gpsLongLatPoint['Elevation']}
    return gpsShapePoint


def longLat2shapeList(gpsLongLatList):
    '''
    longLat2shapeList function creates a new GPS Point list with 'the_geom' key instead of LongLat
    Input: a gpsLongLatList that comes from fillGPS, as we expect the missing fill operation done
    Output: a new GPS point list with 'the_geom' key
    '''
    gpsShapeList = []
    for gpsPoint in gpsLongLatList:
        gpsShapePoint = longLat2shapePoint(gpsPoint)
        gpsShapeList.append(gpsShapePoint)
    return gpsShapeList


def geometryTransfo(gpsShapePoint):
    '''
    geometryTransfo function convert a GPS point list from a geo representation to another
    Input: a GPS shape point, meaning, a dictionnary with 'the_geom' key instead of LongLat
    Output: a GPS shape point with the target geometry, here 2154
    '''
    project = partial(
    pyproj.transform,
    pyproj.Proj(init='epsg:4326'), # source coordinate system
    pyproj.Proj(init='epsg:2154')) # destination coordinate system

    geo1 = gpsShapePoint['the_geom']
    geo2 = transform(project,geo1)
    return geo2


def gps2154(gpsShapePointsFilled):
    '''
    gps2154 function transforms a GPS shape point list, into the 2154 geometry
    Input: a GPS shape point list where GPS point source geometry is 4326
    Output: a GPS shape point list where GPS point target geometry is 2154
    '''
    gps2154Points = []
    for point in tqdm(gpsShapePointsFilled):
        geo2154 = geometryTransfo(point)
        gps2154Point = {'Time':point['Time'],'the_geom':geo2154,'Elevation':point['Elevation']}
        gps2154Points.append(gps2154Point)
    return gps2154Points


print("hello from gps.py")