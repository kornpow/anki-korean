import os

import imagehash
from PIL import Image


def find_duplicates_advanced(directory, hash_size=8, threshold=5):
    """
    Find duplicate images using multiple hashing algorithms
    threshold: how similar images need to be (0 = identical, higher = more lenient)
    """

    image_hashes = []
    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}

    # Calculate hashes for all images
    for filename in os.listdir(directory):
        if any(filename.lower().endswith(ext) for ext in image_extensions):
            filepath = os.path.join(directory, filename)
            try:
                with Image.open(filepath) as img:
                    # Multiple hash types for better accuracy
                    avg_hash = imagehash.average_hash(img, hash_size=hash_size)
                    p_hash = imagehash.phash(img, hash_size=hash_size)
                    d_hash = imagehash.dhash(img, hash_size=hash_size)

                    image_hashes.append(
                        {"path": filepath, "avg_hash": avg_hash, "p_hash": p_hash, "d_hash": d_hash}
                    )
            except Exception as e:
                print(f"Error processing {filepath}: {e}")

    # Find similar images
    duplicates = []
    for i, img1 in enumerate(image_hashes):
        for j, img2 in enumerate(image_hashes[i + 1 :], i + 1):
            # Check similarity using multiple hash types
            avg_diff = img1["avg_hash"] - img2["avg_hash"]
            p_diff = img1["p_hash"] - img2["p_hash"]
            d_diff = img1["d_hash"] - img2["d_hash"]

            # If any hash type shows similarity within threshold
            if min(avg_diff, p_diff, d_diff) <= threshold:
                duplicates.append((img1["path"], img2["path"], min(avg_diff, p_diff, d_diff)))

    return duplicates


# Usage
directory = "cropped_boxes"
duplicates = find_duplicates_advanced(directory, threshold=5)

for img1, img2, similarity in duplicates:
    print(f"Similar images (difference: {similarity}):")
    print(f"  {img1}")
    print(f"  {img2}")
    print()
