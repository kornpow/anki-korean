# Try to extract English↔Korean word pairs from the uploaded video and export to CSV.
# Steps:
# 1) Sample 1 frame per second
# 2) OCR each sampled frame with pytesseract (if available)
# 3) Parse likely "english - korean" pairs
# 4) Deduplicate and save to /mnt/data/english_korean.csv
# 5) Also save sampled frames for user inspection

import cv2
import os
import re
import pandas as pd

video_path = "/mnt/data/ScreenRecording_06-19-2025 15-52-55_1.mov"
out_frames_dir = "/mnt/data/ek_frames"
csv_path = "/mnt/data/english_korean.csv"

os.makedirs(out_frames_dir, exist_ok=True)

cap = cv2.VideoCapture(video_path)
if not cap.isOpened():
    print("ERROR: Could not open the video. Please confirm the file path.")
else:
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration_sec = total_frames / fps if fps else 0
    sample_every_sec = 1  # 1 fps sampling
    sample_every_frames = int(max(1, round(fps * sample_every_sec)))
    saved = 0
    frame_idx = 0
    while True:
        ret = cap.grab()
        if not ret:
            break
        if frame_idx % sample_every_frames == 0:
            ret2, frame = cap.retrieve()
            if not ret2:
                break
            out_path = os.path.join(out_frames_dir, f"frame_{frame_idx:07d}.png")
            cv2.imwrite(out_path, frame)
            saved += 1
        frame_idx += 1
    cap.release()
    print(f"Sampled frames saved: {saved} (duration ~{duration_sec:.1f}s, fps={fps:.2f})")

# Try OCR with pytesseract
text_by_frame = {}
ocr_ok = True
try:
    import pytesseract
    from PIL import Image
except Exception as e:
    ocr_ok = False
    print("WARNING: OCR libraries not available in this environment. Extracted frames were saved for manual review.")

pairs = []

if ocr_ok:
    frame_files = sorted([os.path.join(out_frames_dir, f) for f in os.listdir(out_frames_dir) if f.endswith(".png")])
    # Basic preprocessing + OCR
    for fpath in frame_files:
        try:
            img = Image.open(fpath)
            # Run OCR (try English and Korean)
            txt = pytesseract.image_to_string(img, lang="eng+kor")
            if txt.strip():
                text_by_frame[os.path.basename(fpath)] = txt
        except Exception as e:
            # Try fallback with just eng
            try:
                txt = pytesseract.image_to_string(img, lang="eng")
                if txt.strip():
                    text_by_frame[os.path.basename(fpath)] = txt
            except Exception as e2:
                continue

    # Heuristics to extract "english - korean" pairs
    # Look for lines with a separator like '-', '–', ':', '=>', or '|'
    sep_pattern = re.compile(r"\s*([-–:|=>]{1,3})\s*")
    korean_chars = re.compile(r"[\uac00-\ud7af\u3130-\u318f]")  # Hangul range
    english_chars = re.compile(r"[A-Za-z]")

    for fname, txt in text_by_frame.items():
        for raw_line in txt.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            # Normalize separators
            parts = sep_pattern.split(line)
            # sep_pattern splits into tokens; reconstruct by manual split candidates as well
            candidates = []
            # Common manual splits
            for sep in [" - ", " – ", ":", " | ", " => ", " -> ", "\t"]:
                if sep in line:
                    left, right = line.split(sep, 1)
                    candidates.append((left.strip(), right.strip()))
            # If no manual split found, try to find english then korean chunks
            if not candidates:
                # Try split by hyphen without spaces
                if "-" in line:
                    left, right = line.split("-", 1)
                    candidates.append((left.strip(), right.strip()))
                elif ":" in line:
                    left, right = line.split(":", 1)
                    candidates.append((left.strip(), right.strip()))

            for left, right in candidates:
                # Decide which side is English and which is Korean
                left_has_eng = bool(english_chars.search(left))
                right_has_eng = bool(english_chars.search(right))
                left_has_kor = bool(korean_chars.search(left))
                right_has_kor = bool(korean_chars.search(right))

                eng = None
                kor = None

                if left_has_eng and right_has_kor:
                    eng, kor = left, right
                elif left_has_kor and right_has_eng:
                    eng, kor = right, left
                else:
                    # If both sides look similar, skip
                    continue

                # Clean common artifacts
                def clean(s: str) -> str:
                    s = re.sub(r"^\W+|\W+$", "", s)
                    s = re.sub(r"\s{2,}", " ", s)
                    return s.strip()

                eng = clean(eng)
                kor = clean(kor)

                if eng and kor:
                    pairs.append((eng, kor))

# Deduplicate while preserving order
unique = []
seen = set()
for eng, kor in pairs:
    key = (eng.lower(), kor)
    if key not in seen:
        seen.add(key)
        unique.append({"english": eng, "korean": kor})

# Save CSV if we have any pairs
if unique:
    df = pd.DataFrame(unique)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"CSV saved: {csv_path} with {len(df)} rows")
else:
    print("No word pairs detected yet. You can review the extracted frames in:", out_frames_dir)

# If there is OCR text, save a raw dump for transparency
if text_by_frame:
    raw_txt_path = "/mnt/data/ocr_raw_dump.txt"
    with open(raw_txt_path, "w", encoding="utf-8") as f:
        for fname, txt in text_by_frame.items():
            f.write(f"===== {fname} =====\n{txt}\n\n")
    print(f"OCR raw text saved: {raw_txt_path}")
