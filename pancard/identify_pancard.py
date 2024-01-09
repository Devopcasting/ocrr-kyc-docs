class IdentifyPanCard:
    def __init__(self, clean_text: list) -> None:
        self.clean_text = clean_text
        # Search keyword for Pan card
        self.pancard_identifiers = ["income", "tax", "incometax", 
                                    "department", "permanent", "petianent", "incometaxdepartment"]

    def check_pan_card(self) -> bool:
        for i in self.clean_text:
            for k in i.split():
                if k.lower() in self.pancard_identifiers:
                    return True
        return False