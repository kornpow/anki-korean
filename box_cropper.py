#!/usr/bin/env python3
"""
Simple Box Detection and Cropping Script

Detects boxes in an image and saves each as a separate PNG file.

Requirements:
    pip install opencv-python

Usage:
    python box_detector.py input_image.png
"""

import cv2
import os
import sys


def detect_and_crop_boxes(image_path):
    """Detect boxes and crop each one to separate files"""
    
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not load {image_path}")
        return
    
    # Convert to grayscale and find edges
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter contours to find boxes
    boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        
        # Filter by size (adjust these values if needed)
        if area > 5000 and w > 100 and h > 30:
            boxes.append((x, y, w, h))
    
    # Sort boxes top to bottom
    boxes.sort(key=lambda box: box[1])
    
    print(f"Found {len(boxes)} boxes")
    
    # Create output directory
    os.makedirs("cropped_boxes", exist_ok=True)
    
    # Crop each box
    for i, (x, y, w, h) in enumerate(boxes):
        cropped = img[y:y+h, x:x+w]
        filename = f"cropped_boxes/box_{i+1}.png"
        cv2.imwrite(filename, cropped)
        print(f"Saved {filename}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python box_detector.py input_image.png")
        sys.exit(1)
    
    detect_and_crop_boxes(sys.argv[1])