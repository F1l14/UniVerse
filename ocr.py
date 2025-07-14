import cv2
import numpy as np
import easyocr
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image, ImageEnhance
from paddleocr import PaddleOCR

# def rgb_to_hue(rgb_color):
#     """Convert RGB to OpenCV HSV hue value."""
#     # OpenCV uses BGR order
#     bgr_color = np.uint8([[rgb_color[::-1]]])  # reverse RGB to BGR
#     hsv_color = cv2.cvtColor(bgr_color, cv2.COLOR_BGR2HSV)
#     return int(hsv_color[0][0][0])

# def create_mask(hsv_img, hue, tol=10):
#     """Create mask for pixels within hue ± tol."""
#     lower = np.array([max(hue - tol, 0), 100, 100])
#     upper = np.array([min(hue + tol, 179), 255, 255])
#     return cv2.inRange(hsv_img, lower, upper)

# # Load image
# img = cv2.imread("captcha.png")
# if img is None:
#     print("Error: Image not found")
#     exit()

# hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# # Replace these with your actual RGB letter colors
# letter_colors_rgb = [
#     (255, 0, 0),   # Red
#     (0, 0, 255),   # Blue
#     (0, 255, 0)    # Green
# ]

# # Convert RGB colors to hue values
# hues = [rgb_to_hue(c) for c in letter_colors_rgb]

# # Create masks for each hue
# masks = [create_mask(hsv, hue) for hue in hues]

# # Combine masks for all letters
# combined_mask = masks[0]
# for mask in masks[1:]:
#     combined_mask = cv2.bitwise_or(combined_mask, mask)

# # Morphological opening to clean noise
# kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
# clean_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel, iterations=1)

# # Extract letters from original image using the mask
# letters_only = cv2.bitwise_and(img, img, mask=clean_mask)

# # Save the result
# result = cv2.cvtColor(letters_only, cv2.COLOR_BGR2GRAY)
# result = cv2.threshold(result, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
# result = cv2.morphologyEx(result, cv2.MORPH_CLOSE, kernel, iterations=1)
# result = cv2.morphologyEx(result, cv2.MORPH_OPEN, kernel, iterations=1)

# result = 255 - result

class OCR:
    def __init__(self):
         # Initialize the OCR model
        self.ocr = PaddleOCR(use_doc_orientation_classify=False,   use_doc_unwarping=False)  # use_angle_cls helps with rotated text

    def recognise_text(self, image, save=False):
        # Read the image
        img = image

        # Run OCR
        results = self.ocr.predict(img)

        if save:
            for result in results:
                result.save_to_img("./output")
                print("Detected text:", result.get('rec_texts', []))

        return results[0].get('rec_texts', [])[0]

    def preprocess(self, path):
        # Load the image
        img = Image.open(path)
       
        pixels = img.load()
        # Define what "green" means (tune the range if needed)
        def is_green(rgb):
            r, g, b = rgb
            return g > 100 and r < 100 and b < 100  # adjust thresholds

        # Loop through and replace green pixels
        for y in range(img.height):
            for x in range(img.width):
                if is_green(pixels[x, y]):
                    pixels[x, y] = (0, 0, 0)  # Replace with black
            

        img = img.convert("L")  # Convert to grayscale
        # Adjust contrast
        contrast_enhancer = ImageEnhance.Contrast(img)
        img = contrast_enhancer.enhance(1.7)  # >1 more contrast

        # Adjust sharpness
        sharpness_enhancer = ImageEnhance.Sharpness(img)
        img = sharpness_enhancer.enhance(10)  # >1 sharper

        exposure_enhancer = ImageEnhance.Brightness(img)
        img = exposure_enhancer.enhance(1.2)

        # Show and/or save result
        # img.show()
        img.save("output/processed.png")

