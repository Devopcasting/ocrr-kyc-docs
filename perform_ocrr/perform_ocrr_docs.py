from document_type_identification.identify_documents import DocumentTypeIdentification
from rejected_doc_redacted.redact_rejected_document import RedactRejectedDocument
from write_xml_data.xmldata import WriteXML

class PerformOCRROnDocument:
    def __init__(self, document_info: dict) -> None:
        self.document_info = document_info

    def ocrr_docs(self):
        """
            - Identify Document Type
                - Pancard
                - Aadhaar card
                - E-Aadhaar card
                - Passport
        """
        document_identification_obj = DocumentTypeIdentification(self.document_info['documentPath'])

        """Identify: Pancard"""
        if document_identification_obj.identify_pancard():
            print("PanCard Found")
        else:
            print("Not a valid KYC document")
            self.reject_document()
    
    def reject_document(self):
        # Get 75% redacted coordinates of the rejected document
        rejected_doc_coordinates = RedactRejectedDocument(self.document_info['documentPath']).rejected()
        write_xml_data_coordinates = WriteXML(self.document_info['rejectedPath'], self.document_info['documentName'] ,rejected_doc_coordinates).writexml()