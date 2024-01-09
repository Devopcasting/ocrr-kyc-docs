class IdentifyPassPort:
    def __init__(self, clean_text: list) -> None:
        self.clean_text = clean_text
        # Search keyword for Passport
        self.passport_identifiers = ["republic", "jpassport", "passport"]

    def check_passport(self) -> bool:
        for i in self.clean_text:
            for k in i.split():
                if k.lower() in self.passport_identifiers:
                    return True
        return False