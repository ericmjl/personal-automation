"""High-level functions to do stuff with audio."""

from functools import reduce

from pathlib import Path
from typing import List
from pydub import AudioSegment
from tqdm.auto import tqdm


def stitch(fpaths: List[Path]) -> AudioSegment:
    """Stitch together a collection of WAV files."""
    audio_segments = []
    for fpath in tqdm(fpaths, desc="Stitching audio files"):
        segment = AudioSegment.from_wav(fpath)
        audio_segments.append(segment)
    stitched_audio: AudioSegment = reduce(lambda x, y: x + y, audio_segments)
    return stitched_audio
