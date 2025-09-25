#!/usr/bin/env python3
"""
Simple Box Detection and Cropping Script

Detects boxes in an image and saves each as a separate PNG file.

Requirements:
    pip install opencv-python

Usage:
    python box_detector.py input_image.png
"""

import argparse
import os
import sys
from glob import glob
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image


def load_image(image_path: str) -> Optional[np.ndarray]:
    """
    Load an image from file path

    Args:
        image_path: Path to the input image file

    Returns:
        Numpy array representing the image, or None if loading failed
    """
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not load {image_path}")
        return None
    return img


def apply_large_crop(
    img: np.ndarray, crop_region: Tuple[int, int, int, int]
) -> Tuple[np.ndarray, Tuple[int, int]]:
    """
    Apply a large crop to the image

    Args:
        img: Input image as numpy array
        crop_region: (x, y, width, height) for crop region

    Returns:
        Tuple of (cropped_image, (offset_x, offset_y))
    """
    x, y, w, h = crop_region

    # Ensure crop region is within image bounds
    img_height, img_width = img.shape[:2]
    x = max(0, min(x, img_width))
    y = max(0, min(y, img_height))
    w = min(w, img_width - x)
    h = min(h, img_height - y)

    print(f"Applying large crop: x={x}, y={y}, w={w}, h={h}")
    cropped_img = img[y : y + h, x : x + w]

    return cropped_img, (x, y)


def detect_and_crop_boxes_from_image(
    img: np.ndarray, min_area: int = 5000, min_width: int = 809, min_height: int = 175
) -> List[np.ndarray]:
    """
    Detect rectangular boxes in an image and return cropped box images

    Args:
        img: Input image as numpy array
        min_area: Minimum area for detected boxes
        min_width: Minimum width for detected boxes
        min_height: Minimum height for detected boxes

    Returns:
        List of cropped box images as numpy arrays
    """
    # Convert to grayscale and find edges
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter contours and crop boxes
    cropped_boxes: List[np.ndarray] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area: int = w * h

        # Filter by size
        if area > min_area and w > min_width and h > min_height:
            cropped = img[y : y + h, x : x + w]
            cropped_boxes.append(cropped)
            print(f"Found box with size: {w}x{h}")

    print(f"Found {len(cropped_boxes)} boxes")
    return cropped_boxes


def save_images(images: List[np.ndarray], output_dir: str = "cropped_boxes") -> List[str]:
    """
    Save a list of images to files

    Args:
        images: List of images as numpy arrays
        output_dir: Directory to save images

    Returns:
        List of saved file paths
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    saved_files: List[str] = []

    for i, img in enumerate(images):
        filename: str = f"{output_dir}/image_{i + 1:02d}.png"

        cv2.imwrite(filename, img)
        saved_files.append(filename)
        print(f"Saved {filename}")

    return saved_files


def detect_and_crop_boxes(img: np.ndarray) -> List[np.ndarray]:
    """
    Detect boxes in an image and return cropped box images

    Args:
        img: Input image as numpy array

    Returns:
        List of cropped box images as numpy arrays
    """
    return detect_and_crop_boxes_from_image(img)


def process_image_file(
    image_path: str,
    crop_region: Optional[Tuple[int, int, int, int]] = None,
    output_dir: str = "cropped_boxes",
) -> Optional[List[str]]:
    """
    Main function: Load an image, optionally crop it, detect boxes, and save cropped boxes

    Args:
        image_path: Path to the input image file
        crop_region: Optional (x, y, width, height) for initial large crop
        output_dir: Directory to save cropped boxes

    Returns:
        List of paths to saved cropped box files, or None if image couldn't be loaded
    """
    # Load image
    img = load_image(image_path)
    if img is None:
        return None

    # Apply large crop if specified
    if crop_region is not None:
        img, _ = apply_large_crop(img, crop_region)

    # Detect and crop boxes
    cropped_images = detect_and_crop_boxes(img)
    if not cropped_images:
        return []

    # Save cropped boxes with simple names
    input_path = Path(image_path)
    base_name = input_path.stem
    os.makedirs(output_dir, exist_ok=True)

    saved_files: List[str] = []

    filename: str = f"tempframes/{base_name}_bigcrop.png"
    cv2.imwrite(filename, img)

    for i, cropped_img in enumerate(cropped_images):
        filename: str = f"{output_dir}/{base_name}_box_{i + 1:02d}.png"

        cv2.imwrite(filename, cropped_img)
        saved_files.append(filename)
        print(f"Saved {filename}")

    return saved_files


def box_info() -> None:
    """Print information about all cropped box files"""
    boxes: List[str] = glob("cropped_boxes/*")
    for box in boxes:
        img: Image.Image = Image.open(box)
        print(f"Box: {box} --> shape: {img.size}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Detect and crop boxes from images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python box_cropper.py image.png
  python box_cropper.py image.png --crop 100 50 800 600
  python box_cropper.py image.png --crop
        """,
    )

    parser.add_argument("image_path", help="Path to input image file")

    parser.add_argument(
        "--crop",
        nargs=4,
        type=int,
        metavar=("X", "Y", "WIDTH", "HEIGHT"),
        default=[100, 400, 800, 200],
        help="Crop region coordinates (default: 100 400 800 200)",
    )

    parser.add_argument(
        "--output-dir",
        default="cropped_boxes",
        help="Output directory for cropped boxes (default: cropped_boxes)",
    )

    args = parser.parse_args()

    # Determine crop region
    crop_region = None
    if args.crop:
        crop_region = tuple(args.crop)
        print(f"Using crop: {crop_region}")

    # Process the image
    saved_files = process_image_file(args.image_path, crop_region, args.output_dir)

    if saved_files is None:
        print("Failed to load image")
        sys.exit(1)
    elif not saved_files:
        print("No boxes found")
    else:
        print(f"Successfully processed {len(saved_files)} boxes")


if __name__ == "__main__":
    main()
