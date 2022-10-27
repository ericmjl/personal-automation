"""Personal automation CLI."""
from pathlib import Path
from .audio import stitch
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
    audio_files = sorted(directory.glob(glob_pattern))
    if len(audio_files) == 0:
        raise ValueError(
            f"No audio files matching the glob pattern {glob_pattern} was found! "
            f"These are the files that are present: {sorted(f for f in Path(directory).iterdir() if f.is_file())}"
        )
    logger.info(f"Stitching together the following audio files: {audio_files}")
    stitched_audio: AudioSegment = stitch(audio_files)
    stitched_audio.export(output_path)


if __name__ == "__main__":
    app()
