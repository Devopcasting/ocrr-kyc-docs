import pytesseract
import re
import os
from helper.text_coordinates import TextCoordinates
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging

class PassportDocumentInfo:
    def __init__(self, document_path) -> None:
        # Configure logger
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()

        # Get the coordinates of all the extracted text
        self.coordinates = TextCoordinates(document_path, doc_type="passport").generate_text_coordinates()
    
        self.states = ['andhra pradesh', 'arunachal pradesh', 'assam', 'bihar', 'chandigarh (ut)', 
                       'chhattisgarh', 'dadra and nagar haveli (ut)', 'daman and diu (ut)', 'delhi (nct)', 
                       'goa', 'gujarat', 'haryana', 'himachal pradesh', 'jammu and kashmir', 'jharkhand', 
                       'karnataka', 'kerala', 'lakshadweep (ut)', 'madhya pradesh', 'maharashtra', 'manipur', 
                       'meghalaya', 'mizoram', 'nagaland', 'odisha', 'puducherry (ut)', 'punjab', 'rajasthan', 
                       'sikkim', 'tamil nadu', 'telangana', 'tripura', 'uttarakhand', 'uttar pradesh']
        
        # Get the texts from document
        tesseract_config = r'-l eng --oem 3 --psm 11'
        self.text = pytesseract.image_to_string(document_path, config=tesseract_config)

    
    def __extract_passport_number(self) -> list:
        matching_line_index_top = None
        matching_line_index_bottom = None
        matching_passport_text = None
        matching_text = "passport"
        matching_passport_number_coords_top = []
        matching_passport_number_coords_bottom = []
        result = []

        # find matching text coordinates
        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if matching_text in text.lower():
                matching_line_index_top = i
                break
        if matching_line_index_top is None:
            return result
       
        # find the top Passport coordinates
        for i in range(matching_line_index_top, len(self.coordinates)):
            text = self.coordinates[i][4]
            if len(text) == 8 and text.isupper() and text.isalnum():
                matching_passport_number_coords_top = [self.coordinates[i][0], self.coordinates[i][1],
                                         self.coordinates[i][2], self.coordinates[i][3]]
                matching_line_index_bottom = i
                matching_passport_text = text
                break

        if matching_line_index_bottom is None:
            return result
        
        # find the bottom Passport coordinates
        for i in range(matching_line_index_bottom + 1, len(self.coordinates)):
            text = self.coordinates[i][4]
            if matching_passport_text in text:
                matching_passport_number_coords_bottom = [self.coordinates[i][0], self.coordinates[i][1],
                                         self.coordinates[i][2], self.coordinates[i][3]]
                break
        if not matching_passport_number_coords_bottom:
            return result
       
        result.append(matching_passport_number_coords_top)
        result.append(matching_passport_number_coords_bottom)
        return result

    def __extract_dates(self) -> list:
        # date pattern DD/MM/YYY
        date_pattern = r'\d{2}/\d{2}/\d{4}'
        date_coordinates = []
        result = []

        for i, (x1,y1,x2,y2,text) in enumerate(self.coordinates):
            date_match = re.search(date_pattern, text)
            if date_match:
                date_coordinates.append([x1, y1, x2, y2])

        if not date_coordinates:
            return result
        
        # Get the first 6 chars
        for i in date_coordinates:
            width = i[2] - i[0]
            result.append([i[0], i[1], i[0] + int(0.54 * width), i[3]])
        return result

    def __extract_gender(self) -> list:
        gender_text = ['M', 'F']
        result = []

        for i, (x1,y1,x2,y2,text) in enumerate(self.coordinates):
            if text in gender_text:
                result = [x1, y1, x2, y2]
                break
        return result

    def __extract_surname(self):
        matching_text = "Surname"
        surname = []
        result = []
        # split the text into lines
        lines = [i for i in self.text.splitlines() if len(i) != 0]
        
        # find the line that matches search text
        matching_line_index = self.__find_matching_line_index(lines, matching_text)
        if matching_line_index == 0:
            return result
        
        # get the next line in the text
        next_line_list = []
        for line in lines[matching_line_index + 2 :]:
            if line.lower() in 'faa ora arr /given names':
                break
            else:
                next_line_list.append(line)

        if not next_line_list:
            result

        for i in next_line_list:
            for k, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if i == text:
                    surname.append([x1, y1, x2, y2])
        
        for i in surname:
            width = i[2] - i[0]
            result.append([i[0], i[1], i[0] + int(0.40 * width), i[3]])

        return result

    def __extract_given_name(self):
        matching_text = 'Names'
        given_name = []
        result = []

        # split the text into lines
        lines = [i for i in self.text.splitlines() if len(i) != 0]

        # find the line that matches search text
        matching_line_index = self.__find_matching_line_index(lines, matching_text)
        if matching_line_index == 0:
            return result

        # get the next line in the text
        next_line_list = []
        for line in lines[matching_line_index + 1 :]:
            if line.lower() in 'fier /sex':
                break
            else:
                next_line_list.append(line)

        if not next_line_list:
            result

        for i in next_line_list:
            for k, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if i == text:
                    given_name.append([x1, y1, x2, y2])
        
        for i in given_name:
            width = i[2] - i[0]
            result.append([i[0], i[1], i[0] + int(0.40 * width), i[3]])

        return result
    
    def __extract_father_name(self):
        matching_text = "Father"
        father_name = []
        result = []

        # split the text into lines
        lines = [i for i in self.text.splitlines() if len(i) != 0]

        # find the line that matches search text
        matching_line_index = self.__find_matching_line_index(lines, matching_text)
        if matching_line_index == 0:
            return result

        # get the next line in the text
        next_line_list = []
        for line in lines[matching_line_index + 1 :]:
            if "mother" in line.lower():
                break
            else:
                next_line_list.extend(line.split())

        if not next_line_list:
            return result

        for i in next_line_list:
            for k, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if i == text:
                    father_name.append([x1, y1, x2, y2])
        
        for i in father_name:
            width = i[2] - i[0]
            result.append([i[0], i[1], i[0] + int(0.40 * width), i[3]])
        
        return result

    def __extract_mother_name(self):
        matching_text = "Mother"
        mother_name = []
        result = []

        # split the text into lines
        lines = [i for i in self.text.splitlines() if len(i) != 0]

        # find the line that matches search text
        matching_line_index = self.__find_matching_line_index(lines, matching_text)
        if matching_line_index == 0:
            return result

        # get the next line in the text
        next_line_list = []
        for line in lines[matching_line_index + 1 :]:
            if "af ar of a ora /name of spouse" in line.lower():
                break
            else:
                next_line_list.extend(line.split())

        if not next_line_list:
            return result

        for i in next_line_list:
            for k, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if i == text:
                    mother_name.append([x1, y1, x2, y2])
        
        for i in mother_name:
            width = i[2] - i[0]
            result.append([i[0], i[1], i[0] + int(0.40 * width), i[3]])
        
        return result

    def __extract_address(self):
        matching_text = 'Address'
        result = []

        # split the text into lines
        lines = [i for i in self.text.splitlines() if len(i) != 0]

        # find the line that matches search text
        matching_line_index = self.__find_matching_line_index(lines, matching_text)
        if matching_line_index == 0:
            return result

        # get the next line in the text
        next_line_list = []
        for line in lines[matching_line_index + 1 :]:
            if len(line) == 6 and line.isdigit():
                break
            else:
                next_line_list.append(line)

        if not next_line_list:
            result

        for i in next_line_list:
            for k, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if i == text:
                    result.append([x1, y1, x2, y2])
        return result

    def __find_matching_line_index(self, lines: list, matching_text: str ) -> int:
        # find the line that matches search text
        for i,line in enumerate(lines):
            if matching_text in line:
                return i
        return 0
    
    def __extract_ind_name(self):
        matching_text = 'IND'
        result = []
        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if "IND" in text and '<' in text:
                result.append([x1, y1, x2, y2])
                break
        return result
    
    def __extract_pin_number(self):
        pin_coords = []
        result = []
        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if len(text) == 6 and text.isdigit():
                pin_coords.append([x1, y1, x2, y2])
                break
        
        for i in pin_coords:
            width = i[2] - i[0]
            result.append([i[0], i[1], i[0] + int(0.30 * width), i[3]])
        
        return result

    # func: collect state name
    def __extract_state(self):
        result = []
        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if text.lower() in self.states:
                result.append([x1, y1, x2, y2])
        
        return result
    
        
    # func: collect pancard information
    def collect_passport_info(self) -> dict:
        passport_doc_info_list = []

        # Collect: Passport Number
        passport_number = self.__extract_passport_number()
        if not passport_number:
            self.logger.error(f"| Document Rejected with error ERRPASS1")
            return {"message": "Passport Error: passport number", "status": "REJECTED"}
        passport_doc_info_list.extend(passport_number)

        # Collect: Dates
        passport_dates = self.__extract_dates()
        if not passport_dates:
            self.logger.error(f"| Document Rejected with error ERRPASS2")
            return {"message": "Passport Error: dates", "status": "REJECTED"}
        passport_doc_info_list.extend(passport_dates)

        # Collect: Gender
        passport_gender = self.__extract_gender()
        if not passport_gender:
            self.logger.error(f"| Document Rejected with error ERRPASS3")
            return {"message": "Passport Error: gender", "status": "REJECTED"}
        passport_doc_info_list.append(passport_gender)

        # Collect: Surname
        passport_surname = self.__extract_surname()
        if not passport_surname:
            self.logger.error(f"| Document Rejected with error ERRPASS4")
            return {"message": "Passport Error: surname", "status": "REJECTED"}
        passport_doc_info_list.extend(passport_surname)

        # Collect: Given Name
        passport_given_name = self.__extract_given_name()
        if not passport_given_name:
            self.logger.error(f"| Document Rejected with error ERRPASS5")
            return {"message": "Passport Error: name", "status": "REJECTED"}
        passport_doc_info_list.extend(passport_given_name)

        # Collect: IND Name
        passport_ind_name = self.__extract_ind_name()
        if not passport_ind_name:
            self.logger.error(f"| Document Rejected with error ERRPASS6")
            return {"message": "Passport Error: IND name", "status": "REJECTED"}
        passport_doc_info_list.extend(passport_ind_name)

        # Collect: Father Name
        passport_father_name = self.__extract_father_name()
        if not passport_father_name:
            self.logger.error(f"| Document Rejected with error ERRPASS7")
            return {"message": "Passport Error: father name", "status": "REJECTED"}
        passport_doc_info_list.extend(passport_father_name)

        # Collect: Mother Name
        passport_mother_name = self.__extract_mother_name()
        if not passport_mother_name:
            self.logger.error(f"| Document Rejected with error ERRPASS8")
            return {"message": "Passport Error: mother name", "status": "REJECTED"}
        passport_doc_info_list.extend(passport_mother_name)

        # Collect: Address
        passport_address = self.__extract_address()
        if not passport_address:
            self.logger.error(f"| Document Rejected with error ERRPASS7")
            return {"message": "Passport Error: address", "status": "REJECTED"}
        passport_doc_info_list.extend(passport_address)

        # Collect: Pin Number
        passport_pin_number = self.__extract_pin_number()
        if passport_pin_number:
            passport_doc_info_list.extend(passport_pin_number)

        # Collect: State name
        state_name = self.__extract_state()
        if state_name:
            passport_doc_info_list.extend(state_name)

        # Remove duplicate list of lists
        unique_list = []
        for i in passport_doc_info_list:
            if i not in unique_list:
                unique_list.append(i)

        return {"message": "Passport Successfully Redacted", "data": unique_list, "status": "REDACTED"}
