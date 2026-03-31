import os
import logging
from modules.pdf_processor import process_pdf
from modules.ocr_engine import extract_text_from_images
from modules.link_extractor import process_links
from modules.nlp_processor import extract_nlp_info
from modules.output_formatter import generate_all_outputs

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_document(filepath, output_dir):
    """Core processing pipeline."""
    filename = os.path.basename(filepath)
    logging.info(f"Starting processing for {filename}")
    
    try:
        # 1. PDF Processing & Extraction
        # Extracts pages as images, digital text, and embedded links. Detects tables/images.
        logging.info("Step 1: Extracted PDF/Image contents...")
        pdf_data = process_pdf(filepath, output_dir)
        
        # 2. Image Preprocessing is skipped as OCR handles paths natively now
        logging.info("Step 2: PDF converted to image paths...")
        
        # 3. OCR Processing
        logging.info("Step 3: Extracting text using OCR...")
        ocr_data = {'full_text': '', 'avg_confidence': '0.0%'}
        try:
            if pdf_data['page_images'] and len(pdf_data.get('digital_text', '').strip()) < 50:
                logging.info("No digital text found. Proceeding with OCR...")
                ocr_data = extract_text_from_images(pdf_data['page_images'])
            else:
                logging.info("Skipping OCR: Sufficient digital text was already extracted.")
        except Exception as e:
            logging.error(f"OCR Pipeline failed: {str(e)}")
        
        # 4. Link Extraction and Validation
        logging.info("Step 4: Extracting and validating links...")
        all_links = process_links(pdf_data['digital_text'], ocr_data['full_text'], pdf_data['embedded_links'])
        
        # 5. NLP Entity Extraction & Structuring
        logging.info("Step 5: Performing NLP entity and section extraction...")
        # Combine digital and OCR text (giving priority to digital if available, or combining both)
        combined_text = pdf_data['digital_text'] + "\n\n" + ocr_data['full_text']
        nlp_data = extract_nlp_info(combined_text)
        
        # 6. Structuring the JSON Data
        logging.info("Step 6: Formatting outputs to JSON, CSV, Excel...")
        
        final_data = {
            "document_info": {
                "filename": filename,
                "pages": len(pdf_data['page_images']),
                "file_type": filepath.split('.')[-1].upper()
            },
            "summary": nlp_data.get('summary', "Summary not available."),
            "key_information": nlp_data.get('key_information', {}),
            "sections": nlp_data.get('sections', []),
            "links": all_links,
            "entities": nlp_data.get('entities', []),
            "raw_text": {
                "digital": pdf_data['digital_text'],
                "ocr": ocr_data['full_text']
            },
            "tables": pdf_data.get('tables', []),
            "metadata": {
                "ocr_confidence_avg": ocr_data.get('avg_confidence', 0.0),
                "images_extracted": len(pdf_data.get('extracted_images', [])),
            }
        }
        
        # 7. Write Outputs
        # Use filename prefix
        prefix = filename.rsplit('.', 1)[0]
        result_json_path = os.path.join(output_dir, f"{prefix}_result.json")
        csv_path = os.path.join(output_dir, f"{prefix}_output.csv")
        excel_path = os.path.join(output_dir, f"{prefix}_output.xlsx")
        
        generate_all_outputs(final_data, result_json_path, csv_path, excel_path)
        
        logging.info(f"Processing complete! Results saved to {result_json_path}")
        return result_json_path
        
    except Exception as e:
        logging.error(f"Error processing pipeline: {str(e)}")
        raise e
