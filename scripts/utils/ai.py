import json
import logging 
import requests


logger = logging.getLogger()

def is_ai_ready(url:str)->bool:
    """check whether AI service is available

    Arguments:
        url {str} -- the url formated as follow 'http://ai-service.com'

    Returns:
        ready -- a boolean value saying whether AI service is available
    """
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
    """Get prediction from AI service over a video media

    Arguments:
        video_name {str} -- the name of the video to predict on downloaded within /tmp
        url {str} -- the url formated as follow 'http://ai-service.com'

    Returns:
        output {str} -- the prediction made by the AI service
    """
    files = {'file': (f'/tmp/{video_name}', open(f'/tmp/{video_name}', 'rb'), 'application/octet-stream')}
    response = requests.post(url, files=files)
    if not response.ok:
        logger.error(f'Request to AI failed wih reason {response.reason}.')
    output = [response._content]
    return output


def get_json_prediction(pred:str)->dict:
    """Get the AI prediction formated as JSON dictionnary object

    Arguments:
        pred {str} -- an AI prediction from AI service as a string

    Returns:
        json_prediction -- the AI prediction as JSON dictionnary
    """
    string_prediction = str(pred[0])[2:-3] #removing 2 x first and 3 last characters of pred
    json_prediction = json.loads(string_prediction)
    return json_prediction


def get_trash_label(frame_to_box:dict)->str:
    """Get label from a frame_to_box dictionnary from an AI prediction

    Arguments:
        frame_to_box {dict} -- the data for a unique trash from the AI prediction

    Returns:
        frame_to_box['label'] -- the label value predicted by the AI for a trash
    """
    return frame_to_box['label']


def get_trash_time_index(trash:dict)->int:
    """Get the time index for a trash, the first time it is identified

    Arguments:
        trash {dict} -- [description]

    Returns:
        int -- the index when the trash is identified for the first time
    """
    frame_to_box = trash['frame_to_box']    
    return int(list(frame_to_box.keys())[0])


def get_trash_time_stamp(time_index:int,media_fps:float)->int:
    """Get trash time stamp with regard to the video media it is identified from

    Arguments:
        time_index {int} -- the index when the trash is identified for the first time
        media_fps {float} -- the fps of the media where trash is identified

    Returns:
        int -- the timestamp of the trash
    """
    return int(time_index / media_fps)


def map_label_to_trash_id_PG(label:str)->str:
    """Map label of a trash to equivalent ID within PostGre server

    Arguments:
        label {str} -- the label of the trash

    Returns:
        id_PG -- the equivalent id within PG Trash table of trash label
    """
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
    id_PG =  switcher.get(label, "nothing")
    return id_PG
