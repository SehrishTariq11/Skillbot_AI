import cv2
import pandas as pd
from paddleocr import PaddleOCR

# Initialize PaddleOCR once (CPU only)
ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)


def preprocess_image(image_path):
    """
    Load and preprocess image for OCR
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Apply thresholding if needed
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    return img, thresh


def extract_text(img):
    """
    Extract text from image using PaddleOCR
    """
    if img is None:
        raise ValueError("Image is empty or could not be loaded.")
    
    result = ocr.ocr(img)
    text_list = []
    for line in result[0]:
        text = line[1][0]  # text string
        text_list.append(text)
    return text_list


def extract_marks_from_marksheet(image_path):
    """
    Complete marksheet OCR -> returns pandas DataFrame
    """
    # Preprocess
    img, thresh = preprocess_image(image_path)
    
    # OCR
    text_list = extract_text(img)
    
    # Extract marks data from text_list
    # Here, we assume text_list has structure like: ["URDU", "150", "131", ...]
    subjects = []
    max_marks = []
    obtained = []

    i = 0
    while i < len(text_list):
        try:
            subject = text_list[i]
            max_mark = int(text_list[i + 1])
            obtained_mark = int(text_list[i + 2])
            subjects.append(subject)
            max_marks.append(max_mark)
            obtained.append(obtained_mark)
            i += 3
        except (IndexError, ValueError):
            # Skip if the format is not correct
            i += 1

    df = pd.DataFrame({
        "Subject": subjects,
        "Maximum": max_marks,
        "Obtained": obtained
    })
    return df
