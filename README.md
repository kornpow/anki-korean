# anki-korean

Create Korean flash cards from video content.

## Usage

```bash
# 1. Extract frames from video
uv run python src/video_splitter.py sources/duo-video.mp4

# 2. Crop text boxes from frames
uv run python src/box_cropper.py frames/frame_000001_t0.00s.png
```

## Advanced Usage
```bash
# Run box cropper on all files
find frames/*.png -type f | xargs -I {} uv run src/box_cropper.py {} --crop 0 450 890 1250
```


Install dependencies: `uv sync`
