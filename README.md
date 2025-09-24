# anki-korean

Create Korean flash cards from video content.

## Usage

```bash
# 1. Extract frames from video
python src/video_splitter.py sources/duo-video.mp4

# 2. Crop text boxes from frames
python src/box_cropper.py frames/frame_000001_t0.00s.png
```

Install dependencies: `uv sync`
