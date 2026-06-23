import ddddocr

class OCR:
    def __init__(self):
        self.reader = ddddocr.DdddOcr(show_ad=False)

    def recognise_text(self, image, save=False):
        with open(image, "rb") as f:
            img_bytes = f.read()
        result = self.reader.classification(img_bytes)
        print("Detected text:", result)
        return result
