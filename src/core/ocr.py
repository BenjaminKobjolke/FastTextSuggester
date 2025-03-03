"""
OCR processing functionality for the Screenshot OCR Tool
"""
import os
import time
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
            
    def cleanup_old_files(self, output_dir: str, max_age_hours: int = 1) -> None:
        """
        Delete files older than the specified age from the output directory.
        
        Args:
            output_dir: Directory containing files to clean up
            max_age_hours: Maximum age of files in hours (default: 1)
        """
        if not os.path.exists(output_dir):
            return
            
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        # Get all files in the output directory
        for filename in os.listdir(output_dir):
            filepath = os.path.join(output_dir, filename)
            
            # Skip directories
            if os.path.isdir(filepath):
                continue
                
            # Check if the file is a screenshot or text file
            if filename.endswith('.png') or filename.endswith('.txt'):
                # Check file age
                file_time = os.path.getmtime(filepath)
                age_seconds = current_time - file_time
                
                # Delete if older than max age
                if age_seconds > max_age_seconds:
                    try:
                        os.remove(filepath)
                        print(f"Deleted old file: {filename}")
                    except Exception as e:
                        print(f"Error deleting file {filename}: {e}")
