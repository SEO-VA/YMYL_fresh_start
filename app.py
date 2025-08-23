#!/usr/bin/env python3
"""
YMYL Audit Tool - Simplified Version
Main Streamlit application with clean, future-ready architecture
"""

import streamlit as st
import time
import asyncio
from datetime import datetime

# Import our modular components
from core.auth import check_authentication, logout
from core.extractor import extract_url_content
from core.analyzer import analyze_content
from core.reporter import generate_word_report
from ui.components import (
    create_header,
    create_url_input,
    create_fake_progress,
    create_results_display
)
from utils.helpers import safe_log

# Configure Streamlit page
st.set_page_config(
    page_title="YMYL Audit Tool - Simplified",
    page_icon="🔍",
    layout="wide"
)

def main():
    """Main application function"""
    
    # Check authentication first
    if not check_authentication():
        return
    
    # Create page header
    create_header()
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # URL input section
        url, casino_mode, analyze_clicked = create_url_input()
        
        # Process analysis if requested
        if analyze_clicked and url:
            process_analysis(url, casino_mode)
    
    with col2:
        # Logout option
        if st.button("🚪 Logout", type="secondary"):
            logout()
            st.rerun()
        
        # Info panel
        st.markdown("### ℹ️ How it works")
        st.markdown("""
        1. **Enter URL** - Website to analyze
        2. **Choose Mode** - Regular or Casino review
        3. **Click Analyze** - AI processes content
        4. **Download Report** - Get Word document
        """)

def process_analysis(url: str, casino_mode: bool):
    """Process the complete analysis workflow"""
    
    try:
        # Step 1: Extract content
        with st.status("Extracting content..."):
            success, extracted_content, error = extract_url_content(url)
            
            if not success:
                st.error(f"❌ Content extraction failed: {error}")
                return
        
        # Step 2: AI Analysis with simple progress
        with st.status("Analyzing content..."):
            # Run AI analysis
            async def run_analysis():
                return await analyze_content(extracted_content, casino_mode)
            
            # Run analysis
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(lambda: asyncio.run(run_analysis()))
                analysis_result = future.result(timeout=300)  # 5 min timeout
        
        if not analysis_result or not analysis_result.get('success'):
            error_msg = analysis_result.get('error', 'Unknown error') if analysis_result else 'Analysis failed'
            st.error(f"❌ AI Analysis failed: {error_msg}")
            return
        
        # Step 3: Generate report
        with st.status("Generating report..."):
            word_bytes = generate_word_report(
                analysis_result['report'],
                f"YMYL Compliance Report - {url}",
                casino_mode
            )
            
            # Create download button
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ymyl_report_{timestamp}.docx"
        
        # Simple download section
        st.success("✅ Analysis complete!")
        
        st.download_button(
            label="📄 Download Word Report",
            data=word_bytes,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True
        )
                
    except Exception as e:
        st.error(f"❌ Analysis failed: {str(e)}")
        safe_log(f"Analysis process error: {e}")

if __name__ == "__main__":
    main()
