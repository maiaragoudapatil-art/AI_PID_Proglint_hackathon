import os
import fitz # PyMuPDF
from PIL import Image
import io

def process_pdf(filepath, output_dir):
    """
    Reads a document (PDF or Image), extracts text, links, forms images of each page,
    detects tables, and extracts embedded images.
    """
    results = {
        'digital_text': '',
        'embedded_links': [],
        'page_images': [],  # In-memory PIL Images or paths
        'extracted_images': [], # Saved to output/images
        'tables': [] # Structured tables from PDF
    }
    
    images_dir = os.path.join(output_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)
    
    # If the file is already an image, just read it
    if filepath.lower().endswith(('.png', '.jpg', '.jpeg')):
        # For uniformity, pass the path directly instead of PIL Image
        results['page_images'].append(filepath)
        return results

    # Process PDF
    doc = fitz.open(filepath)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # 1. Digital Text
        text = page.get_text()
        if text:
            results['digital_text'] += text + "\n"
            
        # 2. Embedded Links
        links = page.get_links()
        for link in links:
            if 'uri' in link:
                results['embedded_links'].append(link['uri'])
                
        # 3. Extract Tables
        # PyMuPDF has find_tables() for >= 1.23.0
        try:
            tabs = page.find_tables()
            if tabs is not None and len(tabs.tables) > 0:
                for t_idx, tab in enumerate(tabs.tables):
                    df = tab.to_pandas()
                    results['tables'].append({
                        "page": page_num + 1,
                        "table_id": t_idx + 1,
                        "data": df.fillna('').to_dict(orient='records')
                    })
        except Exception as e:
            print(f"Table extraction error on page {page_num}: {e}")
            pass
            
        # 4. Extract Embedded Images
        image_list = page.get_images(full=True)
        for img_idx, img_info in enumerate(image_list):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            img_path = os.path.join(images_dir, f"page{page_num+1}_img{img_idx+1}.{image_ext}")
            with open(img_path, "wb") as f:
                f.write(image_bytes)
            results['extracted_images'].append(img_path)
            
        # 5. Page Image for OCR Pipeline
        zoom = 2.0  # Increase resolution for better OCR
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_path = os.path.join(images_dir, f"page_{page_num+1}_ocr.png")
        pix.save(img_path)
        results['page_images'].append(img_path)
        
    doc.close()
    return results
