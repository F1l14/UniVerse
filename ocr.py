import numpy as np
from PIL import Image, ImageEnhance
from paddleocr import PaddleOCR
import os
class OCR:
    def __init__(self):
         # Initialize the OCR model
        # Base model folders
        home = os.path.expanduser("~")
        base_model_path = os.path.join(home, ".paddlex", "official_models")
        print("Base model path:", base_model_path)
       
        # force use the cached models if they exist
        def get_subdir_by_partial_name(parent_path, partial_name):
            if not os.path.isdir(parent_path):
                return None
            for entry in os.listdir(parent_path):
                full_path = os.path.join(parent_path, entry)
                if os.path.isdir(full_path) and partial_name in entry:
                    return full_path
            return None

        det_dir = get_subdir_by_partial_name(base_model_path, "det")   # matches 'PP-OCRv5_server_det'
        rec_dir = get_subdir_by_partial_name(base_model_path, "rec")   # matches 'PP-OCRv5_server_rec'
        cls_dir = get_subdir_by_partial_name(base_model_path, "textline")  # matches 'PP-LCNet_x1_0_textline_ori'

        models_exist = all([det_dir, rec_dir, cls_dir])

        if models_exist:
            print("✅ Loading models from local disk...")
            self.ocr = PaddleOCR(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                det_model_dir=det_dir,
                rec_model_dir=rec_dir,
                cls_model_dir=cls_dir
            )
        else:
            print("⬇️  Local models not found — downloading via PaddleOCR...")
            self.ocr = PaddleOCR(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False
            )
        # self.ocr = PaddleOCR(use_doc_orientation_classify=False,   use_doc_unwarping=False)  # use_angle_cls helps with rotated text

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

