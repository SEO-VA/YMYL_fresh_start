#!/usr/bin/env python3
"""
HTML Content Extractor for YMYL Audit Tool - FIXED VERSION
Extracts structured content directly from HTML strings with issue fixes
"""

import json
import re
from bs4 import BeautifulSoup
from typing import Tuple, Optional, List
from utils.helpers import safe_log

class HTMLContentExtractor:
    """Extracts structured content directly from HTML strings"""
    
    def __init__(self):
        """Initialize HTML extractor"""
        self.processed_elements = set()  # Track processed elements to avoid duplicates
        safe_log("HTMLContentExtractor initialized")
    
    def extract_content(self, html_content: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Extract structured content from HTML string
        
        Args:
            html_content: HTML content as string
            
        Returns:
            tuple: (success, organized_json_content, error_message)
        """
        try:
            safe_log(f"Starting HTML content extraction ({len(html_content):,} characters)")
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract structured content with fixes
            content_parts = self._extract_structured_content_fixed(soup)
            
            # Clean and deduplicate content
            content_parts = self._clean_and_deduplicate(content_parts)
            
            # Organize into H2-based chunks
            organized_content = self._organize_by_h2(content_parts)
            
            safe_log(f"HTML extraction successful: {len(organized_content):,} characters")
            return True, organized_content, None
            
        except Exception as e:
            error_msg = f"HTML parsing error: {str(e)}"
            safe_log(error_msg)
            return False, None, error_msg
    
    def _extract_structured_content_fixed(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract structured content with fixes for identified issues
        """
        content_parts = []
        self.processed_elements = set()
        
        # Extract H1 (only once)
        h1 = soup.find('h1')
        if h1 and id(h1) not in self.processed_elements:
            text = self._clean_text(h1.get_text(separator=' ', strip=True))
            if text:
                content_parts.append(f"H1: {text}")
                self.processed_elements.add(id(h1))
        
        # Extract subtitle and lead (skip if already processed)
        subtitle = soup.find('span', class_=['sub-title', 'd-block'])
        if subtitle and id(subtitle) not in self.processed_elements:
            text = self._clean_text(subtitle.get_text(separator=' ', strip=True))
            if text:
                content_parts.append(f"SUBTITLE: {text}")
                self.processed_elements.add(id(subtitle))
        
        lead = soup.find('p', class_='lead')
        if lead and id(lead) not in self.processed_elements:
            text = self._clean_text(lead.get_text(separator=' ', strip=True))
            if text:
                content_parts.append(f"LEAD: {text}")
                self.processed_elements.add(id(lead))
        
        # Process main content area
        article = soup.find('article')
        if article:
            # Remove tab-content sections
            for tab_content in article.find_all('div', class_='tab-content'):
                tab_content.decompose()
            
            # Process elements in order, avoiding duplicates
            for element in article.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'table', 'ul', 'ol', 'dl']):
                if id(element) not in self.processed_elements:
                    formatted_content = self._format_element_fixed(element)
                    if formatted_content:
                        content_parts.append(formatted_content)
                        self.processed_elements.add(id(element))
        else:
            # If no article tag, process body content directly
            body = soup.find('body') or soup
            for element in body.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'table', 'ul', 'ol', 'dl']):
                if id(element) not in self.processed_elements:
                    formatted_content = self._format_element_fixed(element)
                    if formatted_content:
                        content_parts.append(formatted_content)
                        self.processed_elements.add(id(element))
        
        # Extract special sections (avoid duplicates)
        faq_section = soup.find('section', attrs={'data-qa': 'templateFAQ'})
        if faq_section and id(faq_section) not in self.processed_elements:
            text = self._clean_text(faq_section.get_text(separator=' ', strip=True))
            if text:
                content_parts.append(f"FAQ: {text}")
                self.processed_elements.add(id(faq_section))
        
        author_section = soup.find('section', attrs={'data-qa': 'templateAuthorCard'})
        if author_section and id(author_section) not in self.processed_elements:
            text = self._clean_text(author_section.get_text(separator=' ', strip=True))
            if text:
                content_parts.append(f"AUTHOR: {text}")
                self.processed_elements.add(id(author_section))
        
        safe_log(f"Extracted {len(content_parts)} content elements from HTML")
        return content_parts
    
    def _format_element_fixed(self, element) -> Optional[str]:
        """
        Format individual HTML elements with fixes
        """
        tag_name = element.name.lower()
        
        # Handle headings with line break fixes
        if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            text = self._clean_text(element.get_text(separator=' ', strip=True))
            if not text:
                return None
            
            # Fix double H2 prefix issue
            prefix = tag_name.upper()
            if text.startswith(f"{prefix}:"):
                text = text[len(prefix)+1:].strip()
            
            return f"{prefix}: {text}"
        
        # Handle paragraphs
        elif tag_name == 'p':
            text = self._clean_text(element.get_text(separator=' ', strip=True))
            if not text:
                return None
            
            element_classes = element.get('class', [])
            if 'lead' in element_classes:
                return f"LEAD: {text}"
            else:
                return f"CONTENT: {text}"
        
        # Handle tables (improved to avoid duplication)
        elif tag_name == 'table':
            return self._format_table_fixed(element)
        
        # Handle lists
        elif tag_name in ['ul', 'ol']:
            return self._format_list_fixed(element)
        
        # Handle definition lists
        elif tag_name == 'dl':
            return self._format_definition_list_fixed(element)
        
        return None
    
    def _format_table_fixed(self, table) -> Optional[str]:
        """
        Format table with fixes to avoid content duplication
        """
        rows = []
        headers = []
        
        # Mark all table cells as processed to avoid duplicate extraction
        for cell in table.find_all(['td', 'th']):
            self.processed_elements.add(id(cell))
        
        # Try to identify headers
        header_row = table.find('tr')
        if header_row and header_row.find('th'):
            headers = [self._clean_text(th.get_text(strip=True)) for th in header_row.find_all('th')]
        
        # Process data rows
        data_rows = table.find_all('tr')
        start_idx = 1 if headers else 0
        
        for tr in data_rows[start_idx:]:
            cells = [self._clean_text(td.get_text(strip=True)) for td in tr.find_all(['td', 'th'])]
            if cells and any(cell for cell in cells):
                if headers and len(cells) == len(headers):
                    paired = [f"{h}: {v}" for h, v in zip(headers, cells) if v.strip()]
                    if paired:
                        rows.append(" | ".join(paired))
                else:
                    non_empty_cells = [cell for cell in cells if cell.strip()]
                    if non_empty_cells:
                        rows.append(" | ".join(non_empty_cells))
        
        if rows:
            return f"TABLE: {' // '.join(rows)}"
        return None
    
    def _format_list_fixed(self, list_element) -> Optional[str]:
        """
        Format lists with improved text cleaning
        """
        items = []
        list_type = "ORDERED" if list_element.name == 'ol' else "UNORDERED"
        
        # Mark list items as processed
        for li in list_element.find_all('li'):
            self.processed_elements.add(id(li))
        
        for li in list_element.find_all('li', recursive=False):
            text = self._clean_text(li.get_text(separator=' ', strip=True))
            if text:
                items.append(text)
        
        if items:
            return f"{list_type}_LIST: {' // '.join(items)}"
        return None
    
    def _format_definition_list_fixed(self, dl_element) -> Optional[str]:
        """
        Format definition lists with improved text cleaning
        """
        definitions = []
        current_term = None
        
        # Mark definition list elements as processed
        for elem in dl_element.find_all(['dt', 'dd']):
            self.processed_elements.add(id(elem))
        
        for element in dl_element.find_all(['dt', 'dd']):
            if element.name == 'dt':
                current_term = self._clean_text(element.get_text(strip=True))
            elif element.name == 'dd' and current_term:
                definition = self._clean_text(element.get_text(separator=' ', strip=True))
                if definition:
                    definitions.append(f"{current_term}: {definition}")
                current_term = None
        
        if definitions:
            return f"DEFINITION_LIST: {' // '.join(definitions)}"
        return None
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text to fix line break artifacts and formatting issues
        """
        if not text:
            return ""
        
        # Fix line break artifacts
        text = re.sub(r'\n+', ' ', text)  # Replace newlines with spaces
        text = re.sub(r'\s+', ' ', text)  # Collapse multiple spaces
        
        # Remove extra whitespace
        text = text.strip()
        
        # Fix common artifacts
        text = re.sub(r'([a-z])\n([a-z])', r'\1\2', text)  # Fix broken words
        
        return text
    
    def _clean_and_deduplicate(self, content_parts: List[str]) -> List[str]:
        """
        Clean content and remove duplicates
        """
        cleaned_parts = []
        seen_content = set()
        
        for part in content_parts:
            if not part or not part.strip():
                continue
            
            # Normalize for duplicate detection
            normalized = part.strip().lower()
            
            # Skip exact duplicates
            if normalized in seen_content:
                continue
            
            seen_content.add(normalized)
            cleaned_parts.append(part.strip())
        
        safe_log(f"Cleaned and deduplicated: {len(content_parts)} -> {len(cleaned_parts)} parts")
        return cleaned_parts
    
    def _organize_by_h2(self, content_parts: List[str]) -> str:
        """
        Organize content into H2-based chunks
        """
        big_chunks = []
        current_chunk = []
        chunk_index = 1
        
        for part in content_parts:
            # Start new chunk on H2
            if part.startswith('H2:'):
                # Save previous chunk if it exists
                if current_chunk:
                    big_chunks.append({
                        "big_chunk_index": chunk_index,
                        "small_chunks": current_chunk.copy()
                    })
                    chunk_index += 1
                
                # Start new chunk
                current_chunk = [part]
            else:
                # Add to current chunk
                current_chunk.append(part)
        
        # Add final chunk
        if current_chunk:
            big_chunks.append({
                "big_chunk_index": chunk_index,
                "small_chunks": current_chunk
            })
        
        # If no chunks created, put everything in one chunk
        if not big_chunks and content_parts:
            big_chunks = [{
                "big_chunk_index": 1,
                "small_chunks": content_parts
            }]
        
        # Create final JSON structure
        result = {
            "big_chunks": big_chunks
        }
        
        safe_log(f"Organized HTML content into {len(big_chunks)} chunks")
        return json.dumps(result, indent=2, ensure_ascii=False)


# Convenience function for external use
def extract_html_content(html_content: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Convenience function for extracting content from HTML string
    
    Args:
        html_content: HTML content as string
        
    Returns:
        tuple: (success, organized_json_content, error_message)
    """
    extractor = HTMLContentExtractor()
    return extractor.extract_content(html_content)
