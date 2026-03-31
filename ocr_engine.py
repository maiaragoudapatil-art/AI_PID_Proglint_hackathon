import easyocr
import logging

# Initialize EasyOCR
# lang_list=['en'] specifies the English language
ocr = easyocr.Reader(['en'])

def extract_text_from_images(image_paths):
    """
    Takes a list of image file paths and extracts text using EasyOCR.
    Handles both printed and handwritten text natively.
    Returns full concatenated text and average confidence score.
    """
    total_text = ""
    confidences = []
    
    for page_idx, img_path in enumerate(image_paths):
        try:
            logging.info(f"Running EasyOCR on {img_path}")
            result = ocr.readtext(img_path)
            
            # result is a list of tuples: (bounding_box, 'text', confidence_score)
            if not result:
                continue
                
            for res_group in result:
                text = res_group[1]
                conf = float(res_group[2])
                total_text += text + "\n"
                confidences.append(conf)
                
        except Exception as e:
             logging.error(f"OCR Error on {img_path}: {str(e)}")
            
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    
    return {
        'full_text': total_text.strip(),
        'avg_confidence': f"{round(avg_conf * 100, 2)}%"
    }
