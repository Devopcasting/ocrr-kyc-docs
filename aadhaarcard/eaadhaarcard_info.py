import os
import re
import pytesseract
from helper.text_coordinates import TextCoordinates
from helper.text_lang_coordinates import TextLangCoordinates
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging

class EAadhaarCardInfo:
    def __init__(self, document_path: str) -> None:
        self.document_path = document_path
    
        # Configure logger
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()

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
                                                
     # func: top side native language name
    def top_native_eng_lang_name(self, index: int) -> list:

        result = []

        # clean text list
        clean_text = [i for i in self.text_lang.split("\n") if len(i) != 0]
        print(clean_text)
        # get matching text below
        matching_text = self.below_matching_text(clean_text, index)
        print(matching_text)
        if not matching_text:
            return result
        
        result = self.get_top_native_name_coords(matching_text, self.coordinates_lang)
        return result
    
    # func: find text below matching text
    def below_matching_text(self, clean_text: list, index: int) -> list:
        # find text below matching text
        matching_text = []
        for i,text in enumerate(clean_text):
            if "To" in text:
                matching_text = clean_text[i + index].split()
                break
        return matching_text
    
    # func: get top native name coordinates
    def get_top_native_name_coords(self, matching_text: list, coords) -> list:
        result = []
         
        if len(matching_text) > 1:
            matching_text = matching_text[:-1]

        for i,(x1, y1, x2, y2, text) in enumerate(coords):
            if text in matching_text:
                result.append([x1, y1, x2, y2])
            # if len(matching_text) == len(result):
            #     break
        return result
    
    # func: get user name in english
    def get_username_in_eng(self):
        result = []
        # clean text list
        clean_text = [i for i in self.text_eng.split("\n") if len(i) != 0]
        print(clean_text)
        # get matching text below
        matching_text = []
        for i,text in enumerate(clean_text):
            if "dob" in text.lower() or "birth" in text.lower() or "bith" in text.lower() or "year" in text.lower() or "binh" in text.lower():
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

        # get matching text below
        matching_text = []
        for i,text in enumerate(clean_text):
            if "dob" in text.lower() or "birth" in text.lower() or "bith" in text.lower():
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
            if re.match(r'^\d{2}/\d{2}/\d{4}$', self.coordinates[i][4]) or re.match(r'^\d{4}$', self.coordinates[i][4]):
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
        gender_coordinates = []
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
            if re.match(r'^\d{2}/\d{2}/\d{4}$', self.coordinates[i][4]) or re.match(r'^\d{4}$', self.coordinates[i][4]):
                break
            else:
                gender_coordinates.append([self.coordinates[i][0], self.coordinates[i][1], 
                                           self.coordinates[i][2], self.coordinates[i][3]])
        # Prepare final coordinates
        result = [gender_coordinates[-1][0], gender_coordinates[-1][1], gender_coordinates[0][2], gender_coordinates[0][3]]
        return result
    
    # func: collect aadhaar card number
    def __extract_eaadharcard_number(self, matching_text: str) -> list:
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

    # func: collect mobile number
    def __extract_mobile_number(self):
        result = []
        mobile_coords = []

        for i,(x1, y1, x2, y2,text) in enumerate(self.coordinates):
            if len(text) == 10 and text.isdigit():
                mobile_coords = [x1, y1, x2, y2]
                break
        if not mobile_coords:
            return result
        
        # Get first 6 chars
        width = mobile_coords[2] - mobile_coords[0]
        result = [mobile_coords[0], mobile_coords[1], mobile_coords[0] + int(0.54 * width), mobile_coords[3]]
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
    
    # func: collect E-Aadhaar card information
    def collect_eaadhaarcard_info(self):
        eaadhaarcard_info_list = []

        # Collect: User name in regional language
        user_name_in_regional = self.get_username_in_regional_lang()
        if not user_name_in_regional:
            self.logger.error("| E-Aadhaar Error: User name in regional language")
            return {"message": "E-Aadhaar Error: User name in regional language", "status": "REJECTED"}
        eaadhaarcard_info_list.extend(user_name_in_regional)
        
        # Collect: User name in english
        user_name_in_english = self.get_username_in_eng()
        if not user_name_in_english:
            self.logger.error("| E-Aadhaar Error: User name in english language")
            return {"message": "E-Aadhaar Error: User name in english language", "status": "REJECTED"}
        eaadhaarcard_info_list.extend(user_name_in_english)

        # # Collect: Top side name in native language
        # top_side_native_lang_name = self.__top_native_eng_lang_name(1)
        # if not top_side_native_lang_name:
        #     self.logger.error(f"| Document Rejected with error ERREAAD4")
        #     return {"message": "E-Aadhaar Error: extracting name in native language", "status": "REJECTED"}
        # eaadhaarcard_info_list.extend(top_side_native_lang_name)

        # Collect: Top side name in english language
        # top_side_eng_lang_name = self.top_native_eng_lang_name(2)
        # if not top_side_eng_lang_name:
        #     self.logger.error(f"| Document Rejected with error ERREAAD3")
        #     return {"message": "E-Aadhaar Error: extracting name in english", "status": "REJECTED"}
        # eaadhaarcard_info_list.extend(top_side_eng_lang_name)
        
        # Collect: DOB
        aadhaar_card_dob = self.__extract_dob()
        if aadhaar_card_dob:
            eaadhaarcard_info_list.append(aadhaar_card_dob)

        # Collect: E-Aadhaar card Gender
        e_aadhaar_card_gender = self.__extract_gender()
        if not e_aadhaar_card_gender:
            self.logger.error(f"| Document Rejected with error ERREAAD2")
            return {"message": "E-Aadhaar Error: extracting gender", "status": "REJECTED"}
        eaadhaarcard_info_list.append(e_aadhaar_card_gender)

        # Collect: E-Aadhaar card number
        e_aadhaar_card_num = self.__extract_eaadharcard_number("Aadhaar")
        if not e_aadhaar_card_num:
            self.logger.error(f"| Document Rejected with error ERREAAD1")
            return {"message": "E-Aadhaar Error: extracting card number", "status": "REJECTED"}
        eaadhaarcard_info_list.extend(e_aadhaar_card_num)

        # Collect: Mobile number
        mobile_number = self.__extract_mobile_number()
        if mobile_number:
            eaadhaarcard_info_list.append(mobile_number)
        
        # Collect: Pin Code number
        pincode_number = self.__extract_pincode_number()
        if pincode_number:
            eaadhaarcard_info_list.append(pincode_number)

        # Collect: State name
        state_name = self.__extract_state()
        if state_name:
            eaadhaarcard_info_list.extend(state_name)

        return {"message": "Successfully Redacted E-Aadhaar", "data": eaadhaarcard_info_list, "status": "REDACTED"}