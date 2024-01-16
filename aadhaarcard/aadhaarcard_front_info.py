import pytesseract
import re
import os
from helper.text_coordinates import TextCoordinates
from helper.text_lang_coordinates import TextLangCoordinates
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging

class AadhaarCardFrontInfo:
    def __init__(self, document_path: str) -> None:
        self.document_path = document_path
        # self.upload_path = upload_path
    
        # Configure logger
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()

        tesseract_config = r'-l eng --oem 3 --psm 11'

        # Get coordinates and OCR text output
        self.coordinates = TextCoordinates(self.document_path).generate_text_coordinates()
        self.coordinates_lang = TextLangCoordinates(self.document_path).generate_text_coordinates()

        self.text_eng = pytesseract.image_to_string(self.document_path)
        self.text_lang = pytesseract.image_to_string(self.document_path, lang="hin+eng")

        self.states = ['andhra pradesh', 'arunachal pradesh', 'assam', 'bihar', 'chandigarh (ut)', 
                       'chhattisgarh', 'dadra and nagar haveli (ut)', 'daman and diu (ut)', 'delhi (nct)', 
                       'goa', 'gujarat', 'haryana', 'himachal pradesh', 'jammu and kashmir', 'jharkhand', 
                       'karnataka', 'kerala', 'lakshadweep (ut)', 'madhya pradesh', 'maharashtra', 'manipur', 
                       'meghalaya', 'mizoram', 'nagaland', 'odisha', 'puducherry (ut)', 'punjab', 'rajasthan', 
                       'sikkim', 'tamil nadu', 'telangana', 'tripura', 'uttarakhand', 'uttar pradesh']


     # func: extract name in english and native language
    def __extract_name(self, index: int) -> list[list[int]]:
        """
            Extracts the name in English and Native language from the given text.
            Args:
                index: The index of the language to extract the name from. 1 for English, 2 for native language.
            Returns:
                A list of coordinates of the name in English or native language, or an empty list if the name cannot be found.
        """
        if index == 1:
            coords = self.coordinates
            text_lang = self.text_eng
        else:
            coords = self.coordinates_lang
            text_lang = self.text_lang
        
        name_lang_coords = self.__get_name_lang_coords(coords, text_lang, index)
        return name_lang_coords

    def __get_name_lang_coords(self, coords: list[tuple()], text_lang: str, index: int ) -> list[list[int]]:
        """
            Gets the coordinates of the name in English or native language.
            Args:
                coords: The coordinates of the text in English or native language.
                text_lang: The text in English or native language.
                index: The next index value of matching index.
            Returns:
                A list of coordinates of the name in English or native language, or an empty list if the name cannot be found.
        """
        name_lang_coords = []

        # Split the output text
        lines = [i for i in text_lang.splitlines() if len(i) != 0]

        # Find the matching word index
        matching_index = self.__find_matching_index(lines)
        if matching_index == 0:
            return name_lang_coords

        # Get coordinates of name in english or native language
        name_lang_list = lines[matching_index - index].split()
        if len(name_lang_list) > 1:
            name_lang_list = name_lang_list[:-1]

        for i,(x1, y1, x2, y2, text) in enumerate(coords):
            if text in name_lang_list:
                name_lang_coords.append([x1, y1, x2, y2])
            if len(name_lang_coords) == len(name_lang_list):
                break
            
        return name_lang_coords

    def __find_matching_index(self, text_lines: list) -> int:
        """
            Finds the matching index, which is the index of the line that contains the word "Year" or "DOB".
            Args
                text_lang: The text in English or native language.
            Returns:
                The index of the line that contains the word "Year" or "DOB", or None if the word is not found.
        """
        for i,text in enumerate(text_lines):
            if "Year" in text or "DOB" in text:
                return i
        return 0
    
    # func: get user name in english
    def get_username_in_eng(self):
        result = []
        # clean text list
        clean_text = [i for i in self.text_eng.split("\n") if len(i) != 0]
        # get matching text below
        matching_text = []
        for i,text in enumerate(clean_text):
            if "dob" in text.lower():
                matching_text = clean_text[i - 1].split()
                break
        if not matching_text:
            return result
        
        if len(matching_text) > 1:
            matching_text = matching_text[:-1]
        
        for i, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if text in matching_text:
                result.append([x1, y1, x2, y2])
        return result
    
    # func: get user name in regional lang
    def get_username_in_regional_lang(self):
        result = []

        # clean text list
        clean_text = [i for i in self.text_lang.split("\n") if len(i) != 0]
        print(clean_text)
        # get matching text below
        matching_text = []
        for i,text in enumerate(clean_text):
            if "dob" in text.lower():
                matching_text = clean_text[i - 2].split()
                break
        if not matching_text:
            return result
        
        if len(matching_text) > 1:
            matching_text = matching_text[:-1]
        
        for i, (x1, y1, x2, y2, text) in enumerate(self.coordinates_lang):
            if text in matching_text:
                result.append([x1, y1, x2, y2])
        return result
        
    # func: extract dob
    def __extract_dob(self) -> list:
        dob_coordinates = []
        result = []
        matching_index = 0

        # Get the index of Male or Female
        for i ,(x1,y1,x2,y2,text) in enumerate(self.coordinates):
            if text.lower() in ["male", "female"]:
                matching_index = i
                break
        if matching_index == 0:
            return result
        
        # Reverse loop from Male/Female index until DOB comes
        for i in range(matching_index, -1, -1):
            if re.match(r'^\d{4}$', self.coordinates[i][4]):
                return result
            if re.match(r'^\d{2}/\d{2}/\d{4}$', self.coordinates[i][4]):
                dob_coordinates = [self.coordinates[i][0], self.coordinates[i][1], self.coordinates[i][2], self.coordinates[i][3]]
                break
        if not dob_coordinates:
            return result
      
        # Get first 6 chars
        width = dob_coordinates[2] - dob_coordinates[0]
        result = [dob_coordinates[0], dob_coordinates[1], dob_coordinates[0] + int(0.54 * width), dob_coordinates[3]]
        return result

    # func: extract gender
    def __extract_gender(self) -> list:
        gender_coordinates_eng = []
        gender_coordinates_native_lang = []
        result = []
        matching_index = 0

        # Get the index of Male or Female
        for i ,(x1,y1,x2,y2,text) in enumerate(self.coordinates):
            if text.lower() in ["male", "female"]:
                matching_index = i
                gender_coordinates_eng = [x1, y1, x2, y2]
                break
        if matching_index == 0:
            return result
        
        gender_coordinates_native_lang = self.coordinates[matching_index -1]
        result = [gender_coordinates_native_lang[0], gender_coordinates_native_lang[1], gender_coordinates_eng[2], gender_coordinates_eng[3]]
        return result
        # # Reverse loop from Male/Female index until DOB comes
        # for i in range(matching_index, -1, -1):
        #     if re.match(r'^\d{2}/\d{2}/\d{4}$', self.coordinates[i][4]) or re.match(r'^\d{4}$', self.coordinates[i][4]):
        #         break
        #     else:
        #         gender_coordinates.append([self.coordinates[i][0], self.coordinates[i][1], 
        #                                    self.coordinates[i][2], self.coordinates[i][3]])

        # # Prepare final coordinates
        # result = [gender_coordinates[-1][0], gender_coordinates[-1][1], gender_coordinates[0][2], gender_coordinates[0][3]]
        # return result
    
    # func: collect Aadhaar card number
    def __extract_card_number(self) -> list:
        text_result = []
        matching_index = 0
        result = []

        for i,(x1,y1,x2,y2,text) in enumerate(self.coordinates):
            if text.lower() in ["male", "female"]:
                matching_index = i
        if not matching_index:
            return result
        
        for i in range(matching_index, len(self.coordinates)):
            text = self.coordinates[i][4]
            if len(text) == 4 and text.isdigit():
                text_result.append((text))
            if len(text_result) == 3:
                break
        
        for i in text_result[:-1]:
            for k,(x1,y1,x2,y2,text) in enumerate(self.coordinates):
                if i == text:
                    result.append([x1,y1,x2,y2])
        return result

    # func: collect pin code number
    def __extract_pincode_number(self):
        result = []
        pincode_coords = []

        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if len(text) == 6 and text.isdigit():
                pincode_coords = [x1, y1, x2, y2]
                break
        if not pincode_coords:
            return result
        
        # Get first 3 chars
        width = pincode_coords[2] - pincode_coords[0]
        result = [pincode_coords[0], pincode_coords[1], pincode_coords[0] + int(0.30 * width), pincode_coords[3]]
        return result
    
    # func: collect state name
    def __extract_state(self):
        result = []
        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if text.lower() in self.states:
                result.append([x1, y1, x2, y2])
        
        return result

    # func: collect Aadhaar card information
    def collect_aadhaarcard_front_info(self) -> dict:
        aadhaar_card_info_list = []

        # # Collect: name in native lang
        # aadhaar_card_name_native_lang = self.__extract_name(2)
        # if not aadhaar_card_name_native_lang:
        #     self.logger.error("| Document Rejected with error ERRAAD4")
        #     return {"message": "Aadhaar Error: extracting name in native language", "status": "REJECTED"}        
        # aadhaar_card_info_list.extend(aadhaar_card_name_native_lang)
                                          
        # # Collect: Name in engish
        # aadhaar_card_name_eng = self.__extract_name(1)
        # if not aadhaar_card_name_eng:
        #     self.logger.error("| Document Rejected with error ERRAAD3")
        #     return {"message": "Aadhaar Error: extracting name in english language", "status": "REJECTED"}        
        # aadhaar_card_info_list.extend(aadhaar_card_name_eng)

        
        # Collect: User name in regional language
        user_name_in_regional = self.get_username_in_regional_lang()
        if not user_name_in_regional:
            self.logger.error("| Aadhaar Error: User name in regional language")
            return {"message": "Aadhaar Error: User name in regional language", "status": "REJECTED"}
        aadhaar_card_info_list.extend(user_name_in_regional)
        
        # Collect: User name in english
        user_name_in_english = self.get_username_in_eng()
        if not user_name_in_english:
            self.logger.error("| Aadhaar Error: User name in english language")
            return {"message": "Aadhaar Error: User name in english language", "status": "REJECTED"}
        aadhaar_card_info_list.extend(user_name_in_english)

        # Collect: DOB
        aadhaar_card_dob = self.__extract_dob()
        if aadhaar_card_dob:
            aadhaar_card_info_list.append(aadhaar_card_dob)

        # Collect: Gender
        aadhaar_card_gender = self.__extract_gender()
        if aadhaar_card_gender:
            aadhaar_card_info_list.append(aadhaar_card_gender)
        else:
            self.logger.error(f"| Document Rejected with error ERRAAD2")
            return {"message": "Aadhaar Error: extracting gender", "status": "REJECTED"}        
        
        # Collect: Aadhaar card number
        aadhaar_card_num = self.__extract_card_number()
        if aadhaar_card_num:
            aadhaar_card_info_list.extend(aadhaar_card_num)
        else:
            self.logger.error(f"| Document Rejected with error ERRAAD1")
            return {"message": "Aadhaar Error: extracting card number", "status": "REJECTED"}

        # Collect: Pin Code number
        pincode_number = self.__extract_pincode_number()
        if pincode_number:
            aadhaar_card_info_list.append(pincode_number)

        # Collect: State name
        state_name = self.__extract_state()
        if state_name:
            aadhaar_card_info_list.extend(state_name)
          
        return {"message": "Aadhaar Redacted Successfully", "data": aadhaar_card_info_list, "status": "REDACTED"}