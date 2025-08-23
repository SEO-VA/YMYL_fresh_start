#!/usr/bin/env python3
"""
User Layout for YMYL Audit Tool
Handles simple one-step process for regular users
"""

import streamlit as st
import asyncio
import concurrent.futures
from datetime import datetime
from typing import Dict, Any
from utils.feature_registry import FeatureRegistry
from core.analyzer import analyze_content
from core.reporter import generate_word_report
from utils.helpers import safe_log

class UserLayout:
    """Simple user layout with one-step process"""
    
    def render(self, selected_feature: str):
        """Render user interface for selected feature"""
        
        # Get feature handler
        try:
            feature_handler = FeatureRegistry.get_handler(selected_feature)
        except ValueError as e:
            st.error(f"❌ {str(e)}")
            return
        
        # Main content
        self._render_analysis_interface(feature_handler)
    
    def _render_analysis_interface(self, feature_handler):
        """Render simple analysis interface"""
        
        # Get input interface
        input_data = feature_handler.get_input_interface()
        
        # Single analyze button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            analyze_clicked = st.button(
                "🚀 Analyze Content",
                type="primary",
                use_container_width=True,
                disabled=not input_data.get('is_valid', False)
            )
        
        # Process full analysis
        if analyze_clicked:
            self._process_full_analysis(feature_handler, input_data)
    
    def _process_full_analysis(self, feature_handler, input_data: Dict[str, Any]):
        """Process complete analysis in one step"""
        
        try:
            # Step 1: Content Extraction
            with st.status("Extracting content...") as status:
                # Validate input
                is_valid, error_msg = feature_handler.validate_input(input_data)
                if not is_valid:
                    st.error(f"❌ Validation failed: {error_msg}")
                    return
                
                # Extract content
                success, extracted_content, error = feature_handler.extract_content(input_data)
                
                if not success:
                    st.error(f"❌ Extraction failed: {error}")
                    return
                
                status.update(label="Content extracted, running AI analysis...", state="running")
                
                # Step 2: AI Analysis
                casino_mode = input_data.get('casino_mode', False)
                
                async def run_analysis():
                    return await analyze_content(extracted_content, casino_mode)
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(lambda: asyncio.run(run_analysis()))
                    analysis_result = future.result(timeout=300)
                
                if not analysis_result or not analysis_result.get('success'):
                    error_msg = analysis_result.get('error', 'Unknown error')
                    st.error(f"❌ AI analysis failed: {error_msg}")
                    return
                
                status.update(label="Generating Word report...", state="running")
                
                # Step 3: Generate Report
                source_info = feature_handler.get_source_description(input_data)
                word_bytes = generate_word_report(
                    analysis_result['report'],
                    f"YMYL Report - {source_info}",
                    casino_mode
                )
                
                status.update(label="✅ Analysis complete!", state="complete")
            
            # Show results
            self._show_simple_results(analysis_result, word_bytes, source_info)
            
        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            safe_log(f"Full analysis error: {e}")
    
    def _show_simple_results(self, analysis_result: Dict[str, Any], 
                           word_bytes: bytes, source_info: str):
        """Show simple results for regular users"""
        
        st.success("✅ **Analysis Complete!**")
        
        # Simple summary
        ai_response = analysis_result.get('ai_response', [])
        if isinstance(ai_response, list):
            violations_found = sum(1 for section in ai_response 
                                 if section.get('violations') != "no violation found" 
                                 and section.get('violations'))
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Sections Analyzed", len(ai_response))
            with col2:
                if violations_found > 0:
                    st.metric("Violations Found", violations_found, delta=f"in {violations_found} sections")
                else:
                    st.metric("Violations Found", 0, delta="All clear!")
        
        # Download section
        st.markdown("### 📄 Download Your Report")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ymyl_report_{timestamp}.docx"
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.download_button(
                label="📄 Download Word Report",
                data=word_bytes,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                use_container_width=True
            )
        
        # Tips
        st.info("💡 **Tip**: The Word document imports perfectly into Google Docs!")
        
        # New analysis button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔄 Analyze Another", use_container_width=True):
                # Clear all feature session data
                keys_to_remove = [k for k in st.session_state.keys() 
                                if any(k.startswith(prefix) for prefix in 
                                      ['url_analysis_', 'html_analysis_'])]
                for key in keys_to_remove:
                    del st.session_state[key]
                st.rerun()
