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
        
        # Perform OCR with optimized configuration
        # Use both German and English languages, and LSTM OCR Engine only (faster)
        config = f"-l deu+eng --psm 6 --oem 1"
        text = pytesseract.image_to_string(image, config=config)
        
        return text

    def _optimize_image(self, image: Image.Image) -> Image.Image:
        """
        Apply optimizations to improve OCR accuracy without resizing.

        Args:
            image: PIL Image object

        Returns:
            Optimized PIL Image object
        """
        try:
            # Convert to grayscale
            image = image.convert('L')
            
            # Increase contrast
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)  # Enhance contrast by 50%
            
            # Apply auto-level to improve text visibility
            from PIL import ImageOps
            image = ImageOps.autocontrast(image, cutoff=0.5)
            
            return image
            
        except Exception as e:
            # If any optimization fails, return the original image
            print(f"Image optimization error: {e}")
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
