#!/usr/bin/env python3
"""
YMYL Audit Tool - Main Application Router
Restructured for scalable feature architecture
"""

import streamlit as st
from core.auth import check_authentication, logout, get_current_user
from utils.feature_registry import FeatureRegistry
from ui.layouts.admin_layout import AdminLayout
from ui.layouts.user_layout import UserLayout

# Configure Streamlit page
st.set_page_config(
    page_title="YMYL Audit Tool",
    page_icon="🔍",
    layout="wide"
)

def main():
    """Main application router"""
    
    # Check authentication first
    if not check_authentication():
        return
    
    # Get current user and determine layout
    current_user = get_current_user()
    is_admin = (current_user == 'admin')
    
    # Create page header
    create_page_header(current_user, is_admin)
    
    # Feature selection - ONLY CHANGE: Radio buttons instead of dropdown
    selected_feature = show_feature_selector()
    
    # Route#!/usr/bin/env python3
"""
YMYL Audit Tool - Simple Clean Interface
"""

import streamlit as st
from core.auth import check_authentication, logout, get_current_user
from utils.feature_registry import FeatureRegistry

# Configure Streamlit page
st.set_page_config(
    page_title="YMYL Audit Tool",
    page_icon="🔍",
    layout="centered"  # Changed to centered for cleaner look
)

def main():
    """Main application"""
    
    # Check authentication first
    if not check_authentication():
        return
    
    # Get current user
    current_user = get_current_user()
    is_admin = (current_user == 'admin')
    
    # Simple header
    st.title("🔍 YMYL Audit Tool")
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🚪 Logout"):
            logout()
            st.rerun()
    
    st.markdown("---")
    
    # Simple feature selection
    selected_feature = show_simple_feature_selector()
    
    # Route to feature
    if selected_feature:
        try:
            feature_handler = FeatureRegistry.get_handler(selected_feature)
            
            if is_admin:
                render_admin_simple(feature_handler)
            else:
                render_user_simple(feature_handler)
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

def show_simple_feature_selector():
    """Simple feature selection with both URL and HTML"""
    try:
        available_features = FeatureRegistry.get_available_features()
        
        if not available_features:
            st.error("❌ No features available")
            return None
        
        # Simple radio buttons for URL vs HTML
        options = list(available_features.keys())
        labels = [available_features[opt]['display_name'] for opt in options]
        
        if len(options) >= 2:
            selected_idx = st.radio(
                "**Choose analysis type:**",
                range(len(options)),
                format_func=lambda x: labels[x],
                horizontal=True
            )
            return options[selected_idx]
        else:
            # Fallback if only one feature
            return options[0] if options else None
        
    except Exception as e:
        st.error(f"❌ Feature loading error: {str(e)}")
        return None

def render_admin_simple(feature_handler):
    """Simple admin interface"""
    st.subheader("🛠️ Admin Mode")
    
    # Get input
    input_data = feature_handler.get_input_interface()
    
    # Current step
    has_content = feature_handler.has_extracted_content()
    
    if not has_content:
        # Step 1: Extract
        if st.button("📄 Extract Content", type="primary", disabled=not input_data.get('is_valid')):
            process_extraction_simple(feature_handler, input_data)
    else:
        # Step 2: Analyze
        st.success("✅ Content extracted")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🚀 Run Analysis", type="primary"):
                process_analysis_simple(feature_handler)
        with col2:
            if st.button("🗑️ Clear"):
                feature_handler.clear_session_data()
                st.rerun()

def render_user_simple(feature_handler):
    """Simple user interface"""
    # Get input
    input_data = feature_handler.get_input_interface()
    
    # Single analyze button
    if st.button("🚀 Analyze Content", type="primary", disabled=not input_data.get('is_valid')):
        process_full_analysis_simple(feature_handler, input_data)

def process_extraction_simple(feature_handler, input_data):
    """Simple extraction process with admin preview"""
    with st.spinner("Extracting content..."):
        success, extracted_content, error = feature_handler.extract_content(input_data)
        
        if success:
            feature_handler.set_session_data('extracted_content', extracted_content)
            feature_handler.set_session_data('source_info', feature_handler.get_source_description(input_data))
            feature_handler.set_session_data('casino_mode', input_data.get('casino_mode', False))
            
            st.success("✅ Content extracted!")
            
            # Show admin preview
            show_admin_preview_simple(feature_handler, extracted_content)
            
            st.rerun()
        else:
            st.error(f"❌ {error}")

def show_admin_preview_simple(feature_handler, extracted_content):
    """Simple admin preview of extracted content"""
    st.markdown("### 🔍 Extraction Preview")
    
    # Get metrics
    metrics = feature_handler.get_extraction_metrics(extracted_content)
    
    # Show metrics in columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Big Chunks", metrics.get('big_chunks', 'N/A'))
    with col2:
        st.metric("Small Chunks", metrics.get('small_chunks', 'N/A'))
    with col3:
        st.metric("JSON Size", f"{metrics.get('json_size', 0):,} chars")
    
    # Content preview
    with st.expander("👁️ View Content Structure"):
        try:
            import json
            content_data = json.loads(extracted_content)
            big_chunks = content_data.get('big_chunks', [])
            
            for i, chunk in enumerate(big_chunks[:3], 1):  # Show first 3 chunks
                st.markdown(f"**📦 Chunk {i}:**")
                small_chunks = chunk.get('small_chunks', [])
                
                for j, small_chunk in enumerate(small_chunks[:2], 1):  # Show first 2 per chunk
                    preview = small_chunk[:100] + "..." if len(small_chunk) > 100 else small_chunk
                    st.text(f"  {j}. {preview}")
                
                if len(small_chunks) > 2:
                    st.text(f"  ... and {len(small_chunks) - 2} more")
                st.markdown("---")
                
            if len(big_chunks) > 3:
                st.text(f"... and {len(big_chunks) - 3} more chunks")
                
        except json.JSONDecodeError:
            st.error("Could not parse extracted content")

def process_analysis_simple(feature_handler):
    """Simple analysis process"""
    import asyncio
    import concurrent.futures
    from core.analyzer import analyze_content
    from core.reporter import generate_word_report
    from datetime import datetime
    
    extracted_content = feature_handler.get_extracted_content()
    casino_mode = feature_handler.get_session_data('casino_mode', False)
    source_info = feature_handler.get_source_info()
    
    with st.spinner("Running AI analysis..."):
        try:
            async def run_analysis():
                return await analyze_content(extracted_content, casino_mode)
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(lambda: asyncio.run(run_analysis()))
                analysis_result = future.result(timeout=300)
            
            if analysis_result and analysis_result.get('success'):
                word_bytes = generate_word_report(
                    analysis_result['report'],
                    f"YMYL Report - {source_info}",
                    casino_mode
                )
                
                st.success("✅ Analysis complete!")
                show_download_simple(word_bytes)
            else:
                st.error(f"❌ Analysis failed: {analysis_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

def process_full_analysis_simple(feature_handler, input_data):
    """Simple full analysis for users"""
    import asyncio
    import concurrent.futures
    from core.analyzer import analyze_content
    from core.reporter import generate_word_report
    
    with st.spinner("Processing..."):
        try:
            # Extract
            success, extracted_content, error = feature_handler.extract_content(input_data)
            if not success:
                st.error(f"❌ {error}")
                return
            
            # Analyze
            casino_mode = input_data.get('casino_mode', False)
            
            async def run_analysis():
                return await analyze_content(extracted_content, casino_mode)
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(lambda: asyncio.run(run_analysis()))
                analysis_result = future.result(timeout=300)
            
            if not analysis_result or not analysis_result.get('success'):
                st.error(f"❌ Analysis failed")
                return
            
            # Generate report
            source_info = feature_handler.get_source_description(input_data)
            word_bytes = generate_word_report(
                analysis_result['report'],
                f"YMYL Report - {source_info}",
                casino_mode
            )
            
            st.success("✅ Analysis complete!")
            show_download_simple(word_bytes)
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

def show_download_simple(word_bytes):
    """Simple download interface"""
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ymyl_report_{timestamp}.docx"
    
    st.download_button(
        label="📄 Download Report",
        data=word_bytes,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="primary"
    )

if __name__ == "__main__":
    main()
