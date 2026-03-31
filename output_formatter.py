import json
import pandas as pd
import logging

def generate_all_outputs(data_dict, json_path, csv_path, excel_path):
    """
    Takes the aggregated final dictionary and dumps it into
    JSON format (primary), CSV, and Excel (secondary tabular views).
    """
    try:
        # 1. JSON (Structured Nested Output)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=4, ensure_ascii=False)
            
        # 2. DataFrame generation for CSV / Excel
        # Creating a flattened high-level overview
        flat_data = {
            'Document': [data_dict.get('document_info', {}).get('filename', '')],
            'Pages': [data_dict.get('document_info', {}).get('pages', 0)],
            'File_Type': [data_dict.get('document_info', {}).get('file_type', '')],
            'Summary': [data_dict.get('summary', '')],
            'Name': [data_dict.get('key_information', {}).get('name', '')],
            'Emails': [", ".join(data_dict.get('key_information', {}).get('emails', []))],
            'Phones': [", ".join(data_dict.get('key_information', {}).get('phone', []))],
            'Skills': [", ".join(data_dict.get('key_information', {}).get('skills', []))],
            'Links_Count': [len(data_dict.get('links', []))],
            'Entities_Count': [len(data_dict.get('entities', []))],
            'OCR_Confidence': [data_dict.get('metadata', {}).get('ocr_confidence_avg', '0.0%')]
        }
        main_df = pd.DataFrame(flat_data)
        
        # Write CSV
        main_df.to_csv(csv_path, index=False)
        
        # Write Excel with multiple sheets for context separation
        # using 'openpyxl' engine as dependency
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            main_df.to_excel(writer, sheet_name='Overview', index=False)
            
            # Entities sheet
            if data_dict.get('entities'):
                ent_df = pd.DataFrame(data_dict['entities'])
                ent_df.to_excel(writer, sheet_name='Entities', index=False)
                
            # Links sheet
            if data_dict.get('links'):
                lnk_df = pd.DataFrame(data_dict['links'])
                lnk_df.to_excel(writer, sheet_name='Links', index=False)
                
            # Tables sheet (flatten all tables)
            if data_dict.get('tables'):
                for t in data_dict['tables']:
                    if t.get('data'):
                        t_df = pd.DataFrame(t['data'])
                        sheet_name = f"Table_{t['page']}_{t['table_id']}"
                        t_df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
                        
    except Exception as e:
        logging.error(f"Failed to generate output formats: {str(e)}")
        raise e
