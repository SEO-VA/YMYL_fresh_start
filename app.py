#!/usr/bin/env python3
"""
YMYL Audit Tool - Two-Step Process with Admin Features
"""

import streamlit as st
import time
import asyncio
import json
from datetime import datetime

# Import our modular components
from core.auth import check_authentication, logout, get_current_user
from core.extractor import extract_url_content
from core.analyzer import analyze_content
from core.reporter import generate_word_report
from utils.helpers import safe_log

# Configure Streamlit page
st.set_page_config(
    page_title="YMYL Audit Tool",
    page_icon="🔍",
    layout="wide"
)

def main():
    """Main application function"""
    
    # Check authentication first
    if not check_authentication():
        return
    
    # Get current user and check admin status
    current_user = get_current_user()
    is_admin = (current_user == 'admin')
    
    # Create page header
    create_page_header(current_user, is_admin)
    
    # Main content layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Step 1: URL Input and Content Extraction
        handle_content_extraction(is_admin)
        
        # Step 2: AI Analysis (only show if content is extracted)
        if 'extracted_content' in st.session_state:
            handle_ai_analysis(is_admin)
    
    with col2:
        create_sidebar_content(is_admin)

def create_page_header(current_user: str, is_admin: bool):
    """Create page header with user info"""
    st.title("🔍 YMYL Audit Tool")
    
    # Show user and mode info
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("**AI-powered YMYL compliance analysis**")
    with col2:
        if is_admin:
            st.success(f"🛠️ Admin: {current_user}")
        else:
            st.info(f"👤 User: {current_user}")
    
    st.markdown("---")

def handle_content_extraction(is_admin: bool):
    """Handle Step 1: Content extraction"""
    st.subheader("📄 Step 1: Content Extraction")
    
    # URL input
    col1, col2 = st.columns([2, 1])
    
    with col1:
        url = st.text_input(
            "Enter the URL to analyze:",
            placeholder="https://example.com/page-to-analyze",
            help="Enter the full URL including http:// or https://",
            key="url_input"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        casino_mode = st.checkbox(
            "🎰 Casino Mode",
            help="Use specialized gambling content analysis"
        )
    
    # Extract button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        extract_clicked = st.button(
            "📄 Extract Content",
            type="primary",
            use_container_width=True,
            disabled=not url or not url.strip()
        )
    
    # Process extraction
    if extract_clicked and url:
        process_extraction(url.strip(), casino_mode, is_admin)

def process_extraction(url: str, casino_mode: bool, is_admin: bool):
    """Process the content extraction"""
    
    with st.status("Extracting content from URL..."):
        success, extracted_content, error = extract_url_content(url)
    
    if not success:
        st.error(f"❌ Extraction failed: {error}")
        return
    
    # Store in session state
    st.session_state['extracted_content'] = extracted_content
    st.session_state['source_url'] = url
    st.session_state['casino_mode'] = casino_mode
    
    st.success("✅ Content extracted successfully!")
    
    if is_admin:
        show_admin_extraction_details(extracted_content)
    else:
        st.info("💡 Content ready for AI analysis!")

def show_admin_extraction_details(extracted_content: str):
    """Show detailed extraction info for admin users"""
    st.markdown("### 🔍 Admin: Extraction Details")
    
    try:
        # Parse and show structure
        content_data = json.loads(extracted_content)
        big_chunks = content_data.get('big_chunks', [])
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Big Chunks", len(big_chunks))
        with col2:
            total_small_chunks = sum(len(chunk.get('small_chunks', [])) for chunk in big_chunks)
            st.metric("Small Chunks", total_small_chunks)
        with col3:
            st.metric("JSON Size", f"{len(extracted_content):,} chars")
        
        # Show structured content preview
        with st.expander("👁️ View Extracted Content Structure"):
            for i, chunk in enumerate(big_chunks, 1):
                st.markdown(f"**📦 Big Chunk {i}:**")
                small_chunks = chunk.get('small_chunks', [])
                
                for j, small_chunk in enumerate(small_chunks[:3], 1):  # Show first 3
                    preview = small_chunk[:150] + "..." if len(small_chunk) > 150 else small_chunk
                    st.text(f"  {j}. {preview}")
                
                if len(small_chunks) > 3:
                    st.text(f"  ... and {len(small_chunks) - 3} more chunks")
                st.markdown("---")
        
        # Show JSON that goes to AI
        with st.expander("🤖 JSON Data Sent to AI"):
            st.code(extracted_content, language='json')
            
    except json.JSONDecodeError as e:
        st.error(f"❌ Could not parse JSON: {e}")

def handle_ai_analysis(is_admin: bool):
    """Handle Step 2: AI Analysis"""
    st.markdown("---")
    st.subheader("🤖 Step 2: AI Analysis")
    
    # Get stored data
    extracted_content = st.session_state.get('extracted_content')
    casino_mode = st.session_state.get('casino_mode', False)
    source_url = st.session_state.get('source_url', 'Unknown URL')
    
    # Show analysis info
    col1, col2 = st.columns([2, 1])
    
    with col1:
        mode_text = "Casino Review" if casino_mode else "Regular Analysis"
        st.info(f"🎯 Ready to analyze: **{source_url}** ({mode_text})")
    
    with col2:
        clear_clicked = st.button("🗑️ Clear & Restart", help="Clear extracted content")
    
    # Clear content if requested
    if clear_clicked:
        for key in ['extracted_content', 'source_url', 'casino_mode']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    # Analysis button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        analyze_clicked = st.button(
            "🚀 Run AI Analysis",
            type="primary", 
            use_container_width=True
        )
    
    # Process analysis
    if analyze_clicked:
        process_ai_analysis(extracted_content, casino_mode, source_url, is_admin)

def process_ai_analysis(extracted_content: str, casino_mode: bool, source_url: str, is_admin: bool):
    """Process the AI analysis"""
    
    try:
        # Run AI analysis
        with st.status("Running AI analysis..."):
            async def run_analysis():
                return await analyze_content(extracted_content, casino_mode)
            
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(lambda: asyncio.run(run_analysis()))
                analysis_result = future.result(timeout=300)
        
        if not analysis_result or not analysis_result.get('success'):
            error_msg = analysis_result.get('error', 'Unknown error')
            st.error(f"❌ AI analysis failed: {error_msg}")
            return
        
        # Generate report
        with st.status("Generating Word report..."):
            word_bytes = generate_word_report(
                analysis_result['report'],
                f"YMYL Report - {source_url}",
                casino_mode
            )
        
        st.success("✅ Analysis complete!")
        
        # Show results
        show_analysis_results(analysis_result, word_bytes, is_admin)
        
    except Exception as e:
        st.error(f"❌ Analysis failed: {str(e)}")
        safe_log(f"Analysis error: {e}")

def show_analysis_results(analysis_result: dict, word_bytes: bytes, is_admin: bool):
    """Show analysis results"""
    
    if is_admin:
        # Admin: Show detailed results
        st.markdown("### 📊 Admin: Analysis Results")
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Processing Time", f"{analysis_result.get('processing_time', 0):.1f}s")
        with col2:
            ai_response = analysis_result.get('ai_response', [])
            sections_count = len(ai_response) if isinstance(ai_response, list) else 0
            st.metric("Sections", sections_count)
        with col3:
            st.metric("Response Size", f"{analysis_result.get('response_length', 0):,} chars")
        
        # Violation summary
        if isinstance(ai_response, list):
            violations_found = sum(1 for section in ai_response 
                                 if section.get('violations') != "no violation found" 
                                 and section.get('violations'))
            
            if violations_found > 0:
                st.warning(f"⚠️ **Found violations in {violations_found} section(s)**")
            else:
                st.success("✅ **No violations found**")
        
        # Show raw AI response
        with st.expander("🤖 View Raw AI Response"):
            st.json(analysis_result.get('ai_response', {}))
    
    # Download section (for both admin and regular users)
    st.markdown("### 📄 Download Report")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ymyl_report_{timestamp}.docx"
    
    st.download_button(
        label="📄 Download Word Report",
        data=word_bytes,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="primary",
        use_container_width=True
    )
    
    if not is_admin:
        st.info("💡 **Tip**: Import the Word file into Google Docs for perfect formatting!")

def create_sidebar_content(is_admin: bool):
    """Create sidebar content"""
    
    # Logout button
    if st.button("🚪 Logout", type="secondary", use_container_width=True):
        logout()
        # Clear session state
        for key in list(st.session_state.keys()):
            if key not in ['authenticated', 'username']:
                del st.session_state[key]
        st.rerun()
    
    # Instructions
    st.markdown("### ℹ️ How it works")
    
    if is_admin:
        st.markdown("""
        **Admin Mode (2-Step):**
        
        1️⃣ **Extract Content**
        - View detailed extraction metrics
        - See structured content preview
        - Review JSON sent to AI
        
        2️⃣ **Run AI Analysis** 
        - See processing details
        - View raw AI responses
        - Check violation summaries
        
        3️⃣ **Download Report**
        - Professional Word document
        """)
    else:
        st.markdown("""
        **Standard Process:**
        
        1️⃣ **Extract Content**
        - Clean content extraction
        
        2️⃣ **Run AI Analysis**
        - YMYL compliance check
        
        3️⃣ **Download Report**
        - Professional Word document
        """)

if __name__ == "__main__":
    main()
