import sys
from ocr import OCR
 
image_path = "./output/cap.png"
 
ocr = OCR()
 
print(f"\n--- Testing with: {image_path} ---")
 
# print("\n[1] Raw (no preprocessing):")
# result = ocr.recognise_text(image_path)
# print(f"    → '{result}'")
 
print("\n[2] Preprocessed:")
# ocr.preprocess(image_path)
result = ocr.recognise_text("output/processed.png", save=True)
print(f"    → '{result}'")
 