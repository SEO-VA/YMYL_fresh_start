#!/usr/bin/env python3
"""
HTML Analysis Feature for YMYL Audit Tool
Handles HTML file and ZIP archive content analysis
"""

import streamlit as st
import zipfile
import io
from typing import Dict, Any, Tuple, Optional
from features.base_feature import BaseAnalysisFeature
from core.html_extractor import extract_html_content
from utils.helpers import safe_log

class HTMLAnalysisFeature(BaseAnalysisFeature):
    """Feature for analyzing content from HTML files or ZIP archives"""
    
    def get_feature_name(self) -> str:
        """Get display name for this feature"""
        return "HTML Analysis"
    
    def get_input_interface(self) -> Dict[str, Any]:
        """Render HTML input interface"""
        st.subheader("📄 HTML Analysis")
        
        # Input method selection
        col1, col2 = st.columns([2, 1])
        
        with col1:
            input_method = st.selectbox(
                "Choose input method:",
                ["📝 Paste HTML directly", "📁 Upload ZIP file with HTML"],
                key=self.get_session_key("input_method")
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            casino_mode = self.show_casino_mode_toggle()
        
        # Input interface based on method
        input_data = {'casino_mode': casino_mode, 'input_method': input_method}
        
        if input_method == "📝 Paste HTML directly":
            input_data.update(self._render_html_paste_interface())
        else:
            input_data.update(self._render_zip_upload_interface())
        
        return input_data
    
    def _render_html_paste_interface(self) -> Dict[str, Any]:
        """Render HTML paste interface"""
        st.markdown("**Paste HTML Content:**")
        
        html_content = st.text_area(
            "HTML Content:",
            height=200,
            placeholder="<html><head><title>Your content...</title></head><body>...</body></html>",
            help="Paste the complete HTML document here",
            key=self.get_session_key("html_content")
        )
        
        # Validation
        is_valid = bool(html_content and html_content.strip())
        error_message = ""
        
        if html_content and not self._is_valid_html(html_content):
            is_valid = False
            error_message = "HTML content appears to be invalid or incomplete"
            st.warning("⚠️ " + error_message)
        
        return {
            'html_content': html_content.strip() if html_content else "",
            'is_valid': is_valid,
            'error_message': error_message,
            'source_type': 'html_paste'
        }
    
    def _render_zip_upload_interface(self) -> Dict[str, Any]:
        """Render ZIP upload interface"""
        st.markdown("**Upload ZIP Archive:**")
        
        uploaded_file = st.file_uploader(
            "Select ZIP file:",
            type=['zip'],
            help="ZIP must contain exactly one HTML file",
            key=self.get_session_key("zip_file")
        )
        
        # Validation
        is_valid = uploaded_file is not None
        error_message = ""
        html_content = ""
        
        if uploaded_file:
            # Validate ZIP file
            try:
                zip_bytes = uploaded_file.getvalue()
                is_valid, html_content, error_message = self._validate_zip_file(zip_bytes)
                
                if not is_valid:
                    st.error(f"❌ {error_message}")
                else:
                    st.success(f"✅ Valid ZIP file with HTML content ({len(html_content):,} characters)")
                    
            except Exception as e:
                is_valid = False
                error_message = f"Error reading ZIP file: {str(e)}"
                st.error(f"❌ {error_message}")
        
        return {
            'zip_file': uploaded_file,
            'html_content': html_content,
            'is_valid': is_valid,
            'error_message': error_message,
            'source_type': 'zip_upload'
        }
    
    def _is_valid_html(self, html_content: str) -> bool:
        """Basic HTML validation"""
        if not html_content or len(html_content.strip()) < 10:
            return False
        
        html_lower = html_content.lower().strip()
        
        # Check for basic HTML structure
        has_html_tag = '<html' in html_lower and '</html>' in html_lower
        has_body_tag = '<body' in html_lower and '</body>' in html_lower
        has_content = len(html_content.strip()) > 50
        
        return has_html_tag or has_body_tag or has_content
    
    def _validate_zip_file(self, zip_bytes: bytes) -> Tuple[bool, str, str]:
        """Validate ZIP file and extract HTML content"""
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zip_file:
                # Get file list
                file_list = zip_file.namelist()
                
                # Filter HTML files
                html_files = [f for f in file_list 
                             if f.lower().endswith(('.html', '.htm')) 
                             and not f.startswith('__MACOSX/')]
                
                if len(html_files) == 0:
                    return False, "", "No HTML files found in ZIP archive"
                
                if len(html_files) > 1:
                    return False, "", f"Multiple HTML files found ({len(html_files)}). ZIP must contain exactly one HTML file"
                
                # Extract HTML content
                html_file = html_files[0]
                html_content = zip_file.read(html_file).decode('utf-8', errors='ignore')
                
                # Validate HTML content
                if not self._is_valid_html(html_content):
                    return False, "", "HTML file contains invalid or incomplete content"
                
                # Check size
                if len(html_content) > 5 * 1024 * 1024:  # 5MB limit
                    return False, "", f"HTML file too large: {len(html_content):,} characters (max: 5MB)"
                
                return True, html_content, ""
                
        except zipfile.BadZipFile:
            return False, "", "Invalid or corrupted ZIP file"
        except UnicodeDecodeError:
            return False, "", "HTML file contains invalid character encoding"
        except Exception as e:
            return False, "", f"Error processing ZIP file: {str(e)}"
    
    def validate_input(self, input_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate HTML input"""
        html_content = input_data.get('html_content', '').strip()
        
        if not html_content:
            return False, "HTML content is required"
        
        if len(html_content) < 10:
            return False, "HTML content is too short"
        
        if len(html_content) > 5 * 1024 * 1024:  # 5MB limit
            return False, f"HTML content is too large: {len(html_content):,} characters (max: 5MB)"
        
        if not self._is_valid_html(html_content):
            return False, "HTML content appears to be invalid"
        
        return True, ""
    
    def extract_content(self, input_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        """Extract content from HTML"""
        html_content = input_data['html_content']
        source_type = input_data.get('source_type', 'unknown')
        
        safe_log(f"Starting HTML content extraction ({source_type}, {len(html_content):,} chars)")
        
        try:
            # Use HTML extractor
            success, extracted_content, error = extract_html_content(html_content)
            
            if success:
                safe_log(f"HTML extraction successful: {len(extracted_content):,} characters")
                return True, extracted_content, None
            else:
                safe_log(f"HTML extraction failed: {error}")
                return False, None, error
                
        except Exception as e:
            error_msg = f"Unexpected error during HTML extraction: {str(e)}"
            safe_log(error_msg)
            return False, None, error_msg
    
    def get_progress_steps(self) -> list:
        """Get HTML-specific progress steps"""
        return [
            "Validating HTML content",
            "Parsing HTML structure", 
            "Extracting text content",
            "Processing tables and lists",
            "Organizing by sections"
        ]
    
    def get_source_description(self, input_data: Dict[str, Any]) -> str:
        """Get description of the content source"""
        source_type = input_data.get('source_type', 'unknown')
        
        if source_type == 'html_paste':
            return "HTML (pasted content)"
        elif source_type == 'zip_upload':
            zip_file = input_data.get('zip_file')
            if zip_file:
                return f"ZIP: {zip_file.name}"
            return "ZIP file"
        else:
            return "HTML content"
    
    def show_extraction_preview(self, extracted_content: str, source_info: str, is_admin: bool = False):
        """Show extraction preview for HTML analysis"""
        if is_admin:
            self._show_admin_preview(extracted_content, source_info)
        else:
            # Simple preview for regular users
            st.info(f"💡 Content ready for AI analysis from: **{source_info}**")
    
    def _show_admin_preview(self, extracted_content: str, source_info: str):
        """Show detailed admin preview"""
        st.markdown("### 🔍 Admin: HTML Extraction Details")
        
        # Get metrics
        metrics = self.get_extraction_metrics(extracted_content)
        
        # Show metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Big Chunks", metrics.get('big_chunks', 'N/A'))
        with col2:
            st.metric("Small Chunks", metrics.get('small_chunks', 'N/A'))
        with col3:
            st.metric("JSON Size", f"{metrics.get('json_size', 0):,} chars")
        
        # Content preview
        with st.expander("👁️ View Extracted Content Structure"):
            try:
                import json
                content_data = json.loads(extracted_content)
                big_chunks = content_data.get('big_chunks', [])
                
                for i, chunk in enumerate(big_chunks, 1):
                    st.markdown(f"**📦 Big Chunk {i}:**")
                    small_chunks = chunk.get('small_chunks', [])
                    
                    for j, small_chunk in enumerate(small_chunks[:3], 1):
                        preview = small_chunk[:150] + "..." if len(small_chunk) > 150 else small_chunk
                        st.text(f"  {j}. {preview}")
                    
                    if len(small_chunks) > 3:
                        st.text(f"  ... and {len(small_chunks) - 3} more chunks")
                    st.markdown("---")
                    
            except json.JSONDecodeError:
                st.error("Could not parse extracted JSON")
        
        # Raw JSON preview
        with st.expander("🤖 JSON Data Sent to AI"):
            st.code(extracted_content, language='json')
