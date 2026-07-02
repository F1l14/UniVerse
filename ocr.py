import re

import ddddocr
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

class OCR:
    def __init__(self):
        self.reader = ddddocr.DdddOcr(show_ad=False, beta=True)
        self.legacy_reader = ddddocr.DdddOcr(show_ad=False)
        self.allowed_charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

        for reader in (self.reader, self.legacy_reader):
            try:
                reader.set_charset_range(self.allowed_charset)
            except Exception:
                pass

    def _normalize_text(self, text):
        return re.sub(r"\s+", "", text or "").upper()

    def _load_variants(self, image_path):
        with Image.open(image_path) as source:
            image = source.convert("RGB")

            large_size = (image.width * 2, image.height * 2)
            grayscale = ImageOps.grayscale(image)
            grayscale = ImageOps.autocontrast(grayscale)
            grayscale = grayscale.filter(ImageFilter.MedianFilter(size=3))
            sharpened = ImageEnhance.Sharpness(grayscale).enhance(2.0)
            high_contrast = ImageEnhance.Contrast(grayscale).enhance(2.5)
            threshold = high_contrast.point(lambda pixel: 255 if pixel > 150 else 0)

            return [
                ("original", image),
                ("grayscale", grayscale),
                ("sharpened", sharpened),
                ("high_contrast", high_contrast),
                ("threshold", threshold),
                ("threshold_x2", threshold.resize(large_size, Image.Resampling.LANCZOS)),
                ("grayscale_x2", grayscale.resize(large_size, Image.Resampling.LANCZOS)),
            ]

    def _score_candidate(self, text, confidence):
        cleaned = self._normalize_text(text)
        score = float(confidence or 0.0)

        if cleaned.isalpha():
            score += 0.15

        if 4 <= len(cleaned) <= 6:
            score += 0.15

        if cleaned and all(char in self.allowed_charset for char in cleaned):
            score += 0.2

        return cleaned, score

    def _extract_prediction(self, prediction):
        if isinstance(prediction, dict):
            return prediction.get("text", ""), prediction.get("confidence", 0.0)

        return prediction, 0.0

    def _collect_candidates(self, reader, image_variants, label_prefix):
        candidates = []

        for variant_label, variant in image_variants:
            try:
                prediction = reader.classification(variant, probability=True)
                text, confidence = self._extract_prediction(prediction)
                cleaned, score = self._score_candidate(text, confidence)
                if cleaned:
                    candidates.append((score, cleaned, f"{label_prefix}:{variant_label}", float(confidence or 0.0)))
            except Exception as exc:
                print(f"OCR warning ({label_prefix}:{variant_label}): {exc}")

        return candidates

    def recognise_top_candidates(self, image, max_count=3):
        candidates = []
        image_variants = self._load_variants(image)

        candidates.extend(self._collect_candidates(self.reader, image_variants, "beta"))
        candidates.extend(self._collect_candidates(self.legacy_reader, image_variants, "legacy"))

        try:
            import easyocr

            easy_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
            for variant_label, variant in image_variants[:3]:
                try:
                    results = easy_reader.readtext(
                        variant,
                        detail=1,
                        paragraph=False,
                        allowlist=self.allowed_charset,
                    )
                    for _, text, confidence in results:
                        cleaned, score = self._score_candidate(text, confidence)
                        if cleaned:
                            candidates.append((score, cleaned, f"easyocr:{variant_label}", float(confidence or 0.0)))
                except Exception as exc:
                    print(f"OCR warning (easyocr:{variant_label}): {exc}")
        except Exception:
            pass

        if not candidates:
            with open(image, "rb") as f:
                fallback = self._normalize_text(self.reader.classification(f.read()))
            print("Detected text:", fallback)
            return [fallback] if fallback else []

        candidates.sort(key=lambda item: item[0], reverse=True)
        print("OCR candidates:")
        for score, text, label, confidence in candidates:
            print(f"  - {label}: {text} (score={score:.3f}, confidence={confidence:.3f})")

        # Get unique texts with score >= 0.55
        seen = set()
        top_candidates = []
        for score, text, label, confidence in candidates:
            if text not in seen and score >= 0.55:
                seen.add(text)
                top_candidates.append(text)
                if len(top_candidates) == max_count:
                    break

        print("Top candidates:", top_candidates)
        return top_candidates

    def recognise_text(self, image, save=False):
        candidates = []
        image_variants = self._load_variants(image)

        candidates.extend(self._collect_candidates(self.reader, image_variants, "beta"))
        candidates.extend(self._collect_candidates(self.legacy_reader, image_variants, "legacy"))

        try:
            import easyocr

            easy_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
            for variant_label, variant in image_variants[:3]:
                try:
                    results = easy_reader.readtext(
                        variant,
                        detail=1,
                        paragraph=False,
                        allowlist=self.allowed_charset,
                    )
                    for _, text, confidence in results:
                        cleaned, score = self._score_candidate(text, confidence)
                        if cleaned:
                            candidates.append((score, cleaned, f"easyocr:{variant_label}", float(confidence or 0.0)))
                except Exception as exc:
                    print(f"OCR warning (easyocr:{variant_label}): {exc}")
        except Exception:
            pass

        if not candidates:
            with open(image, "rb") as f:
                fallback = self._normalize_text(self.reader.classification(f.read()))
            print("Detected text:", fallback)
            return fallback

        candidates.sort(key=lambda item: item[0], reverse=True)
        best_score, best_text, best_label, best_confidence = candidates[0]
        print("OCR candidates:")
        for score, text, label, confidence in candidates:
            print(f"  - {label}: {text} (score={score:.3f}, confidence={confidence:.3f})")

        if best_score < 0.55:
            print(f"Low OCR confidence ({best_score:.3f}); retrying is safer than submitting a bad guess.")
            return ""

        print("Detected text:", best_text)
        return best_text
