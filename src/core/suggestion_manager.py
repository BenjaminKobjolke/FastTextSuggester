"""
Suggestion manager for the Screenshot OCR Tool
"""
import os
import re
from typing import List, Optional
import keyboard
import time


class SuggestionManager:
    """
    Manages text suggestions from OCR results.
    Provides functionality to extract words, find matches, and insert text.
    """

    def __init__(self, output_directory: str = "output"):
        """
        Initialize the suggestion manager.

        Args:
            output_directory: Directory containing OCR output files
        """
        self.output_directory = output_directory
        self.words = []
        self.phrases = []
        self.last_file = None

    def load_latest_ocr_file(self) -> bool:
        """
        Load the most recent OCR text file if it's not older than 1 minute.

        Returns:
            True if a recent file was loaded successfully, False otherwise
        """
        try:
            # Find the most recent file in the output directory
            if not os.path.exists(self.output_directory):
                return False

            files = [
                os.path.join(self.output_directory, f) 
                for f in os.listdir(self.output_directory) 
                if f.endswith('.txt')
            ]
            
            if not files:
                return False
                
            # Sort by modification time (newest first)
            files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            latest_file = files[0]
            
            # Check if the file is recent (less than 1 minute old)
            file_time = os.path.getmtime(latest_file)
            current_time = time.time()
            if (current_time - file_time) > 60:  # 60 seconds = 1 minute
                print(f"Most recent OCR file is too old ({int(current_time - file_time)} seconds)")
                return False
            
            self.last_file = latest_file
            
            # Parse the file
            return self._parse_ocr_file(self.last_file)
            
        except Exception as e:
            print(f"Error loading OCR file: {e}")
            return False

    def _parse_ocr_file(self, file_path: str) -> bool:
        """
        Parse an OCR text file to extract words and phrases.

        Args:
            file_path: Path to the OCR text file

        Returns:
            True if file was parsed successfully, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Reset collections
            self.words = []
            self.phrases = []
            
            # Extract words (split by whitespace and remove punctuation)
            words = re.findall(r'\b\w+\b', content)
            self.words = list(set(words))  # Remove duplicates
            
            # Extract email addresses and their components
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
            for email in emails:
                # Add the full email
                self.words.append(email)
                
                # Extract username part (before @)
                if '@' in email:
                    username = email.split('@')[0]
                    self.words.append(username)
                    
                    # Split username by common separators and add parts
                    username_parts = re.split(r'[._-]', username)
                    for part in username_parts:
                        if part and len(part) > 2:  # Only add parts with length > 2
                            self.words.append(part)
                
                # Extract domain part (after @)
                if '@' in email:
                    domain = email.split('@')[1]
                    self.words.append(domain)
                    
                    # Split domain by dots and add parts
                    domain_parts = domain.split('.')
                    for part in domain_parts:
                        if part and len(part) > 2 and part.lower() not in ['com', 'org', 'net', 'edu', 'gov', 'io']:
                            self.words.append(part)
            
            # Extract URLs
            # This pattern matches URLs starting with http:// or https:// and captures the domain and path
            urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[-\w%!./?=&+#~:;]*)*', content)
            for url in urls:
                # Clean the URL (remove trailing punctuation that might have been captured)
                clean_url = url.rstrip('.,;:\'\"')
                self.words.append(clean_url)
            
            # Extract phrases (2-4 word sequences)
            words_list = content.split()
            for i in range(len(words_list)):
                # Add 2-word phrases
                if i < len(words_list) - 1:
                    self.phrases.append(f"{words_list[i]} {words_list[i+1]}")
                # Add 3-word phrases
                if i < len(words_list) - 2:
                    self.phrases.append(f"{words_list[i]} {words_list[i+1]} {words_list[i+2]}")
                # Add 4-word phrases
                if i < len(words_list) - 3:
                    self.phrases.append(f"{words_list[i]} {words_list[i+1]} {words_list[i+2]} {words_list[i+3]}")
            
            return True
            
        except Exception as e:
            print(f"Error parsing OCR file: {e}")
            return False

    def get_suggestions(self, partial_text: str, max_results: int = 10) -> List[str]:
        """
        Get suggestions based on partial text input.

        Args:
            partial_text: The text to match against
            max_results: Maximum number of suggestions to return

        Returns:
            List of matching suggestions
        """
        if not partial_text:
            return []
            
        partial_text = partial_text.lower()
        
        # First, look for exact prefix matches in words
        prefix_word_matches = [word for word in self.words if word.lower().startswith(partial_text)]
        
        # Then look for exact prefix matches in phrases
        prefix_phrase_matches = [phrase for phrase in self.phrases if phrase.lower().startswith(partial_text)]
        
        # Then look for substring matches in words (not starting with partial_text)
        substring_word_matches = [
            word for word in self.words 
            if partial_text in word.lower() and not word.lower().startswith(partial_text)
        ]
        
        # Then look for substring matches in phrases (not starting with partial_text)
        substring_phrase_matches = [
            phrase for phrase in self.phrases 
            if partial_text in phrase.lower() and not phrase.lower().startswith(partial_text)
        ]
        
        # Combine results with priority order: prefix matches first, then substring matches
        all_matches = prefix_word_matches + prefix_phrase_matches + substring_word_matches + substring_phrase_matches
        
        # Remove duplicates while preserving order
        unique_matches = []
        for match in all_matches:
            if match not in unique_matches:
                unique_matches.append(match)
        
        return unique_matches[:max_results]

    def insert_text(self, text: str) -> None:
        """
        Insert text into the active application.

        Args:
            text: Text to insert
        """
        if not text:
            return
            
        # Use keyboard library to type the text
        keyboard.write(text)
        time.sleep(0.1)  # Small delay to ensure text is inserted
