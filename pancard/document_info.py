import pytesseract
import re
import os
from helper.text_coordinates import TextCoordinates
from pancard.pattern1 import PanCardPattern1
from pancard.pattern2 import PanCardPattern2
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging

class PancardDocumentInfo:
    def __init__(self, document_path) -> None:
        # Configure logger
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()

        # # Set document original path
        # document_name_list = os.path.basename(document_path).split('+')
        # original_document_name = document_name_list[2]
        # self.original_document_path = upload_path+"\\"+document_name_list[0]+"\\"+document_name_list[1]+"\\"+original_document_name

        # Get the coordinates of all the extracted text
        self.coordinates = TextCoordinates(document_path).generate_text_coordinates()
        # Get the texts from document
        self.text = pytesseract.image_to_string(document_path)

     # func: extract the pan card number
    def __extract_pan_card_num(self) -> list:
        matching_line_index = None
        matching_text = ["Permanent", "Pe@fanent", "Pe@ffignent",
                          "Pertianent", "Account", "Number", "Card"]
        matching_pan_num_coord = []
        result = []

        # find matching text coordinates
        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
         if text in matching_text:
              matching_line_index = i
              break
        if matching_line_index is None:
            return result
        
        # find the pan card coordinates
        for i in range(matching_line_index, len(self.coordinates)):
         text = self.coordinates[i][4]
         if len(text) == 10 and text.isupper() and text.isalnum():
              matching_pan_num_coord = [self.coordinates[i][0], self.coordinates[i][1],
                                         self.coordinates[i][2], self.coordinates[i][3]]
              break
         
        # adjust the width
        if not matching_pan_num_coord:
            return result
        
        width = matching_pan_num_coord[2] - matching_pan_num_coord[0]
        result = [matching_pan_num_coord[0], matching_pan_num_coord[1], 
                  matching_pan_num_coord[0] + int(0.65 * width), matching_pan_num_coord[3]]
        return result
    
      
    # func: collect the DOB
    def __extract_dob(self) -> list:
        # date pattern DD/MM/YYY
        date_pattern = r'\d{2}/\d{2}/\d{4}'
        text_date_coordinates = []
        dob_coords = []

        for i, (x1,y1,x2,y2,text) in enumerate(self.coordinates):
            match = re.search(date_pattern, text)
            if match:
                text_date_coordinates = [x1, y1, x2, y2]
                break
        
        if len(text_date_coordinates) == 0:
            return dob_coords
        
        # get first 6 chars
        width = text_date_coordinates[2] - text_date_coordinates[0]
        dob_coords = [text_date_coordinates[0], text_date_coordinates[1], text_date_coordinates[0] + int(0.54 * width), text_date_coordinates[3]]
        return dob_coords

    # func: extract user name and Father's name from Pan card Pattern 1
    def __extract_names_pancard_p1(self, matching_text) -> list:
        name = PanCardPattern1(self.coordinates, self.text, matching_text).search_coordinates_user_father_name()
        return name
    
    # func: extract user name and Father's name from Pan card Pattern 2
    def __extract_names_pancard_p2(self,index_num) -> list:
        matching_text_keyword = [" GOVT.", "INDIA", "INCOME", "TAX", "DEPARTMENT"]
        name = PanCardPattern2(self.coordinates, self.text, matching_text_keyword, index_num).search_coordinates_user_father_name()
        return name

    # func: identify pan card pattern
    def __identify_pancard_pattern(self, pancard_pattern_keyword_search: list) -> int:
        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if text in pancard_pattern_keyword_search:
                return 1
        return 0
    
    # func: collect pancard information
    def collect_pancard_info(self) -> dict:
        pancard_pattern_keyword_search = ["Name", "Father's", "Father"]
        pancard_doc_info_list = []

        # Collect : PAN card number
        pancard_number = self.__extract_pan_card_num()
        if not pancard_number:
            self.logger.error(f"| Document Rejected with error ERRPAN1")
            return {"message": "Error extracting PAN card number", "status": "REJECTED"}
        pancard_doc_info_list.append(pancard_number)

         # Collect : DOB
        pancard_dob = self.__extract_dob()
        if not pancard_dob:
            self.logger.error(f"| Document Rejected with error ERRPAN2")
            pancard_doc_info_list = []
            return {"message": "Error extracting DOB from PAN Card", "status": "REJECTED"}
        pancard_doc_info_list.append(pancard_dob)


        # Collect: pan card names
        """
            Collect User name and Father's name from Pan cards Patterns.
            - Identify the pan card pattern
            - Collect User name and Father's name coordinates
        """
        pattern = self.__identify_pancard_pattern(pancard_pattern_keyword_search)
        if pattern == 1:
            # Pan card Pattern 1 found
            username_p1 = self.__extract_names_pancard_p1(["Name"])
            fathername_p1 = self.__extract_names_pancard_p1([ "Father's", "Father"])
            if username_p1 and fathername_p1:
                pancard_doc_info_list.extend(username_p1)
                pancard_doc_info_list.extend(fathername_p1)
            else:
                self.logger.error(f"| Document Rejected with error ERRPAN3")
                pancard_doc_info_list = []
                return {"message": "Error extracting User or Father's name from PAN card", "status": "REJECTED"}
        else:
            # Pan card Pattern 2 found
            username_p2 = self.__extract_names_pancard_p2(1)
            fathername_p2 = self.__extract_names_pancard_p2(2)
            if username_p2 and fathername_p2:
                pancard_doc_info_list.extend(username_p2)
                pancard_doc_info_list.extend(fathername_p2)
            else:
                self.logger.error(f"| Document Rejected with error ERRPAN3")
                pancard_doc_info_list = []
                return {"message": "Error extracting User or Father's name from PAN card", "status": "REJECTED"}

        return {"message": "Successfully Redacted PAN Card", "data": pancard_doc_info_list, "status": "REDACTED"}