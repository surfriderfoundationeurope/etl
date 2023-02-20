import json
import logging
import pandas as pd
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


def get_trash_first_time(trash:dict)->int:
    """Get the time index for a trash, the first time it is identified

    Arguments:
        trash {dict} -- [description]

    Returns:
        fist_index -- the index when the trash is identified for the first time
    """
    frame_to_box = trash['frame_to_box']
    first_index = int(list(frame_to_box.keys())[0])
    return first_index


def get_trash_time_index(prediction:dict,media_fps:float)->int:
    """ Get trash time stamp

    Arguments:
        prediction {dict} -- the prediction made by AI of a unique trash
        media_fps {float} -- the FPS of the media where the trash comes from

    Returns:
        time_index -- the timestamp of the trash with regard to video it comes from
    """
    first_index = get_trash_first_time(prediction)
    time_index = int(first_index / media_fps)
    return time_index


def get_clean_timed_prediction(prediction:dict,media_fps:int)->dict:
    """Get timed prediction with single frame_to_box

    Arguments:
        prediction {dict} -- a single prediction from a dictionary of AI predictions
        media_fps {float} -- the FPS of the media where the trash comes from

    Returns:
        timed_prediction -- a prediction with the first frame_to_box only & a time_index additional key/value pair
    """
    first_index = str(get_trash_first_time(prediction))
    clean_frame_to_box = prediction['frame_to_box'][first_index]
    time_index = get_trash_time_index(prediction,media_fps)
    trash_type_id =  int(map_label_to_trash_id_PG(prediction['label']))
    timed_prediction = {'time_index':int(time_index),'frame_to_box':clean_frame_to_box,'id':prediction['id'],'label':prediction['label'],'trash_type_id':trash_type_id}    
    return timed_prediction

def get_df_prediction(json_prediction:dict,media_fps)->pd.DataFrame:
    """Get AI prediction dictionnary as Dataframe

    Arguments:
        json_prediction {dict} -- a full prediction of AI service as JSON dico
        media_fps {float} -- the FPS of the media where the trash comes from

    Returns:
       df_prediction -- the AI prediction as a Dataframe
    """
    timed_prediction_list = []
    for prediction in json_prediction['detected_trash']:
        timed_prediction_list.append(get_clean_timed_prediction(prediction,media_fps))
    df_prediction = pd.DataFrame(timed_prediction_list)

    return df_prediction


def get_df_manual_trash(gpx_data_waypoints:list)->pd.DataFrame:
    """ Get trash DataFrame from a gpx file where Trash have been manually collected

    Arguments:
        gpx_data_waypoints {list} -- the waypoints list from an OSM track gpx_data parsing

    Returns:
       df_manual_trash -- the manually collected trash as a DataFrame
    """
    trash_list = []
    i = 0
    for waypoint in gpx_data_waypoints:
        trash_type_id = map_label_to_trash_id_PG(waypoint.name.lower())
        trash = {'id':i,'label':waypoint.name,'trash_type_id':trash_type_id}
        trash_list.append(trash)
        i = i+1
    df_manual_trash = pd.DataFrame(trash_list)
    return df_manual_trash


def get_df_json_manual_trash(json_data:dict)->pd.DataFrame:
    """Get trash DataFrame from a JSON file where Trash have been manually collected


    Args:
        json_data (dict): the json data from the Plastic Origin Mobile app

    Returns:
        pd.DataFrame: the gps info as a DataFrame associated with manually collected trash
    """
    trash_list = []
    i = 0
    for trash in json_data['trashes']:
        trash_type_id = map_json_label_to_trash_id_PG(trash['name'])
        trash = {'id':i,'label':trash['name'],'trash_type_id':trash_type_id}
        trash_list.append(trash)
        i = i+1
    df_manual_trash = pd.DataFrame(trash_list)
    return df_manual_trash


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
    id_PG =  switcher.get(label, "0")
    return id_PG


def map_json_label_to_trash_id_PG(label:str)->str:
    """Map label of a trash to equivalent ID within PostGre server

    Arguments:
        label {str} -- the label of the trash

    Returns:
        id_PG -- the equivalent id within PG Trash table of trash label
    """
    switcher = { 
        "unknown":"11", 
        "agriculturalFoodWaste":"12",
        "bottles":"13", 
        "industrials":"14",
        "fishHunting":"15",
        "foodPackage":"16",
        "householdItems":"17",
        "unknown10":"18"
    }
    id_PG =  switcher.get(label, "0")
    return id_PG