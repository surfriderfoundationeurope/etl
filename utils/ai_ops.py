import json
import logging

logger = logging.getLogger()
import requests


class AIError(Exception):
    """Base exception for all AI-related exceptions"""
    pass


def ai_ready(url: str) -> bool:
    """ Evaluate whether AI inference service is available

    Parameters
    ----------
    url: address of to AI API

    Returns
    -------
    ready: AI Status: True if AI is ready, else False
    """

    try:
        ai_request = requests.get(url)
        logger.info("AI request reason: ", ai_request.reason)
        return ai_request.ok  # True if AI is ready, False if not.
    except requests.exceptions.RequestException:
        logger.warning("AI not found, an error has occured")  # Probably wrong url or AI server is down.
        return False


def get_predicted_trashs(media_path: str, ai_url: str) -> list:
    """ Post a media to AI and waits for its response

    Parameters
    ----------
    media_path: Path to video or image in a local storage
    url: AI API address

    Returns
    -------
    List of trashs detected by AI
    """

    files = {
        "file": (
            media_path,
            open(media_path, "rb"),
            "application/octet-stream",
        )
    }
    response = requests.post(ai_url, files=files)
    if not response.ok:
        logger.error(f"Request to AI failed wih reason {response.reason}.")
    json_response = response._content
    try:
        prediction = json.loads(json_response)
    except json.decoder.JSONDecodeError:
        raise AIError('Could not deserialize AI response')
    detected_trashs = prediction.get('detected_trash')
    return detected_trashs


def mapLabel2TrashIdPG(label):
    """
    TODO: I'm not sure this should be here
    mapLabel2TrashIdPG function is a different mapping between a predicted label by AI and TrashId as defined within TrashType table
    Input: a label predicted by AI
    Output: a TrashId as defined in TrashType table
    """
    switcher = {
        "others": "1",  # "autre dechet" in PG Data Model mapped to IA "others" label
        "dechet agricole": "2",
        "bottles": "3",  # "bouteille boisson" in PG Data Model mapped to IA "bottles" label
        "fragments": "4",  # "industriel ou construction in PG Data Model mapped to IA "fragments" label
        "peche et chasse": "5",
        "emballage alimentaire": "6",
        "objet vie courante": "7",
        "autres dechets +10": "8"
    }
    return switcher.get(label, "nothing")
