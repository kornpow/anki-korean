#!/usr/bin/env python3
"""
Simple Box Detection and Cropping Script

Detects boxes in an image and saves each as a separate PNG file.

Requirements:
    pip install opencv-python

Usage:
    python box_detector.py input_image.png
"""

import os
import sys
from glob import glob
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
from PIL import Image


def detect_and_crop_boxes(image_path: str) -> Optional[List[str]]:
    """
    Detect boxes and crop each one to separate files

    Args:
        image_path: Path to the input image file

    Returns:
        List of paths to cropped box files, or None if image couldn't be loaded
    """

    # Read image
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not load {image_path}")
        return None

    # Convert to grayscale and find edges
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours to find boxes
    boxes: List[Tuple[int, int, int, int]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area: int = w * h

        # Filter by size (adjust these values if needed)
        if area > 5000 and w > 100 and h > 30:
            boxes.append((x, y, w, h))

    # Sort boxes top to bottom
    boxes.sort(key=lambda box: box[1])

    print(f"Found {len(boxes)} boxes")

    # Create output directory
    os.makedirs("cropped_boxes", exist_ok=True)

    # Extract base filename without extension for output naming
    input_path = Path(image_path)
    base_name: str = input_path.stem  # filename without extension

    # Crop each box and collect filenames
    cropped_files: List[str] = []
    for i, (x, y, w, h) in enumerate(boxes):
        cropped = img[y : y + h, x : x + w]
        filename: str = f"cropped_boxes/{base_name}_box_{i + 1:02d}.png"
        cv2.imwrite(filename, cropped)
        cropped_files.append(filename)
        print(f"Saved {filename}")

    return cropped_files


def box_info() -> None:
    """Print information about all cropped box files"""
    boxes: List[str] = glob("cropped_boxes/*")
    for box in boxes:
        img: Image.Image = Image.open(box)
        print(f"Box: {box} --> shape: {img.size}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python box_detector.py input_image.png")
        sys.exit(1)

    detect_and_crop_boxes(sys.argv[1])
