import configparser
import threading
import queue
import sys
from config.database import MongoDBConnection
from in_progress.filter_in_progress import FilterInProgressDocuments
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging


class OCRREngine:
    def __init__(self) -> None:
        """Logger"""
        logger_config = OCRREngineLogging()
        self.logger = logger_config.configure_logger()

        """Establish OCRR Workspace DB connection"""
        database_name = "ocrrworkspace"
        collection_name = "ocrr"
        db_client = MongoDBConnection().get_connection()
        if db_client is not None:
            self.logger.info("Connection established with MongoDB")
            """Create OCRRWORKSPACE DB and OCRR collection"""
            db_name_list = db_client.list_database_names()
            if database_name not in db_name_list:
                self.logger.info(f"Creating {database_name} database and {collection_name} collection")
                database = db_client[database_name]
                database.create_collection(collection_name)
                db_client.close()
            else:
                self.logger.info(f"Flush {collection_name} collection")
                database = db_client[database_name]
                collection = database[collection_name]
                collection.drop()
                db_client.close()    
        else:
            self.logger.error("Failed to establish connection to MongoDB.")
            self.logger.info("Stopping OCRR Engine")
            db_client.close()
            sys.exit(1)

        """"Set Queue objects"""
        self.in_progress_queue = queue.Queue()
    
    def start_ocrr_engine(self):
        """
            Thread 1:
                Query filter upload database fileDetails collection for status:IN_PROGRESS
                Put the absolute path in Queue
        """
        query_inprogress_obj = FilterInProgressDocuments(upload_path, self.in_progress_queue)
        query_inprogress_thread = threading.Thread(target=query_inprogress_obj.query_in_progress_status)
        
        """Start Thread"""
        query_inprogress_thread.start()
        query_inprogress_thread.join()

if __name__ == '__main__':

    """Read config.ini"""
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(r'C:\Program Files (x86)\OCRR\config\config.ini')

    """Get paths"""
    upload_path = config['Paths']['upload']
    workspace_path = config['Paths']['workspace']

    ocrr = OCRREngine()
    ocrr.start_ocrr_engine()

