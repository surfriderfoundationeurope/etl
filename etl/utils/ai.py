import json
import logging

import numpy as np
import pandas as pd
import requests

logger = logging.getLogger()

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
        logger.warning(
            "AI not found, an error has occured"
        )  # Probably wrong url or AI server is down.
        return False


def get_ai_prediction(media_path: str, ai_url: str) -> (pd.DataFrame, dict):
    """ Post a media to AI and waits for its response and deserialize

    Parameters
    ----------
    media_path: Path to video or image in a local storage
    url: AI API address

    Returns
    -------
    ai_prediction:  response from AI API as a dict with keys
                    'detected__trash', 'fps', 'video_id', 'video_length'
                     todo: check how it is like for images

    Examples:
    ---------
    > ai_prediction
        {'detected_trash': [
                        {'frame_to_box': {'2': [0.43, 0.44, 0.49, 0.5]},
                           'id': 0,
                           'label': 'fragments'},
                        {'frame_to_box': {'3': [0.4, 0.44, 0.46, 0.49]},
                           'id': 1,
                           'label': 'fragments'},
                        ...
                        {'frame_to_box': {'24': [0.49, 0.44, 0.56, 0.46]},
                           'id': 13,
                           'label': 'others'}],
         'fps': 4,
         'video_id': 'vid1-480p.mov',
         'video_length': 25
         }

    """

    files = {"file": (media_path, open(media_path, "rb"), "application/octet-stream",)}
    response = requests.post(ai_url, files=files)
    if not response.ok:
        logger.error(f"Request to AI failed wih reason {response.reason}.")
    json_response = response._content
    try:
        ai_prediction = json.loads(json_response)
    except json.decoder.JSONDecodeError:
        raise AIError("Could not deserialize AI response")
    return ai_prediction


def prediction_to_dataframe(
    ai_prediction: dict, start: pd.Timestamp, duration: float = None
):
    """Convert AI dict prediction to DataFrame with eventually timestamps index (if `start` is given)

    Parameters
    ----------
    ai_prediction: Dict with keys 'fps', 'video-id', 'video_length'
    url: AI API address

    Returns
    -------
    detected_trashes: DataFrame with each row is a detected trash with columns ['frame', 'box', 'id', 'label']
                      and index are inferred timestamp

    Examples:
    ---------
    > detected_trashes
                                           id      label                      box  frame
            2018-01-01 00:00:01.435708800   0  fragments  [0.43, 0.44, 0.49, 0.5]      2
            2018-01-01 00:00:01.435708801   1  fragments  [0.4, 0.44, 0.46, 0.49]      3
            2018-01-01 00:00:01.435708801   2     others  [0.32, 0.45, 0.38, 0.46      4
            2018-01-01 00:00:01.435708801   3    bottles  [0.32, 0.45, 0.38, 0.46      4
            2018-01-01 00:00:01.435708803   4  fragments  [0.25, 0.43, 0.29, 0.49      9
            2018-01-01 00:00:01.435708804   5  fragments  [0.22, 0.41, 0.26, 0.48     10
            2018-01-01 00:00:01.435708804   6  fragments  [0.2, 0.43, 0.23, 0.48]     11
            2018-01-01 00:00:01.435708805   7  fragments  [0.18, 0.42, 0.21, 0.48     12
                            ...                ...                 ...

    """
    # convert list of dict to DataFrame
    detected_trashes = pd.DataFrame(ai_prediction.get("detected_trash"))
    # interpret 'frame_to_box' as frame and box separately,
    # eg:  {'2': [0.43, 0.44, 0.49, 0.5]} means 'on frame 2,
    # there's a trash in box with coordinates [0.43, 0.44, 0.49, 0.5]
    detected_trashes.loc[:, "box"] = np.apply_along_axis(
        lambda frame_to_box: str(list(frame_to_box[0].values())[0]),
        axis=1,
        arr=detected_trashes[["frame_to_box"]].values,
    )
    detected_trashes.loc[:, "frame"] = np.apply_along_axis(
        lambda frame_to_box: int(list(frame_to_box[0].keys())[0]),
        axis=1,
        arr=detected_trashes[["frame_to_box"]].values,
    )
    detected_trashes.drop("frame_to_box", axis=1, inplace=True)

    if start is not None:
        infer_trashes_timestamps(
            detected_trashes,
            start=start,
            fps=ai_prediction["fps"],
            num_frames=ai_prediction["video_length"],
            duration=duration,
        )
    return detected_trashes


def infer_trashes_timestamps(
    detected_trashes: pd.DataFrame,
    start: pd.Timestamp,
    fps: int,
    num_frames: int = None,
    duration: float = None,
):
    """ Retrieve trashes timestamps given start reference, fps and frame index of the trash

    Parameters
    ----------
    detected_trashes: DataFrame with 'frame' in columns
    start: Timestamp corresponding to beginning of media
    fps: number of frame per second (given by AI)
    num_frames: number of frames (given by AI)
    duration: video duration (if None, this is inferred from fps and num_frames)

    Examples:
    ---------
    > detected_trashes
            id      label                      box  frame
        0    0  fragments  [0.43, 0.44, 0.49, 0.5]      2
        1    1  fragments  [0.4, 0.44, 0.46, 0.49]      3
        2    2     others  [0.32, 0.45, 0.38, 0.46      4
        3    3    bottles  [0.32, 0.45, 0.38, 0.46      4
                    ...             ...

    > infer_trashes_timestamps(detected_trashes_input, start=pd.Timestamp('2018-01-01 10:10:23'), fps: 4, num_frames: 25)
    > detected_trashes
                                       id      label                      box  frame
        1970-01-01 00:00:01.514801423   0  fragments  [0.43, 0.44, 0.49, 0.5]      2
        1970-01-01 00:00:01.514801424   1  fragments  [0.4, 0.44, 0.46, 0.49]      3
        1970-01-01 00:00:01.514801424   2     others  [0.32, 0.45, 0.38, 0.46      4
        1970-01-01 00:00:01.514801424   3    bottles  [0.32, 0.45, 0.38, 0.46      4
                              ...             ...           ...

    """
    start = start or pd.Timedelta(0)
    num_frames = num_frames or round(duration * fps)
    duration = duration or num_frames / fps
    # todo: if duration (that is given by GPS data), need to check it's not lower than video duration
    #       (question) if it is the case: what do we do ?

    stop = start + duration * np.timedelta64(1, "s")
    index = pd.to_datetime(np.linspace(start.value, stop.value, num=num_frames))
    timestamps = np.apply_along_axis(
        lambda frame: index[frame], axis=0, arr=detected_trashes["frame"].values
    )
    detected_trashes.index = timestamps
