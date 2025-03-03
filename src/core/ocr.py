"""
OCR processing functionality for the Screenshot OCR Tool
"""
import os
from typing import Dict, Any, Optional

# We'll use pytesseract for OCR
import pytesseract
from PIL import Image


class OCRProcessor:
    """
    Handles OCR processing of screenshots.
    """

    def __init__(self, ocr_settings: Optional[Dict[str, Any]] = None):
        """
        Initialize the OCR processor.

        Args:
            ocr_settings: Dictionary of OCR settings
        """
        self.settings = ocr_settings or {
            "language": "eng",
            "optimize": True
        }

    def process_image(self, image_path: str) -> str:
        """
        Process an image with OCR.

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text from the image
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Load the image
        image = Image.open(image_path)
        
        # Apply optimizations if enabled
        if self.settings.get("optimize", True):
            image = self._optimize_image(image)
        
        # Perform OCR
        config = f"-l {self.settings.get('language', 'eng')} --psm 6"
        text = pytesseract.image_to_string(image, config=config)
        
        return text

    def _optimize_image(self, image: Image.Image) -> Image.Image:
        """
        Apply optimizations to improve OCR accuracy.

        Args:
            image: PIL Image object

        Returns:
            Optimized PIL Image object
        """
        # Convert to grayscale
        image = image.convert('L')
        
        # You can add more optimizations here as needed
        # For example:
        # - Increase contrast
        # - Apply thresholding
        # - Remove noise
        # - Resize image
        
        return image

    def save_text_to_file(self, text: str, output_path: str) -> None:
        """
        Save extracted text to a file.

        Args:
            text: Extracted text
            output_path: Path to save the text file
        """
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write the text to the file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
