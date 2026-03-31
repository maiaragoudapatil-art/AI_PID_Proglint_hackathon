import cv2
import numpy as np

def enhance_images(pil_images):
    """
    Takes a list of PIL Images, converts to OpenCV format,
    and applies preprocessing: grayscale, noise removal, thresholding.
    Returns a list of NumPy arrays ready for PaddleOCR.
    """
    processed_images = []
    
    for pil_img in pil_images:
        # Convert PIL to OpenCV (RGB to BGR)
        open_cv_image = np.array(pil_img)
        # Some images might be 'L' (grayscale) or 'RGBA'. Adjusting here.
        if len(open_cv_image.shape) == 2:
            open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_GRAY2BGR)
        elif open_cv_image.shape[2] == 4:
            open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGBA2BGR)
        else:
            open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)
            
        # 1. Grayscale
        gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)
        
        # 2. Noise Removal (Fast NL Means)
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        # 3. Thresholding (Adaptive / Otsu)
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # PaddleOCR models generally expect 3-channel input
        thresh_3_channel = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
        
        processed_images.append(thresh_3_channel)
        
    return processed_images
