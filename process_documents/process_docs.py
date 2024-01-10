import magic
import fitz
import os
import cv2
import shutil
from PIL import Image
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from perform_ocrr.perform_ocrr_docs import PerformOCRROnDocument
from time import sleep

class ProcessDocuments:
    def __init__(self, inprogress_queue: object, upload_path: str, workspace_path: str) -> None:
        """Logger"""
        logger_config = OCRREngineLogging()
        self.logger = logger_config.configure_logger()

        self.inprogress_queue = inprogress_queue
        self.upload_path = upload_path
        self.workspace_path = workspace_path
    
    def process_docs(self):
        """Identify the document format (JPEG or PDF)"""
        while True:
            document_info = self.inprogress_queue.get()
            if document_info is not None:
                get_doc_format = self.identify_document_format(document_info['path'])

                if get_doc_format == "JPEG":
                    self.logger.info(f"PDF document found '{document_info['path']}")
                    document_name_prefix = self.get_prefix_name(document_info['path'])
                    document_name = os.path.basename(document_info['path'])
                    renamed_doc_name = f"{document_name_prefix}{document_name}"
                    jpeg_path = os.path.join(self.workspace_path, renamed_doc_name)
                    document_info_list = []

                    """Copy document to workspace"""
                    shutil.copy(document_info['path'], jpeg_path )

                    # Perform Pre-Processing of documents
                    self.pre_process_docs(jpeg_path, renamed_doc_name)

                    """Perform OCR-Redaction and Prepare Coordinates XML file"""
                    document_info_list = [
                        {
                            "taskId": document_info['taskId'],
                            "documentType": "JPEG",
                            "roomName": document_name_prefix.split('+')[0],
                            "roomID": document_name_prefix.split('+')[1],
                            "documentName": document_name,
                            "documentPath": jpeg_path,
                            "uploadPath": self.upload_path,
                            "rejectedPath": self.upload_path+"\\"+document_name_prefix.split('+')[0]+"\\"+document_name_prefix.split('+')[1]+"\\"+"Rejected",
                            "redactedPath": self.upload_path+"\\"+document_name_prefix.split('+')[0]+"\\"+document_name_prefix.split('+')[1]+"\\"+"Redacted"
                        }
                    ]
                    perform_ocrr = PerformOCRROnDocument(document_info_list).ocrr_docs()

                elif get_doc_format == "PDF":
                    """
                        PDF info that need to be passed
                        - PDF document name
                        - Number of Frames
                        - Workspace path for PDF
                    """
                    self.logger.info(f"PDF document found '{document_info['path']}")
                    document_name_prefix = self.get_prefix_name(document_info['path'])
                    document_name = os.path.splitext(os.path.basename(document_info['path']))[0]
                    frame_count = self.count_pdf_frames(document_info['path'])
                    document_info_list = []
                    
                    """Convert PDF to JPEG"""
                    # Open PDF File
                    pdf_document = fitz.open(document_info['path'])
                    # Iterate through each page in the PDF
                    for page_number in range(frame_count):
                        # Get the page
                        page = pdf_document[page_number]
                        # Convert the page to an image
                        image = page.get_pixmap()
                        # Create a Pillow image from the raw image data
                        pil_image = Image.frombytes("RGB", [image.width, image.height], image.samples)
                        # Save the Pillow image as a JPEG file
                        document_name_suffix = f"{page_number + 1}F-{document_name}.jpg"
                        jpeg_path = os.path.join(self.workspace_path, f"{document_name_prefix}{document_name_suffix}")
                        pil_image.save(jpeg_path, "JPEG")

                        # Perform Pre-Processing of documents
                        renamed_doc_name = f"{document_name_prefix}{page_number + 1}F-{document_name}.jpg"
                        self.pre_process_docs(jpeg_path, renamed_doc_name)

                        """Perform OCR-Redaction and Prepare Coordinates XML file"""
                        document_info = {
                            "taskId": document_info['taskId'],
                            "documentType": "PDF",
                            "roomName": document_name_prefix.split('+')[0],
                            "roomID": document_name_prefix.split('+')[1],
                            "documentName": document_name_suffix,
                            "documentPath": jpeg_path,
                            "uploadPath": self.upload_path,
                            "frameCount": frame_count,
                            "rejectedPath": self.upload_path+"\\"+document_name_prefix.split('+')[0]+"\\"+document_name_prefix.split('+')[1]+"\\"+"Rejected",
                            "redactedPath": self.upload_path+"\\"+document_name_prefix.split('+')[0]+"\\"+document_name_prefix.split('+')[1]+"\\"+"Redacted"
                        }
                        document_info_list.append(document_info)  
                    pdf_document.close()

                    """Perform OCRR"""
                    perform_ocrr = PerformOCRROnDocument(document_info_list).ocrr_docs()

            sleep(5)
    
    def identify_document_format(self, document_path: str):
        mime_type = magic.from_file(document_path, mime=True)
        if mime_type.startswith("image/jpeg"):
            return "JPEG"
        elif mime_type == "application/pdf":
            return "PDF"
        else:
            return "IN VALID DOCUMENT"
    
    def count_pdf_frames(self, document_path: str) -> int:
        try:
            pdf_document = fitz.open(document_path)
            total_pages = pdf_document.page_count
            pdf_document.close()
            return total_pages
        except Exception as e:
            print(f"Error: {e}")
            pdf_document.close()
            return 0
        
    def pre_process_docs(self, jpeg_path: str, renamed_doc_name: str):
        # Document processing cv2 values
        sigma_x = 1
        sigma_y = 1
        sig_alpha = 1.5
        sig_beta = -0.2
        gamma = 0

        """Pre-process document"""
        document = cv2.imread(jpeg_path)
        denoise_document = cv2.fastNlMeansDenoisingColored(document, None,  10, 10, 7, 21)
        gray_document = cv2.cvtColor(denoise_document, cv2.COLOR_BGR2GRAY)
        gaussian_blur_document = cv2.GaussianBlur(gray_document, (5,5), sigmaX=sigma_x, sigmaY=sigma_y )
        sharpened_image = cv2.addWeighted(gray_document, sig_alpha, gaussian_blur_document, sig_beta, gamma)
        sharpened_image_gray = cv2.cvtColor(sharpened_image, cv2.COLOR_GRAY2BGR)
        cv2.imwrite(os.path.join(jpeg_path, renamed_doc_name), sharpened_image_gray)
    
    def get_prefix_name(self, document_path: str) -> str:
        renamed_doc_list = document_path.split("\\")
        renamed_doc = renamed_doc_list[-3]+"+"+renamed_doc_list[-2]+"+"
        return renamed_doc