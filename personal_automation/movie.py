"""High-level functions to do stuff with movies."""
from moviepy.editor import concatenate_videoclips, VideoFileClip, VideoClip
from typing import List
from pathlib import Path


def stitch(fpaths: List[Path]) -> VideoClip:
    """Stitch together video clips.

    :param fpaths: List of file paths to video files to stitch.
    :returns: A concatenated VideoClip object.
    """
    clips = []
    for fpath in fpaths:
        clip = VideoFileClip(str(fpath))
        clips.append(clip)
    final: VideoClip = concatenate_videoclips(clips)
    return final
