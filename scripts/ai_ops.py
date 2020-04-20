import json 
import os
import subprocess
import requests

import requests
import subprocess
import json

def AIready(url):
    '''
    AIready function evaluate whether AI inference service is available
    Input: takes the url of the AI service to evaluate availability
    Output: returns ready status, a boolean status
    '''
    ready = False
    try:
        AI_request = requests.get(url)
        print("HTTP Status Code: ",AI_request.status_code)
        if AI_request.status_code == 200:
            print("AI inference service is available")
            ready = True
            return ready
        else:
            print("HTTP Status Code: ",AI_request.status_code)
            print("AI server is responding but there might be an issue")
    except requests.exceptions.RequestException:
        print("AI not found, an error has occured")
        return ready


def getPrediction(video_name):
    '''
    getPrediction sends POST request to an AI inference service, delegated to bash script subprocess
    Input: the name of a video which is expected to be dowloaded in local /tmp before
    Output: the prediction made by AI: a json-like format data but as a list
    '''
    curl_request_script = ['./curl_request_param.sh',video_name]
    output = []
    request_answer = subprocess.Popen(curl_request_script, stdout=subprocess.PIPE)
    i = 0
    for line in request_answer.stdout:
        print(line)
        output.append(line)
    return output


def jsonPrediction(pred):
    ''' 
    jsonPrediction cast a prediction from getPrediction function
    Input: pred, the string result of the previous getPrediction function
    Output: json_prediction, a dictionnary built from a subset of pred string
    '''
    string_prediction = str(pred[0])[2:-3] #removing 2 x first and 3 last characters of pred
    json_prediction = json.loads(string_prediction)
    return json_prediction


def getTrashLabel(frame_2_box):
    ''' 
    getTrashLabel return label from a frame_to_box
    Input: a frame_2_box dictionnary from jsonPrediction
    Output: the value of predicted label
    '''
    return frame_2_box['label']


def mapLabel2TrashId(label):
    ''' 
    mapLabelTrashId is a switch that converts label to TrashId
    Input: label that comes from getTrashLabel from jsonPrediction dictionnary 
    Output: a TrashId, which is meaningful with respect to Trash_Type table in PostGre
    '''
    switcher = { 
    "Fishing or Hunting":"89B44BAA-69AA-4109-891A-128E012E7E07",
    "Food Packaging":"185FEFA2-EEF2-47A8-873E-26032A4BB3C3",
    "Unknown":"BB4DEA69-218A-40CC-A000-2AE17C37152C",
    "Industrial or Construction Debris":"2A863E38-E5D0-455F-87CE-2B75DA29F59A",
    "fragments":"ED401B92-DC24-44C0-A52A-34CE831092BF",
    "Agricultural Waste":"36B2AFEB-7A7C-44B5-A790-5E5C73BA144D",
    "others":"4BEC18FC-BC48-45B7-AFDA-6BA96BD80921",
    "Common Household Items":"C68E90CF-6E65-4474-BC60-72E1C8513F55",
    "plastic":"6961D0DB-928C-419E-9985-98EEEAF552C7",
    "bottles":"9780940B-D06C-4AAB-8003-AB914981E87A",
    "Drinking Bottles":"BCF549A8-AECD-4BC9-B9B8-B94A8F3758D5",
    "Unknown10":"BC7BB564-BE04-4B4B-9913-FF69780B93A6"
    } 
    return switcher.get(label, "nothing")
    
print("hello from aiprediction.py")