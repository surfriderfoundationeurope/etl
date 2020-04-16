import json 
import os
import subprocess
import requests

def isAIready(url):
    AI_ready = requests.get(url)
    if AI_ready.status_code == 200:
        print('AI is ready')
        print('HTTP Status code: ',AI_ready.status_code)
        print(AI_ready.headers)
    else:
        print("AI not found, an error has occured")
        print("Server Answer: ",AI_ready)
        print("HTTP Status Code: ",AI_ready.status_code)
        print("HTTP Status Code: ",AI_ready.raise_for_status())

''' getPrediction function sends curl request to Surfrider AI'''
''' video name is the name of a locally downloaded video from Azure'''
''' video name is passed as an argument to curl_request script '''
''' curl_request script sends actual POST request to Surfrider AI'''
def getPrediction(video_name):
    curl_request_script = ['./curl_request_param.sh',video_name]
    output = []
    request_answer = subprocess.Popen(curl_request_script, stdout=subprocess.PIPE)
    i = 0
    for line in request_answer.stdout:
        print(line)
        output.append(line)
    return output


''' jsonPrediction cast a prediction from getPrediction function '''
''' from a list prediction to a string then dictionnary with json_loads '''
def jsonPrediction(pred):
    string_prediction = str(pred[0])[2:-3] #removing 2 x first and 3 last characters of pred
    json_prediction = json.loads(string_prediction)
    return json_prediction


''' getTrashLabel return label from a frame_to_box'''
def getTrashLabel(frame_2_box):
    return frame_2_box['label']

''' mapLabelTrashId is a switch that converts label to TrashId'''
''' param is label that comes from AI predictions dictionnary jsonPrediction'''
def mapLabel2TrashId(label):
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