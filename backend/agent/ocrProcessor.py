import os
import sys
import cv2
import numpy as np
from typing import List, Dict
from google import genai
from google.genai import types
from PIL import Image, ImageDraw

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
from schemas import PagePayload
from agent.pdfConverter import convert_pdf_to_images
import json

def contains_blue_handwriting(pil_image: Image.Image) -> bool:
    """
    Converts a PIL Image to OpenCV format in-memory and determines 
    if it contains enough blue pen strokes to warrant processing.
    """
    # 1. Convert PIL image to an OpenCV numpy array (BGR format)
    open_cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    # 2. Convert to HSV space
    hsv = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2HSV)

    # 3. Strict blue pen thresholds (covers light blue gel pens to dark ballpoints)
    lower_blue = np.array([90, 40, 40])
    upper_blue = np.array([135, 255, 255])

    # 4. Create the blue color mask
    blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # 5. Calculate the percentage of blue pixels on the page
    blue_pixels = cv2.countNonZero(blue_mask)
    total_pixels = open_cv_image.shape[0] * open_cv_image.shape[1]
    blue_percentage = (blue_pixels / total_pixels) * 100

    # 6. Set a realistic threshold (0.04% of a 300 DPI page is ~3,600 small pen pixels)
    return blue_percentage > 0.04

def extract_chapters_from_images(image_pages: List[Image.Image], api_key: str) -> Dict[str, str]:
    print("function is running")
    if not api_key:
        raise ValueError("Gemini API key is missing")

    client = genai.Client(api_key=api_key)
    master_chapters_dataset = {}
    
    prompt_instructions = """
    You are an uncompromising data digitization system for regulated biopharma manufacturing logs.
    Your sole task is to extract printed text and handwriting from the provided image, segmented by Chapter ID, and mapped as exact key-value pairs.

    CRITICAL BEHAVIORAL SAFETY RULES:
    1. NEVER correct mathematical or logical errors. If a human writes '100 + 200 = 400', transcribe it exactly as '400'.

    2. NEVER fill in blank text entry fields or unchecked boxes. If a field has no handwriting, label it 'EMPTY'.

    3. Keep number layouts exactly as written (e.g., preserve commas as decimal points if written as '4,5').

    4. NEVER ASSUME OR GUESS unclear text or scribbles. If you cannot read it or determine wheter or not it is marked or not, just append the flag 'UNCLEAR' to the value.

    5. If there are multiple chapters on a single page, extract each chapter separately and label them with their exact chapter numbers.

    6. If a field has multiple choices (e.g., checkboxes), extract ONLY the text of the marked option. Ignore unmarked options. If NONE are marked, return 'EMPTY'.

    7. If there are multiple handwritten values for a single field (e.g., date and signature), then use a delimiter '|' to seperate the values.

    8. If multiple mutually exclusive options (e.g., both Yes and No) are checked or crossed out, append the flag 'UNCLEAR' to the value.

    9. If a SINGLE CHECKLIST OPTION is not MARKED OR CHECKED, append the flag 'EMPTY' to the value.

    10 If a field includes a printed target ('Soll') value, add a new key-value pair by naming the field_name as 'Soll_<name of the value>'. If the document provides both a fixed number and a range for a 'Soll' value, PRIORITIZE extracting the range as the target value.

    11. If a chapter contains a multi-row table (e.g., an equipment list with columns like 'Anlagennummer'), DO NOT use just the column header as the field_name, or you will overwrite data.

    12. You MUST combine the Row Name (usually the first column) and the Column Header using a hyphen to create a unique field_name. Example: For row 'Oven A' and column 'Anlagennummer', the field_name MUST be exactly 'Oven A - Anlagennummer'.

    13. In multi-row tables, humans often write a single value (like a date, signature, or line) that visually spans across multiple rows to imply it applies to the entire block. If a handwritten value in a column is written only once but is sized or positioned to apply to the whole column, you MUST duplicate that exact value for EVERY row's composite key in that column. Do NOT assign it to just one row and leave the others 'EMPTY'. 

    14. In the first image, there is ALWAYS a 'Prozessstufe', 'SAP-Materialnummer' and 'Batch No.' fields. Combine only these three fields into a LIST of tableField with the chapter_id called 'Produktinfo'. Then SKIP the entire first page and move onto the next page.
    """
    
    generation_config = types.GenerateContentConfig(
        temperature=0.0, 
        response_mime_type="application/json",
        response_schema=PagePayload,
    )
    
    for index, page_image in enumerate(image_pages):
        page_num = index + 1
        print(f"Analyzing layout blocks on Page {page_num}...")
        
        if not contains_blue_handwriting(page_image):
            print(f"Skipping Page {page_num}: No blue handwriting detected by OpenCV.")
            continue
            
        print(f"Blue handwriting found. Sending Page {page_num} to Gemini OCR Layer...")

        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[prompt_instructions, page_image],
                config=generation_config
            )
            
            page_data = PagePayload.model_validate_json(response.text)
            
            for block in page_data.chapters:
                clean_key = block.chapter_id.strip()
                
                dict_format = {field.field_name: field.value for field in block.table_data}
                
                if clean_key in master_chapters_dataset:
                    master_chapters_dataset[clean_key].update(dict_format)
                else:

                    master_chapters_dataset[clean_key] = dict_format
                    
        except Exception as e:
            print(f"⚠️ Error reading Page {page_num}: {e}")
            continue
            
    return master_chapters_dataset

if __name__ == "__main__":
    print("Starting end-to-end local pipeline test")

    load_dotenv()

    API_KEY = os.getenv("GOOGLE_AI_API_KEY")

    test_pdf_path = r"C:\Users\JasonBS\Desktop\final_final_test.pdf"
    
    try:
        print("1. Running PDF to Image conversion")

        test_pages = convert_pdf_to_images(test_pdf_path, target_dpi=300)
        
        print("2. Pushing images into Gemini OCR Layer")
        parsed_results = extract_chapters_from_images(test_pages, api_key=API_KEY)
        
        print("Real Document Processing Mapping Complete:")

        print(json.dumps(parsed_results, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"\n❌ Pipeline integration failure: {e}")