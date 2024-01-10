from document_type_identification.identify_documents import DocumentTypeIdentification
from rejected_doc_redacted.redact_rejected_document import RedactRejectedDocument
from pancard.document_info import PancardDocumentInfo
from aadhaarcard.aadhaarcard_front_info import AadhaarCardFrontInfo
from aadhaarcard.eaadhaarcard_info import EAadhaarCardInfo
from passport.document_info import PassportDocumentInfo
from write_xml_data.xmldata import WriteXML
from config.database import MongoDBConnection
from pathlib import Path
import requests
import json

class PerformOCRROnDocument:
    def __init__(self, document_info: list) -> None:
        self.document_info = document_info

        """Establish MongoDB connection"""
        self.db_client = MongoDBConnection().get_connection()

    def ocrr_docs(self):
        for docs in self.document_info:
            document_identification_obj = DocumentTypeIdentification(docs['documentPath'])

            """Identify: Pancard"""
            if document_identification_obj.identify_pancard():
                self.process_pancard(docs['documentPath'], docs['rejectedPath'], 
                                     docs['redactedPath'], docs['documentType'], docs['documentName'], docs['taskId'])
                """Identify: Aadhaar card"""
            elif document_identification_obj.identify_aadhaarcard():
                if document_identification_obj.identify_eaadhaarcard():
                    self.process_eaadhaarcard(docs['documentPath'], docs['rejectedPath'], 
                                     docs['redactedPath'], docs['documentType'], docs['documentName'], docs['taskId'])
                elif document_identification_obj.identify_aadhaarcard_front():
                    self.process_aadhaarcard(docs['documentPath'], docs['rejectedPath'], 
                                     docs['redactedPath'], docs['documentType'], docs['documentName'], docs['taskId'])
                else:
                    self.document_rejected(docs['documentPath'], docs['rejectedPath'], 
                                     docs['redactedPath'], docs['documentType'], docs['documentName'], docs['taskId'])
                """Identify: Passport"""
            elif document_identification_obj.identify_passport():
                self.process_passport(docs['documentPath'], docs['rejectedPath'], 
                                     docs['redactedPath'], docs['documentType'], docs['documentName'], docs['taskId'])
            else:
                self.document_rejected(docs['documentPath'], docs['rejectedPath'], 
                                     docs['redactedPath'], docs['documentType'], docs['documentName'], docs['taskId'])
        
        """Remove collection data from ocrrworkspace db"""
        self.remove_collection_data_ocrrworkspace(self.document_info[0]['taskId'])

        """Send Post request to webhook"""
        self.webhook_post_request(self.document_info[0]['taskId'])

    def process_pancard(self, document_path, rejectedPath, redactedPath, documentType, documentName, taskid):
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

            """Update upload db"""
            self.update_upload_filedetails(taskid, "REDACTED", pancard_result['message'])
        else:
            pass
            
        self.remove_doc_from_workspace(document_path)

    def process_eaadhaarcard(self, document_path, rejectedPath, redactedPath, documentType, documentName, taskid):
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
            
            """Update upload db"""
            self.update_upload_filedetails(taskid, "REDACTED", e_aadhaar_result['message'])
        else:
            pass

        self.remove_doc_from_workspace(document_path)
      
    def process_aadhaarcard(self, document_path, rejectedPath, redactedPath, documentType, documentName, taskid):
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
            
            """Update upload db"""
            self.update_upload_filedetails(taskid, "REDACTED", aadhaar_result['message'])

        else:
            pass
        
        self.remove_doc_from_workspace(document_path)
    
    def process_passport(self, document_path, rejectedPath, redactedPath, documentType, documentName, taskid):
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

            """Update upload db"""
            self.update_upload_filedetails(taskid, "REDACTED", passport_result['message'])
        else:
            pass
        
        self.remove_doc_from_workspace(document_path)
    
    def remove_doc_from_workspace(self, document_path):
         path = Path(document_path)
         path.unlink()
    
    def document_rejected(self,  document_path, rejectedPath, redactedPath, documentType, documentName, taskid ):
        if documentType == "PDF":
            # Get 75% redacted coordinates of the rejected document
            rejected_doc_coordinates = RedactRejectedDocument(document_path).rejected()
            WriteXML(redactedPath, documentName , rejected_doc_coordinates).writexml()
            """Update upload db"""
            self.update_upload_filedetails(taskid, "REDACTED", "Not able to Identify Document")
        else:
            pass

        self.remove_doc_from_workspace(document_path)
    
    def update_upload_filedetails(self, taskid, status, message):
        database_name = "upload"
        collection_name = "fileDetails"
        database = self.db_client[database_name]
        collection = database[collection_name]

        filter_query = {"taskId": taskid}
        update = {"$set" : {
            "status": status,
            "taskResult": message
        }}

        collection.update_one(filter_query, update)
    
    def remove_collection_data_ocrrworkspace(self, taskid):
        database_name = "ocrrworkspace"
        collection_name = "ocrr"
        database = self.db_client[database_name]
        collection = database[collection_name]

        remove_query = {"taskId": taskid}
        collection.delete_one(remove_query)
    
    def webhook_post_request(self, taskid):
        database_name = "upload"

        """Get the payload data from filedetails collection"""
        collection_name = "fileDetails"
        database = self.db_client[database_name]
        collection = database[collection_name]

        taskid_to_filter = {"taskId": taskid}
        result = collection.find_one(taskid_to_filter)

        client_id = result['clientId']
        payload = {
            "taskId": result['taskId'],
            "status": result["status"],
            "taskResult": result["taskResult"],
            "clientId": result["clientId"],
            "uploadDir": result["uploadDir"]
        }

        """Get Client Webhook URL from webhook DB"""
        collection_name = "webhooks"
        database = self.db_client[database_name]
        collection = database[collection_name]

        filter_query = {"clientId": client_id}
        client_doc = collection.find_one(filter_query)

        if client_doc:
            WEBHOOK_URL = client_doc["url"]
            HEADER = {'Content-Type': 'application/json'}
            requests.post(WEBHOOK_URL+"/CVCore/processstatus", data=json.dumps(payload), headers=HEADER)
        else:
            print("ERROR")
