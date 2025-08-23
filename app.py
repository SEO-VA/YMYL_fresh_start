#!/usr/bin/env python3
"""
URL Analysis Feature for YMYL Audit Tool
Handles URL-based content analysis
"""

import streamlit as st
from typing import Dict, Any, Tuple, Optional
from features.base_feature import BaseAnalysisFeature
from core.extractor import extract_url_content
from utils.helpers import validate_url, safe_log

class URLAnalysisFeature(BaseAnalysisFeature):
    """Feature for analyzing content from web URLs"""
    
    def get_feature_name(self) -> str:
        """Get display name for this feature"""
        return "URL Analysis"
    
    def get_input_interface(self) -> Dict[str, Any]:
        """Render simple URL input interface"""
        
        # URL input
        url = st.text_input(
            "**Enter URL:**",
            placeholder="https://example.com/page",
            key=self.get_session_key("url_input")
        )
        
        # Casino mode toggle
        casino_mode = self.show_casino_mode_toggle()
        
        # Simple validation
        is_valid = bool(url and url.strip() and validate_url(url.strip()))
        
        if url and not is_valid:
            st.error("❌ Please enter a valid URL")
        
        return {
            'url': url.strip() if url else "",
            'casino_mode': casino_mode,
            'is_valid': is_valid,
            'error_message': "" if is_valid else "Valid URL required"
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate URL input"""
        url = input_data.get('url', '').strip()
        
        if not url:
            return False, "URL is required"
        
        if not validate_url(url):
            return False, "Invalid URL format"
        
        return True, ""
    
    def extract_content(self, input_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        """Extract content from URL"""
        url = input_data['url']
        
        safe_log(f"Starting URL content extraction from: {url}")
        
        try:
            # Use existing extractor
            success, extracted_content, error = extract_url_content(url)
            
            if success:
                safe_log(f"URL extraction successful: {len(extracted_content):,} characters")
                return True, extracted_content, None
            else:
                safe_log(f"URL extraction failed: {error}")
                return False, None, error
                
        except Exception as e:
            error_msg = f"Unexpected error during URL extraction: {str(e)}"
            safe_log(error_msg)
            return False, None, error_msg
    
    def show_extraction_preview(self, extracted_content: str, url: str, is_admin: bool = False):
        """Show extraction preview for URL analysis"""
        if is_admin:
            self._show_admin_preview(extracted_content, url)
        else:
            # Simple preview for regular users
            st.info(f"💡 Content ready for AI analysis from: **{url}**")
    
    def _show_admin_preview(self, extracted_content: str, url: str):
        """Show detailed admin preview"""
        st.markdown("### 🔍 Admin: Extraction Details")
        
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
    
    def get_progress_steps(self) -> list:
        """Get URL-specific progress steps"""
        return [
            "Connecting to URL",
            "Downloading content",
            "Parsing HTML structure", 
            "Extracting text content",
            "Organizing by sections"
        ]
    
    def get_source_description(self, input_data: Dict[str, Any]) -> str:
        """Get description of the content source"""
        url = input_data.get('url', '')
        try:
            from utils.helpers import extract_domain
            domain = extract_domain(url)
            return f"URL: {domain}" if domain else f"URL: {url}"
        except Exception:
            return f"URL: {url}"
