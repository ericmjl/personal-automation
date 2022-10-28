"""Personal automation CLI."""
from pathlib import Path
from personal_automation import audio, movie
from pydub import AudioSegment
from loguru import logger

import typer


app = typer.Typer()


@app.command()
def hello():
    print("Hello home automation!")


@app.command()
def stitch_audio(
    output_path: Path = Path("stitched.wav"),
    glob_pattern="*.WAV",
    directory: Path = Path("."),
):
    """Stitch audio files together.

    :param output_path: File path to output file.
    :param glob_pattern: Pattern of files to look for.
    :param directory: Where to search for WAV files.
    :raises ValueError: if we cannot find any files matching the glob pattern.
    """
    audio_files = sorted(directory.glob(glob_pattern))
    if len(audio_files) == 0:
        raise ValueError(
            "No audio files matching the glob pattern "
            f"{glob_pattern} was found! "
            "These are the files that are present: "
            f"{sorted(f for f in Path(directory).iterdir() if f.is_file())}"
        )
    logger.info(f"Stitching together the following audio files: {audio_files}")
    stitched_audio: AudioSegment = audio.stitch(audio_files)
    stitched_audio.export(output_path)


@app.command()
def stitch_video(
    output_path: Path = Path("stitched.mov"),
    glob_pattern="*.MOV",
    directory: Path = Path("."),
):
    """Stitch video files together.

    :param output_path: File path to output file.
    :param glob_pattern: Pattern of files to look for.
    :param directory: Where to search for WAV files.
    :raises ValueError: if we cannot find any files matching the glob pattern.
    """
    video_files = sorted(directory.glob(glob_pattern))
    if len(video_files) == 0:
        raise ValueError(
            "No video files matching the glob pattern "
            f"{glob_pattern} was found! "
            "These are the files that are present: "
            f"{sorted(f for f in Path(directory).iterdir() if f.is_file())}"
        )
    logger.info(f"Stitching together the following video files: {video_files}")
    stitched_video = movie.stitch(video_files)
    stitched_video.write_videofile(output_path)


if __name__ == "__main__":
    app()
