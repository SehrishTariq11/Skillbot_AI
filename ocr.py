# ocr.py
import cv2
import pandas as pd
from paddleocr import PaddleOCR

# Initialize PaddleOCR (English, no GPU required)
ocr = PaddleOCR(use_angle_cls=True, lang='en')

def preprocess_image(image_path):
    """
    Reads an image and converts it to grayscale with thresholding.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Optional: apply thresholding to improve OCR
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    return img, thresh

def extract_text(img):
    """
    Extracts text from a preprocessed image using PaddleOCR.
    """
    result = ocr.ocr(img, cls=True)
    text_list = []
    for line in result:
        for word_info in line:
            text_list.append(word_info[-1][0])
    return text_list

def extract_marks_from_marksheet(image_path, output_csv=None):
    """
    Extracts marks from a marksheet image and returns a DataFrame.
    """
    img, thresh = preprocess_image(image_path)
    text_list = extract_text(thresh)

    # Simple parser: looks for lines with Subject and Marks
    subjects = []
    obtained_marks = []
    max_marks = []

    for i, text in enumerate(text_list):
        # Naive parsing: adjust based on your marksheet format
        if text.strip().isdigit() and i >= 1:
            try:
                obtained_marks.append(int(text.strip()))
                subjects.append(text_list[i-1])
                max_marks.append(100)  # default max marks, adjust if needed
            except:
                continue

    df = pd.DataFrame({
        "Subject": subjects,
        "Obtained": obtained_marks,
        "Maximum": max_marks
    })

    if output_csv:
        df.to_csv(output_csv, index=False)

    return df
