import pytesseract
from pancard.identify_pancard import IdentifyPanCard
from aadhaarcard.identify_aadhaarcard import IdentifyAadhaarCard
from passport.identify_passport_doc import IdentifyPassPort
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

        # Aadhaarcard identification object
        self.aadhaarcard_obj = IdentifyAadhaarCard(clean_text)

        # Passport identification object
        self.passport_obj = IdentifyPassPort(clean_text)

    
    def identify_pancard(self) -> bool:
        if self.pancard_obj.check_pan_card():
            return True
        return False

    def identify_aadhaarcard(self):
        if self.aadhaarcard_obj.check_aadhaar_card():
            return True
        return False
    
    def identify_eaadhaarcard(self):
        if self.aadhaarcard_obj.check_e_aadhaar_card():
            return True
        return False
    
    def identify_aadhaarcard_front(self):
        if self.aadhaarcard_obj.check_aadhaar_front():
            return True
        return False
    
    def identify_passport(self):
        if self.passport_obj.check_passport():
            return True
        return False