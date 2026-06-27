import os
from pdf2image import convert_from_path

def convert_pdf_to_images(pdf_path: str, target_dpi: int = 300):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"The specified PDF file does not exist: {pdf_path}")
    
    print(f"PDF found, starting conversion of {pdf_path} to images")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../.."))
    poppler_path = os.path.join(project_root, "poppler-26.02.0", "Library", "bin")

    pages = convert_from_path(
        pdf_path,
        dpi = target_dpi,
        fmt = "jpeg",
        poppler_path = poppler_path
    )

    print("Successfully converted PDF to images")

    return pages

if __name__ == "__main__":
    pdf_path = r"your path" 
    try:
        images = convert_pdf_to_images(pdf_path)
        print(f"Converted {len(images)} pages to images.")
    except Exception as e:
        print(f"An error occurred: {e}")