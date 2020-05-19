import json
import logging 
import requests


logger = logging.getLogger()

def ai_ready(url):
    '''
    AIready function evaluate whether AI inference service is available
    Input: takes the url of the AI service to evaluate availability
    Output: returns ready status, a boolean status
    '''
    ready = False
    try:
        AI_request = requests.get(url)
        logger.info(f'HTTP Status Code:{AI_request.status_code}')
        if AI_request.status_code == 200:
            logger.info("AI inference service is available")
            ready = True
            return ready
        else:
            logger.info(f'HTTP Status Code: {AI_request.status_code}')
            logger.info("AI server is responding but there might be an issue")
    except requests.exceptions.RequestException:
        logger.error("AI not found, an error has occured")
        return ready


def get_prediction(video_name:str,url:str)->str:
    '''
    getPrediction sends POST request to an AI inference service, delegated to bash script subprocess
    Input: the name of a video which is expected to be dowloaded in local /tmp before
    Output: the prediction made by AI: a json-like format data but as a list
    '''
    files = {'file': (f'/tmp/{video_name}', open(f'/tmp/{video_name}', 'rb'), 'application/octet-stream')}
    response = requests.post(url, files=files)
    if not response.ok:
        logger.error(f'Request to AI failed wih reason {response.reason}.')
    output = [response._content]
    return output


def json_prediction(pred:str)->dict:
    ''' 
    jsonPrediction cast a prediction from getPrediction function
    Input: pred, the string result of the previous getPrediction function
    Output: json_prediction, a dictionnary built from a subset of pred string
    '''
    string_prediction = str(pred[0])[2:-3] #removing 2 x first and 3 last characters of pred
    json_prediction = json.loads(string_prediction)
    return json_prediction


def get_trash_label(frame_2_box:dict)->str:
    ''' 
    getTrashLabel return label from a frame_to_box
    Input: a frame_2_box dictionnary from jsonPrediction
    Output: the value of predicted label
    '''
    return frame_2_box['label']


def get_trash_time_index(frame_2_box:dict)->int:
    temp_dico = frame_2_box['frame_to_box']    
    return int(list(temp_dico.keys())[0])


def get_trash_time_stamp(timeIndex:int,mediaFPS:float)->int:
    """ Get trash timestamp with regard to media

    Arguments:
        timeIndex {int} -- [description]
        mediaFPS {float} -- [description]

    Returns:
        int -- [description]
    """
    return int(timeIndex / mediaFPS)


def map_label_2_trash_id_PG(label:str)->str:
    '''
    mapLabel2TrashIdPG function is a different mapping between a predicted label by AI and TrashId as defined within TrashType table
    Input: a label predicted by AI
    Output: a TrashId as defined in TrashType table
    '''
    switcher = { 
        "others":"1", #"autre dechet" in PG Data Model mapped to IA "others" label
        "dechet agricole":"2",
        "bottles":"3", #"bouteille boisson" in PG Data Model mapped to IA "bottles" label
        "fragments":"4",#"industriel ou construction in PG Data Model mapped to IA "fragments" label
        "peche et chasse":"5",
        "emballage alimentaire":"6",
        "objet vie courante":"7",
        "autres dechets +10":"8"
    } 
    return switcher.get(label, "nothing")
