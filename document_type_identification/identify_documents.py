import pytesseract
from pancard.identify_pancard import IdentifyPanCard
from helper.clean_text import CleanText

class DocumentTypeIdentification:
    def __init__(self, document_path: str) -> None:
        self.document_path = document_path

        # Tesseract configuration
        tesseract_config = r'-l eng --oem 3 --psm 6'

        # Extract text from document in dictionary format
        data_text = pytesseract.image_to_string(self.document_path, output_type=pytesseract.Output.DICT, config=tesseract_config)

        # Clean the extracted text
        clean_text = CleanText(data_text).clean_text()

        # Pancard identification object
        self.pancard_obj = IdentifyPanCard(clean_text)

    
    def identify_pancard(self) -> bool:
        if self.pancard_obj.check_pan_card():
            return True
        return False