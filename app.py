#!/usr/bin/env python3
"""
YMYL Audit Tool - Simple Interface
"""

import streamlit as st
from core.auth import check_authentication, logout, get_current_user
from utils.feature_registry import FeatureRegistry

# Configure Streamlit page
st.set_page_config(
    page_title="YMYL Audit Tool",
    page_icon="🔍",
    layout="centered"
)

def main():
    """Main application"""
    
    # Check authentication
    if not check_authentication():
        return
    
    # Get current user
    current_user = get_current_user()
    is_admin = (current_user == 'admin')
    
    # Header
    st.title("🔍 YMYL Audit Tool")
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🚪 Logout"):
            logout()
            st.rerun()
    
    st.markdown("---")
    
    # Feature selection with radio buttons
    analysis_type = st.radio(
        "**Choose analysis type:**",
        ["🌐 URL Analysis", "📄 HTML Analysis"],
        horizontal=True
    )
    
    # Get appropriate feature handler
    try:
        available_features = FeatureRegistry.get_available_features()
        
        # Debug: Show what features are available
        if not available_features:
            st.error("❌ No features registered")
            st.text("Debug: Check feature imports in feature_registry.py")
            return
        
        # Map display names to feature keys
        if analysis_type == "🌐 URL Analysis":
            feature_key = "url_analysis"
        else:
            feature_key = "html_analysis"
        
        # Check if feature exists
        if feature_key not in available_features:
            st.error(f"❌ Feature '{feature_key}' not found")
            st.text(f"Available features: {list(available_features.keys())}")
            return
        
        feature_handler = FeatureRegistry.get_handler(feature_key)
        
        if is_admin:
            render_admin_interface(feature_handler)
        else:
            render_user_interface(feature_handler)
            
    except Exception as e:
        st.error(f"❌ Error loading feature: {str(e)}")
        
        # Show debug info
        try:
            available_features = FeatureRegistry.get_available_features()
            st.text(f"Available features: {list(available_features.keys())}")
        except:
            st.text("Could not get available features")

def render_admin_interface(feature_handler):
    """Admin interface with two steps and preview"""
    
    # Check if we have extracted content
    has_content = feature_handler.has_extracted_content()
    
    if not has_content:
        # Step 1: Extract content
        st.subheader("Step 1: Extract Content")
        
        # Get input interface
        input_data = feature_handler.get_input_interface()
        
        # Extract button
        if st.button("📄 Extract Content", type="primary", disabled=not input_data.get('is_valid')):
            with st.spinner("Extracting content..."):
                success, extracted_content, error = feature_handler.extract_content(input_data)
                
                if success:
                    # Save data
                    feature_handler.set_session_data('extracted_content', extracted_content)
                    feature_handler.set_session_data('source_info', feature_handler.get_source_description(input_data))
                    feature_handler.set_session_data('casino_mode', input_data.get('casino_mode', False))
                    
                    st.success("✅ Content extracted!")
                    st.rerun()
                else:
                    st.error(f"❌ {error}")
    
    else:
        # Step 2: Show preview and analyze
        st.subheader("Step 2: Review & Analyze")
        
        # Show admin preview
        show_admin_preview(feature_handler)
        
        # Action buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🚀 Run AI Analysis", type="primary"):
                run_analysis(feature_handler)
        with col2:
            if st.button("🗑️ Clear & Restart"):
                feature_handler.clear_session_data()
                st.rerun()

def render_user_interface(feature_handler):
    """Simple user interface - one step"""
    
    # Get input interface
    input_data = feature_handler.get_input_interface()
    
    # Single analyze button
    if st.button("🚀 Analyze Content", type="primary", disabled=not input_data.get('is_valid')):
        with st.spinner("Processing..."):
            # Extract content
            success, extracted_content, error = feature_handler.extract_content(input_data)
            if not success:
                st.error(f"❌ {error}")
                return
            
            # Run analysis
            casino_mode = input_data.get('casino_mode', False)
            source_info = feature_handler.get_source_description(input_data)
            
            analysis_result = run_ai_analysis(extracted_content, casino_mode)
            
            if analysis_result and analysis_result.get('success'):
                # Generate report
                word_bytes = generate_report(analysis_result, source_info, casino_mode)
                st.success("✅ Analysis complete!")
                show_download(word_bytes)
            else:
                st.error("❌ Analysis failed")

def show_admin_preview(feature_handler):
    """Show content preview for admin"""
    extracted_content = feature_handler.get_extracted_content()
    source_info = feature_handler.get_source_info()
    
    st.info(f"**Source**: {source_info}")
    
    # Get metrics
    metrics = feature_handler.get_extraction_metrics(extracted_content)
    
    # Show metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Big Chunks", metrics.get('big_chunks', 'N/A'))
    with col2:
        st.metric("Small Chunks", metrics.get('small_chunks', 'N/A'))  
    with col3:
        st.metric("JSON Size", f"{metrics.get('json_size', 0):,} chars")
    
    # Content preview
    with st.expander("👁️ View Full Extracted Content"):
        st.text_area(
            "Complete Extracted Content:",
            value=extracted_content,
            height=400,
            key="full_content_preview"
        )

def run_analysis(feature_handler):
    """Run AI analysis for admin"""
    extracted_content = feature_handler.get_extracted_content()
    casino_mode = feature_handler.get_session_data('casino_mode', False)
    source_info = feature_handler.get_source_info()
    
    with st.spinner("Running AI analysis..."):
        analysis_result = run_ai_analysis(extracted_content, casino_mode)
        
        if analysis_result and analysis_result.get('success'):
            word_bytes = generate_report(analysis_result, source_info, casino_mode)
            st.success("✅ Analysis complete!")
            
            # Show admin results
            show_admin_results(analysis_result)
            
            # Download
            show_download(word_bytes)
        else:
            st.error("❌ Analysis failed")

def show_admin_results(analysis_result):
    """Show analysis results for admin"""
    st.markdown("### 📊 Analysis Results")
    
    # Metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Processing Time", f"{analysis_result.get('processing_time', 0):.1f}s")
    with col2:
        ai_response = analysis_result.get('ai_response', [])
        violations = sum(1 for section in ai_response 
                        if section.get('violations') != "no violation found" 
                        and section.get('violations')) if isinstance(ai_response, list) else 0
        st.metric("Violations Found", violations)

def run_ai_analysis(extracted_content, casino_mode):
    """Run AI analysis"""
    import asyncio
    import concurrent.futures
    from core.analyzer import analyze_content
    
    try:
        async def run_analysis():
            return await analyze_content(extracted_content, casino_mode)
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(lambda: asyncio.run(run_analysis()))
            return future.result(timeout=300)
            
    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
        return None

def generate_report(analysis_result, source_info, casino_mode):
    """Generate Word report"""
    from core.reporter import generate_word_report
    
    return generate_word_report(
        analysis_result['report'],
        f"YMYL Report - {source_info}",
        casino_mode
    )

def show_download(word_bytes):
    """Show download button"""
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
