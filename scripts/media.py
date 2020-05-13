from moviepy.editor import VideoFileClip


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