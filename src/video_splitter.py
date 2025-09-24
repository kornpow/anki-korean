#!/usr/bin/env python3
"""
Video Frame Extractor

Extracts frames from video files that can be processed by box_cropper.py.
Supports various video formats and provides options for frame sampling.

Requirements:
    pip install opencv-python ffmpeg-python

Usage:
    python video_splitter.py input_video.mp4 [options]

Options:
    --output-dir: Directory to save extracted frames (default: frames/)
    --interval: Extract every Nth frame (default: 30, i.e., ~1fps for 30fps video)
    --start-time: Start extraction from this time in seconds (default: 0)
    --end-time: End extraction at this time in seconds (default: video end)
    --quality: JPEG quality for output frames (default: 95)
    --format: Output format - 'jpg' or 'png' (default: 'png')
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

import cv2


class VideoFrameExtractor:
    """Extract frames from video files for further processing"""

    def __init__(self, video_path: str, output_dir: str = "frames"):
        """
        Initialize the video frame extractor

        Args:
            video_path: Path to the input video file
            output_dir: Directory to save extracted frames
        """
        self.video_path = Path(video_path)
        self.output_dir = Path(output_dir)

        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize video capture
        self.cap = cv2.VideoCapture(str(self.video_path))
        if not self.cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        # Get video properties
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.total_frames / self.fps if self.fps > 0 else 0

        print("Video properties:")
        print(f"  FPS: {self.fps:.2f}")
        print(f"  Total frames: {self.total_frames}")
        print(f"  Duration: {self.duration:.2f} seconds")

    def extract_frames(
        self,
        interval: int = 30,
        start_time: float = 0,
        end_time: Optional[float] = None,
        quality: int = 95,
        output_format: str = "png",
    ) -> list[str]:
        """
        Extract frames from the video

        Args:
            interval: Extract every Nth frame (default: 30)
            start_time: Start extraction from this time in seconds
            end_time: End extraction at this time in seconds (None for video end)
            quality: JPEG quality for output frames (1-100, only for jpg format)
            output_format: Output format - 'jpg' or 'png'

        Returns:
            List of paths to extracted frame files
        """
        if end_time is None:
            end_time = self.duration

        # Convert times to frame numbers
        start_frame = int(start_time * self.fps)
        end_frame = int(end_time * self.fps)
        end_frame = min(end_frame, self.total_frames)

        print(f"Extracting frames {start_frame} to {end_frame} (every {interval} frames)")

        extracted_files = []
        frame_count = 0
        extracted_count = 0

        # Set starting position
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        while True:
            ret, frame = self.cap.read()
            if not ret or frame_count + start_frame > end_frame:
                break

            # Extract frame at specified interval
            if frame_count % interval == 0:
                timestamp = (frame_count + start_frame) / self.fps

                # Generate filename with timestamp
                if output_format.lower() == "jpg":
                    filename = f"frame_{extracted_count:06d}_t{timestamp:.2f}s.jpg"
                else:
                    filename = f"frame_{extracted_count:06d}_t{timestamp:.2f}s.png"

                filepath = self.output_dir / filename

                # Save frame
                if output_format.lower() == "jpg":
                    cv2.imwrite(str(filepath), frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
                else:
                    cv2.imwrite(str(filepath), frame)

                extracted_files.append(str(filepath))
                extracted_count += 1

                if extracted_count % 10 == 0:
                    print(f"Extracted {extracted_count} frames...")

            frame_count += 1

        print(f"Successfully extracted {extracted_count} frames to {self.output_dir}")
        return extracted_files

    def extract_single_frame(self, timestamp: float, output_path: Optional[str] = None) -> str:
        """
        Extract a single frame at a specific timestamp

        Args:
            timestamp: Time in seconds to extract frame from
            output_path: Optional custom output path

        Returns:
            Path to the extracted frame file
        """
        frame_number = int(timestamp * self.fps)
        frame_number = min(frame_number, self.total_frames - 1)

        # Set position to specific frame
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()

        if not ret:
            raise ValueError(f"Could not extract frame at timestamp {timestamp}s")

        if output_path is None:
            output_path = self.output_dir / f"frame_t{timestamp:.2f}s.png"

        cv2.imwrite(str(output_path), frame)
        print(f"Extracted frame at {timestamp}s to {output_path}")

        return str(output_path)

    def get_frame_info(self) -> dict:
        """Get information about the video for frame extraction planning"""
        return {
            "fps": self.fps,
            "total_frames": self.total_frames,
            "duration": self.duration,
            "video_path": str(self.video_path),
            "output_dir": str(self.output_dir),
        }

    def __del__(self):
        """Clean up video capture resources"""
        if hasattr(self, "cap") and self.cap.isOpened():
            self.cap.release()


def process_frames_with_box_cropper(frame_files: list[str]) -> None:
    """
    Process extracted frames with the box cropper

    Args:
        frame_files: List of frame file paths to process
    """
    try:
        from .box_cropper import detect_and_crop_boxes

        print(f"\nProcessing {len(frame_files)} frames with box cropper...")
        for i, frame_file in enumerate(frame_files):
            print(f"Processing frame {i + 1}/{len(frame_files)}: {frame_file}")
            detect_and_crop_boxes(frame_file)

    except ImportError:
        print("box_cropper module not found. Please ensure box_cropper.py is available.")
        print("You can manually process frames with:")
        for frame_file in frame_files:
            print(f"  python box_cropper.py {frame_file}")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Extract frames from video files for processing with box_cropper.py"
    )
    parser.add_argument("video_path", help="Path to input video file")
    parser.add_argument(
        "--output-dir",
        default="frames",
        help="Directory to save extracted frames (default: frames/)",
    )
    parser.add_argument(
        "--interval", type=int, default=30, help="Extract every Nth frame (default: 30)"
    )
    parser.add_argument(
        "--start-time",
        type=float,
        default=0,
        help="Start extraction from this time in seconds (default: 0)",
    )
    parser.add_argument(
        "--end-time", type=float, help="End extraction at this time in seconds (default: video end)"
    )
    parser.add_argument(
        "--quality", type=int, default=95, help="JPEG quality for output frames (default: 95)"
    )
    parser.add_argument(
        "--format", choices=["jpg", "png"], default="png", help="Output format (default: png)"
    )
    parser.add_argument(
        "--timestamp", type=float, help="Extract single frame at specific timestamp (seconds)"
    )
    parser.add_argument(
        "--process-with-cropper",
        action="store_true",
        help="Automatically process extracted frames with box_cropper.py",
    )

    args = parser.parse_args()

    try:
        # Initialize extractor
        extractor = VideoFrameExtractor(args.video_path, args.output_dir)

        # Print video info
        info = extractor.get_frame_info()
        print(f"Video: {info['video_path']}")
        print(f"Output directory: {info['output_dir']}")

        # Extract frames
        if args.timestamp is not None:
            # Extract single frame
            frame_file = extractor.extract_single_frame(args.timestamp)
            frame_files = [frame_file]
        else:
            # Extract multiple frames
            frame_files = extractor.extract_frames(
                interval=args.interval,
                start_time=args.start_time,
                end_time=args.end_time,
                quality=args.quality,
                output_format=args.format,
            )

        # Optionally process with box cropper
        if args.process_with_cropper and frame_files:
            process_frames_with_box_cropper(frame_files)

        print("\nExtracted frames are ready for processing with box_cropper.py:")
        print(
            f"Example: python box_cropper.py {frame_files[0] if frame_files else 'frame_file.png'}"
        )

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
