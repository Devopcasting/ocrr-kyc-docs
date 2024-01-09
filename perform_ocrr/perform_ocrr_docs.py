from document_type_identification.identify_documents import DocumentTypeIdentification
from rejected_doc_redacted.redact_rejected_document import RedactRejectedDocument
from pancard.document_info import PancardDocumentInfo
from aadhaarcard.aadhaarcard_front_info import AadhaarCardFrontInfo
from aadhaarcard.eaadhaarcard_info import EAadhaarCardInfo
from passport.document_info import PassportDocumentInfo
from write_xml_data.xmldata import WriteXML
import shutil
from pathlib import Path

class PerformOCRROnDocument:
    def __init__(self, document_info: list) -> None:
        self.document_info = document_info

    def ocrr_docs(self):
        for docs in self.document_info:
            document_identification_obj = DocumentTypeIdentification(docs['documentPath'])

            """Identify: Pancard"""
            if document_identification_obj.identify_pancard():
                self.process_pancard(docs['documentPath'], docs['rejectedPath'], 
                                     docs['redactedPath'], docs['documentType'], docs['documentName'])
                
                """Identify: Aadhaar card"""
            elif document_identification_obj.identify_aadhaarcard():
                if document_identification_obj.identify_eaadhaarcard():
                    self.process_eaadhaarcard(docs['documentPath'], docs['rejectedPath'], 
                                     docs['redactedPath'], docs['documentType'], docs['documentName'])
                elif document_identification_obj.identify_aadhaarcard_front():
                    self.process_aadhaarcard(docs['documentPath'], docs['rejectedPath'], 
                                     docs['redactedPath'], docs['documentType'], docs['documentName'])
                else:
                    self.document_rejected(docs['documentPath'], docs['rejectedPath'], 
                                     docs['redactedPath'], docs['documentType'], docs['documentName'])
            elif document_identification_obj.identify_passport():
                self.process_passport(docs['documentPath'], docs['rejectedPath'], 
                                     docs['redactedPath'], docs['documentType'], docs['documentName'])
            else:
                self.document_rejected(docs['documentPath'], docs['rejectedPath'], 
                                     docs['redactedPath'], docs['documentType'], docs['documentName'])
    
    def process_pancard(self, document_path, rejectedPath, redactedPath, documentType, documentName):
        pancard_result = PancardDocumentInfo(document_path).collect_pancard_info()
        status = pancard_result['status']

        if documentType == "PDF":
            """Check the status"""
            if status == "REJECTED":
                # Get 75% redacted coordinates of the rejected document
                rejected_doc_coordinates = RedactRejectedDocument(document_path).rejected()
                WriteXML(redactedPath, documentName , rejected_doc_coordinates).writexml()
            else:
                redacted_doc_coordinates = pancard_result['data']
                WriteXML(redactedPath, documentName , redacted_doc_coordinates).writexml()
            
        self.remove_doc_from_workspace(document_path)

    def process_eaadhaarcard(self, document_path, rejectedPath, redactedPath, documentType, documentName):
        e_aadhaar_result = EAadhaarCardInfo(document_path).collect_eaadhaarcard_info()
        status = e_aadhaar_result['status']

        if documentType == "PDF":
            if status == "REJECTED":
                # Get 75% redacted coordinates of the rejected document
                rejected_doc_coordinates = RedactRejectedDocument(document_path).rejected()
                WriteXML(redactedPath, documentName , rejected_doc_coordinates).writexml()
            else:
                redacted_doc_coordinates = e_aadhaar_result['data']
                WriteXML(redactedPath, documentName , redacted_doc_coordinates).writexml()

        self.remove_doc_from_workspace(document_path)
      
    def process_aadhaarcard(self, document_path, rejectedPath, redactedPath, documentType, documentName):
        aadhaar_result = AadhaarCardFrontInfo(document_path).collect_aadhaarcard_front_info()
        status = aadhaar_result['status']

        if documentType == "PDF":
            if status == "REJECTED":
                # Get 75% redacted coordinates of the rejected document
                rejected_doc_coordinates = RedactRejectedDocument(document_path).rejected()
                WriteXML(redactedPath, documentName , rejected_doc_coordinates).writexml()
            else:
                redacted_doc_coordinates = aadhaar_result['data']
                WriteXML(redactedPath, documentName , redacted_doc_coordinates).writexml()
        
        self.remove_doc_from_workspace(document_path)
    
    def process_passport(self, document_path, rejectedPath, redactedPath, documentType, documentName):
        passport_result = PassportDocumentInfo(document_path).collect_passport_info()
        status = passport_result['status']

        if documentType == "PDF":
            if status == "REJECTED":
                # Get 75% redacted coordinates of the rejected document
                rejected_doc_coordinates = RedactRejectedDocument(document_path).rejected()
                WriteXML(redactedPath, documentName , rejected_doc_coordinates).writexml()
            else:
                redacted_doc_coordinates = passport_result['data']
                WriteXML(redactedPath, documentName , redacted_doc_coordinates).writexml()
        
        self.remove_doc_from_workspace(document_path)
    
    def remove_doc_from_workspace(self, document_path):
         path = Path(document_path)
         path.unlink()
    
    def document_rejected(self,  document_path, rejectedPath, redactedPath, documentType, documentName ):
        if documentType == "PDF":
            # Get 75% redacted coordinates of the rejected document
            rejected_doc_coordinates = RedactRejectedDocument(document_path).rejected()
            WriteXML(redactedPath, documentName , rejected_doc_coordinates).writexml()
        else:
            pass

        self.remove_doc_from_workspace(document_path)
  