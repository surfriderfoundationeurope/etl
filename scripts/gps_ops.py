# Parse GPX file
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
    gopro2gpx_script = ['./gopro2gpx_param.sh',video_name]
    result = subprocess.Popen(gopro2gpx_script, stdout=subprocess.PIPE)
    output = []
    i = 0
    for line in result.stdout:
        print(line)
        output.append(line)
    path='/tmp/'+video_name+'.gpx'
    return path

# Create GPX points list
''' gpsPointList function extract gps points from gpx file '''
''' gpxdata is a gpxpy object that returns data from a parsed gpx file'''
''' gpsPointList return a list of dictionnary points with Time, Lat, Long, Elev'''
def gpsPointList(gpxdata):
    point_list = []
    for track in gpxdata.tracks:
        for segment in track.segments: 
            for point in segment.points:
                point_info = {'Time':point.time,'Latitude':point.latitude,'Longitude':point.longitude,'Elevation':point.elevation}
                point_list.append(point_info)
    return point_list


#===============================
def getMediaInfo(mediafile):
    cmd = "mediainfo --Output=JSON %s"%(mediafile)
    proc = subprocess.Popen(cmd, shell=True,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    data = json.loads(stdout)
    return data

#===============================
def getDuration(mediafile):
    data = getMediaInfo(mediafile)
    duration = float(data['media']['track'][0]['Duration'])
    return duration


def createTime(time):
    new_time = time
    new_time = new_time + timedelta(seconds=1)
    return new_time

def createLatitude(lat1,lat2):
    new_latitude = (lat1+lat2)/2
    new_latitude = round(new_latitude,6)
    return new_latitude

def createLongitude(long1,long2):
    new_longitude = (long1+long2)/2
    new_latitude = round(new_longitude,6)
    return new_longitude

def createElevation(elev1,elev2):
    new_elevation = (elev1+elev2)/2
    new_elevation = round(new_elevation,6)
    return new_elevation


def fillGPS(inputGPSList,videoLength):
    filledGps = inputGPSList.copy()
    gps_length = len(filledGps)
    iteration_length = int((filledGps[gps_length-1]['Time'] - filledGps[0]['Time']).total_seconds())
    #print(iteration_length)
    ## this section output a filled gps list of length iteration_length+1 = Delta T between last gps timestamp and first one
    i = 0
    while i < (iteration_length):
#        print(i)
        delta = filledGps[i+1]['Time']-filledGps[i]['Time']
        delta = int(delta.total_seconds())
        if delta > 1: # adding a newly created element at index i+1
            #print(i)
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
    gpsShapePoint = {'Time':gpsLongLatPoint['Time'],'the_geom':Point(gpsLongLatPoint['Longitude'],gpsLongLatPoint['Latitude']),'Elevation':gpsLongLatPoint['Elevation']}
    return gpsShapePoint

def longLat2shapeList(gpsLongLagList):
    gpsShapeList = []
    for gpsPoint in gpsLongLagList:
        gpsShapePoint = longLat2shapePoint(gpsPoint)
        gpsShapeList.append(gpsShapePoint)
    return gpsShapeList



def geometryTransfo(gpsShapePoint):
    project = partial(
    pyproj.transform,
    pyproj.Proj(init='epsg:4326'), # source coordinate system
    pyproj.Proj(init='epsg:2154')) # destination coordinate system

    geo1 = gpsShapePoint['the_geom']
    geo2 = transform(project,geo1)

    return geo2

def gps2154(gpsShapePointsFilled):
    gps2154Points = []
    for point in tqdm(gpsShapePointsFilled):
        geo2154 = geometryTransfo(point)
        gps2154Point = {'Time':point['Time'],'the_geom':geo2154,'Elevation':point['Elevation']}
        gps2154Points.append(gps2154Point)
    return gps2154Points


print("hello from gps.py")