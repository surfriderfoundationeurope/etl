from moviepy.editor import VideoFileClip
import numpy as np


def get_media_duration(media_path: str) -> float:
    """ Extract duration from a media file
    Taken from `here <https://www.reddit.com/r/moviepy/comments/2bsnrq/is_it_possible_to_get_the_length_of_a_video/>`_
    Parameters
    ----------
    media_path: Path to media
    Returns
    -------
    duration: duration of the media
    """
    clip = VideoFileClip(media_path)
    return clip.duration

def get_media_fps(json_prediction: dict) -> int:
    """ Get FPS of video media

    Arguments:
        media_path {str} -- path of video media to get FPS from

    Returns:
        fps {int} -- the FPS of the media video
    """
    fps = int(json_prediction['fps'])
    return fps
