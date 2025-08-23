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
        # Create progress container
        progress_container = st.container()
        
        with progress_container:
            st.markdown("### 🔄 Processing Analysis")
            
            # Step 1: Extract content
            st.info("📄 Extracting content from URL...")
            success, extracted_content, error = extract_url_content(url)
            
            if not success:
                st.error(f"❌ Content extraction failed: {error}")
                return
            
            st.success(f"✅ Content extracted ({len(extracted_content):,} characters)")
            
            # Step 2: AI Analysis with fake progress
            st.info("🤖 Starting AI analysis...")
            
            # Create fake progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Start AI analysis in background
            async def run_analysis():
                return await analyze_content(extracted_content, casino_mode)
            
            # Fake progress while AI runs
            progress_steps = [
                (10, "Processing content structure..."),
                (30, "Analyzing YMYL compliance..."), 
                (60, "Checking guideline violations..."),
                (85, "Generating recommendations..."),
                (100, "Analysis complete!")
            ]
            
            # Run analysis with fake progress
            analysis_result = None
            start_time = time.time()
            
            # Create async task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(lambda: asyncio.run(run_analysis()))
                
                # Show fake progress
                for progress, message in progress_steps:
                    elapsed = time.time() - start_time
                    if future.done():
                        break
                    
                    progress_bar.progress(progress / 100)
                    status_text.text(f"🔄 {message}")
                    time.sleep(2)  # Wait between updates
                
                # Get final result
                try:
                    analysis_result = future.result(timeout=300)  # 5 min timeout
                    progress_bar.progress(1.0)
                    status_text.text("✅ Analysis complete!")
                except concurrent.futures.TimeoutError:
                    st.error("❌ Analysis timed out after 5 minutes")
                    return
            
            if not analysis_result or not analysis_result.get('success'):
                error_msg = analysis_result.get('error', 'Unknown error') if analysis_result else 'Analysis failed'
                st.error(f"❌ AI Analysis failed: {error_msg}")
                return
            
            st.success("✅ AI analysis completed successfully!")
            
            # Step 3: Generate report
            st.info("📝 Generating Word report...")
            
            try:
                word_bytes = generate_word_report(
                    analysis_result['report'],
                    f"YMYL Compliance Report - {url}",
                    casino_mode
                )
                
                # Create download button
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"ymyl_report_{timestamp}.docx"
                
                st.success("✅ Report generated successfully!")
                
                # Display results
                create_results_display(analysis_result, word_bytes, filename)
                
            except Exception as e:
                st.error(f"❌ Report generation failed: {str(e)}")
                safe_log(f"Report generation error: {e}")
                
    except Exception as e:
        st.error(f"❌ Unexpected error during analysis: {str(e)}")
        safe_log(f"Analysis process error: {e}")

if __name__ == "__main__":
    main()
