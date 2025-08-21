"""
Suggestion manager for the Screenshot OCR Tool
"""
import os
import re
from typing import List, Optional, Dict, Set
from pynput.keyboard import Controller
import time


class SuggestionManager:
    """
    Manages text suggestions from OCR results.
    Provides functionality to extract words, find matches, and insert text.
    """

    def __init__(self, output_directory: str = "output", data_directory: str = "data"):
        """
        Initialize the suggestion manager.

        Args:
            output_directory: Directory containing OCR output files
            data_directory: Directory containing data files for suggestions
        """
        self.output_directory = output_directory
        self.data_directory = data_directory
        self.words = []
        self.phrases = []
        self.lines = []  # Store complete lines from _line.txt files
        self.blocks = {}  # Store multi-line blocks from _separator.txt files (first_line -> full_block)
        self.last_file = None
        
        # Load data files at initialization
        self.load_data_files()

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
                #p rint(f"Most recent OCR file is too old ({int(current_time - file_time)} seconds)")
                return False
            
            self.last_file = latest_file
            
            # Parse the file - check if it's a line-based file
            if self.last_file.endswith('_line.txt'):
                # For _line.txt files, store complete lines
                return self._parse_line_file(self.last_file)
            else:
                # For regular text files, extract words and phrases
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
                
            # Reset collections (but preserve lines from data files)
            self.words = []
            self.phrases = []
            
            # Extract words (split by whitespace and remove punctuation)
            words = re.findall(r'\b\w+\b', content)
            self.words = list(set(words))  # Remove duplicates
            
            # Extract email addresses and their components
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
            for email in emails:
                # Add the full email (highest priority)
                self.words.append(email)
                
                # Extract username part (before @)
                if '@' in email:
                    username = email.split('@')[0]
                    
                    # Add the full username (second priority)
                    self.words.append(username)
                    
                    # Add username with @ and domain (for partial matches)
                    if '.' in username:
                        # For emails like frank.schnepf@domain.com, add frank@domain.com
                        parts = username.split('.')
                        if len(parts) > 1:
                            for i in range(len(parts)):
                                partial_username = parts[i]
                                if partial_username and len(partial_username) > 1:
                                    self.words.append(f"{partial_username}@{email.split('@')[1]}")
                    
                    # Split username by common separators and add parts (lowest priority)
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

    def load_data_files(self) -> bool:
        """
        Load text files from the data directory.
        Files ending with _line.txt will have their lines stored separately.

        Returns:
            True if any files were loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(self.data_directory):
                print(f"Data directory {self.data_directory} does not exist")
                return False

            # Clear existing data collections to avoid duplicates when reloading
            self.words = []
            self.phrases = []
            self.lines = []
            self.blocks = {}

            # Get all text, TSV, and CSV files in the data directory
            files = [
                os.path.join(self.data_directory, f) 
                for f in os.listdir(self.data_directory) 
                if f.endswith('.txt') or f.endswith('.tsv') or f.endswith('.csv')
            ]
            
            if not files:
                print(f"No text, TSV, or CSV files found in {self.data_directory}")
                return False
            
            # Process each file
            for file_path in files:
                if file_path.endswith('.tsv'):
                    # For TSV files, extract all values
                    self._parse_tsv_file(file_path)
                elif file_path.endswith('.csv'):
                    # For CSV files, extract all values
                    self._parse_csv_file(file_path)
                elif file_path.endswith('_separator.txt'):
                    # For _separator.txt files, store multi-line blocks
                    self._parse_separator_file(file_path)
                elif file_path.endswith('_line.txt'):
                    # For _line.txt files, store complete lines
                    self._parse_line_file(file_path)
                else:
                    # For regular text files, extract words and phrases
                    self._parse_data_file(file_path)
            
            return True
            
        except Exception as e:
            print(f"Error loading data files: {e}")
            return False
    
    def _parse_line_file(self, file_path: str) -> bool:
        """
        Parse a _line.txt file to extract complete lines.

        Args:
            file_path: Path to the line text file

        Returns:
            True if file was parsed successfully, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read all lines and strip whitespace
                lines = [line.strip() for line in f.readlines() if line.strip()]
                
                # Add lines to the collection (avoid duplicates)
                for line in lines:
                    if line not in self.lines:
                        self.lines.append(line)
            
            return True
            
        except Exception as e:
            print(f"Error parsing line file {file_path}: {e}")
            return False
    
    def _parse_tsv_file(self, file_path: str) -> bool:
        """
        Parse a TSV file to extract individual values.
        
        Args:
            file_path: Path to the TSV file
            
        Returns:
            True if file was parsed successfully, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read all lines
                for line in f:
                    # Skip empty lines
                    if not line.strip():
                        continue
                        
                    # Split by tabs
                    values = line.strip().split('\t')
                    
                    # Add each value to words collection
                    for value in values:
                        value = value.strip()
                        if value and value not in self.words:
                            self.words.append(value)
            
            return True
            
        except Exception as e:
            print(f"Error parsing TSV file {file_path}: {e}")
            return False
    
    def _parse_csv_file(self, file_path: str) -> bool:
        """
        Parse a CSV file to extract individual values.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            True if file was parsed successfully, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read all lines
                for line in f:
                    # Skip empty lines
                    if not line.strip():
                        continue
                        
                    # Split by commas
                    values = line.strip().split(',')
                    
                    # Add each value to words collection
                    for value in values:
                        value = value.strip()
                        if value and value not in self.words:
                            self.words.append(value)
            
            return True
            
        except Exception as e:
            print(f"Error parsing CSV file {file_path}: {e}")
            return False
    
    def _parse_separator_file(self, file_path: str) -> bool:
        """
        Parse a _separator.txt file to extract multi-line blocks separated by ||.
        
        Args:
            file_path: Path to the separator text file
            
        Returns:
            True if file was parsed successfully, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split content by || separator
            blocks = content.split('||')
            
            # Process each block
            for block in blocks:
                # Strip whitespace and skip empty blocks
                block = block.strip()
                if not block:
                    continue
                
                # Get the first line as the key for display
                lines = block.split('\n')
                first_line = lines[0].strip() if lines else ''
                
                if first_line:
                    # Store the full block with first line as key
                    # If there are duplicate first lines, append a counter
                    key = first_line
                    counter = 1
                    while key in self.blocks:
                        counter += 1
                        key = f"{first_line} ({counter})"
                    
                    self.blocks[key] = block
            
            return True
            
        except Exception as e:
            print(f"Error parsing separator file {file_path}: {e}")
            return False
    
    def _parse_data_file(self, file_path: str) -> bool:
        """
        Parse a regular data text file to extract words and phrases.

        Args:
            file_path: Path to the data text file

        Returns:
            True if file was parsed successfully, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract words (split by whitespace and remove punctuation)
            words = re.findall(r'\b\w+\b', content)
            
            # Add words to the collection (avoid duplicates)
            for word in words:
                if word not in self.words:
                    self.words.append(word)
            
            # Extract phrases (2-4 word sequences)
            words_list = content.split()
            for i in range(len(words_list)):
                # Add 2-word phrases
                if i < len(words_list) - 1:
                    phrase = f"{words_list[i]} {words_list[i+1]}"
                    if phrase not in self.phrases:
                        self.phrases.append(phrase)
                # Add 3-word phrases
                if i < len(words_list) - 2:
                    phrase = f"{words_list[i]} {words_list[i+1]} {words_list[i+2]}"
                    if phrase not in self.phrases:
                        self.phrases.append(phrase)
                # Add 4-word phrases
                if i < len(words_list) - 3:
                    phrase = f"{words_list[i]} {words_list[i+1]} {words_list[i+2]} {words_list[i+3]}"
                    if phrase not in self.phrases:
                        self.phrases.append(phrase)
            
            return True
            
        except Exception as e:
            print(f"Error parsing data file {file_path}: {e}")
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
        
        # First, look for block matches (highest priority)
        # Search within the entire block content, but only return the first line (key)
        block_matches = []
        for key, block in self.blocks.items():
            if partial_text in block.lower():
                block_matches.append(key)
        
        # Then, look for line matches (second highest priority)
        line_matches = [
            line for line in self.lines 
            if partial_text in line.lower()
        ]
        
        # Special handling for email-like inputs (contains @ or .)
        email_matches = []
        if '@' in partial_text or '.' in partial_text:
            email_matches = [
                word for word in self.words 
                if '@' in word and partial_text in word.lower()
            ]
        
        # Then, look for exact prefix matches in words
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
        
        # Combine results with priority order: 
        # blocks first, then lines, then email matches, then prefix matches, then substring matches
        all_matches = block_matches + line_matches + email_matches + prefix_word_matches + prefix_phrase_matches + substring_word_matches + substring_phrase_matches
        
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
        
        # Check if the text is a key in our blocks dictionary
        # If so, insert the full block instead of just the first line
        if text in self.blocks:
            text_to_insert = self.blocks[text]
        else:
            text_to_insert = text
            
        # Add a longer delay before inserting text to ensure focus is properly restored
        time.sleep(.1)  # Increased delay to ensure focus is stable
            
        # Use pynput to type the text
        keyboard = Controller()
        keyboard.type(text_to_insert)
