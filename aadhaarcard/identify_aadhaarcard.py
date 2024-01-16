class IdentifyAadhaarCard:
    def __init__(self, clean_text: list) -> None:
        self.clean_text = clean_text
        
        # Search keyword for Aadhaar card
        self.aadhaar_card_identifiers = ["government", "government of india", "male", "female", "help@uidal.gov.in", 
                                         "www.uidal.gov.in", "unique identification authority of india", "enrollment", "aadhaar"]
        self.aadhaar_card_identifiers_front = ["government", "government of india", "male", "female"]
        self.eaadhaar_card_identifiers = ["enrollment", "vid:", "enrolment", "enroliment", "your aadhaar no", "/enrolment"]
    
    # func: check for valid aadhaar card
    def check_aadhaar_card(self) -> bool:
        for i in self.clean_text:
            for k in i.split():
                if k.lower() in self.aadhaar_card_identifiers:
                    return True
        return False
    
    # func: check for aadhaar card front or back side
    def check_aadhaar_front(self) -> bool:
        for i in self.clean_text:
            for k in i.split():
                if k.lower() in self.aadhaar_card_identifiers_front:
                    return True
        return False
    
    # func: check for e-aadhaar card
    def check_e_aadhaar_card(self):
        for i in self.clean_text:
            for k in i.split():
                if k.lower() in self.eaadhaar_card_identifiers:
                    return True
        return False