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
        
        # Check if we have results
        if st.session_state.get('user_report') and st.session_state.get('user_word_bytes'):
            self._show_results()
        else:
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
    
    def _show_results(self):
        """Show results with markdown preview"""
        st.success("✅ **Analysis Complete!**")
        
        # Show markdown report
        st.markdown(st.session_state['user_report'])
        
        # Download button
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ymyl_report_{timestamp}.docx"
        
        st.download_button(
            label="📄 Download Word Report",
            data=st.session_state['user_word_bytes'],
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary"
        )
        
        # New analysis button
        if st.button("🔄 Analyze Another"):
            del st.session_state['user_report']
            del st.session_state['user_word_bytes']
            st.rerun()
    
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
            
            # Store results
            st.session_state['user_report'] = analysis_result['report']
            st.session_state['user_word_bytes'] = word_bytes
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            safe_log(f"Full analysis error: {e}")