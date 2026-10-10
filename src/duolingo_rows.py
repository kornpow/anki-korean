"""CPU Korean OCR for Duolingo's light-background, bordered vocabulary list.

Layout-specific: incomplete cells and unsupported screens are skipped rather than
interpreting navigation controls as vocabulary. The original frame remains evidence.
"""

from pathlib import Path

import cv2
import numpy as np


def runs(indices, gap=1):
    groups = []
    for index in indices:
        if not groups or index > groups[-1][-1] + gap:
            groups.append([])
        groups[-1].append(int(index))
    return [(group[0], group[-1] + 1) for group in groups]


def row_regions(image):
    """Return complete cells with two text lines, in original image coordinates."""
    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    neutral = image.max(2) - image.min(2) < 10
    rules = (gray > 180) & (gray < 240) & neutral
    rules = rules[:, round(width * 0.25) : round(width * 0.9)].mean(1) > 0.9
    borders = runs(np.flatnonzero(rules))
    cells = [
        (bottom, top)
        for (_, bottom), (top, _) in zip(borders, borders[1:])
        if 0.045 * height < top - bottom < 0.14 * height
    ]
    if len(cells) < 3:
        return []
    usual_height = float(np.median([bottom - top for top, bottom in cells]))
    padding = max(2, round(height * 0.003))
    x0, x1 = round(width * 0.175), round(width * 0.94)
    output = []
    for y0, y1 in cells:
        if y1 - y0 < 0.88 * usual_height:
            continue
        ink = gray[y0 + padding : y1 - padding, x0:x1] < 210
        lines = runs(
            np.flatnonzero(ink.sum(1) > max(1, width * 0.0015)), gap=max(2, round(height * 0.0023))
        )
        lines = [(a, b) for a, b in lines if b - a > height * 0.003]
        if len(lines) != 2:
            continue
        boxes = []
        for a, b in lines:
            # Text touching a cell edge may be occluded by the fixed header/footer.
            if a < padding or len(ink) - b < padding:
                break
            a, b = max(0, a - padding), min(len(ink), b + padding)
            columns = np.flatnonzero(ink[a:b].any(0))
            if not len(columns):
                break
            boxes.append(
                (int(x0 + columns[0]), y0 + padding + a, int(columns[-1] - columns[0] + 1), b - a)
            )
        if len(boxes) == 2:
            output.append({"cell": (x0, y0, x1 - x0, y1 - y0), "lines": boxes})
    return output


class KoreanOCR:
    def __init__(self):
        from rapidocr import EngineType, ModelType, OCRVersion, RapidOCR

        cv2.setNumThreads(1)
        self.engine = RapidOCR(
            params={
                "Global.use_det": False,
                "Global.use_cls": False,
                "Global.text_score": 0.0,
                "Global.model_root_dir": str(Path.home() / ".cache/anki-korean/ocr"),
                "Rec.engine_type": EngineType.ONNXRUNTIME,
                "Rec.lang_type": "korean",
                "Rec.ocr_version": OCRVersion.PPOCRV5,
                "Rec.model_type": ModelType.MOBILE,
                "EngineConfig.onnxruntime.use_cuda": False,
                "EngineConfig.onnxruntime.intra_op_num_threads": 2,
                "EngineConfig.onnxruntime.inter_op_num_threads": 1,
            }
        )

    def lines(self, image):
        """Return positioned text and raw scores; no inferred translations or corrections."""
        rows = row_regions(image)
        output = []
        for block, row in enumerate(rows, start=1):
            for x, y, width, height in row["lines"]:
                crop = image[y : y + height, x : x + width]
                crop = cv2.copyMakeBorder(
                    crop, 8, 8, 8, 8, cv2.BORDER_CONSTANT, value=(255, 255, 255)
                )
                result = self.engine(crop)
                output.append(
                    {
                        "text": result.txts[0] if result.txts else "",
                        "confidence": float(result.scores[0]) * 100 if result.txts else 0,
                        "left": x,
                        "top": y,
                        "width": width,
                        "height": height,
                        "block": block,
                    }
                )
        return output, rows
