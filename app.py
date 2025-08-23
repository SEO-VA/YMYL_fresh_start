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
    
    # Feature selection
    selected_feature = show_feature_selector()
    
    # Route to appropriate handler based on user type
    if is_admin:
        layout = AdminLayout()
        layout.render(selected_feature)
    else:
        layout = UserLayout()
        layout.render(selected_feature)
    
    # Sidebar
    create_sidebar(current_user, is_admin)

def create_page_header(current_user: str, is_admin: bool):
    """Create main page header"""
    st.title("🔍 YMYL Audit Tool")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("**AI-powered YMYL compliance analysis**")
    with col2:
        if is_admin:
            st.success(f"🛠️ Admin: {current_user}")
        else:
            st.info(f"👤 User: {current_user}")
    
    st.markdown("---")

def show_feature_selector():
    """Show feature selection interface"""
    st.subheader("📋 Analysis Type")
    
    # Get available features from registry
    available_features = FeatureRegistry.get_available_features()
    
    # Feature selection
    col1, col2 = st.columns([3, 1])
    with col1:
        selected = st.selectbox(
            "Choose analysis method:",
            options=list(available_features.keys()),
            format_func=lambda x: available_features[x]['display_name'],
            help="Select the type of content you want to analyze"
        )
    
    with col2:
        # Show feature info
        feature_info = available_features[selected]
        st.info(f"📄 {feature_info['description']}")
    
    return selected

def create_sidebar(current_user: str, is_admin: bool):
    """Create sidebar with user controls and info"""
    with st.sidebar:
        # Logout button
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            logout()
            # Clear session state except auth
            for key in list(st.session_state.keys()):
                if key not in ['authenticated', 'username']:
                    del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        
        # Mode-specific instructions
        if is_admin:
            show_admin_info()
        else:
            show_user_info()
        
        # System status
        show_system_status()

def show_admin_info():
    """Show admin-specific information"""
    st.markdown("### 🛠️ Admin Mode")
    st.markdown("""
    **Two-Step Process:**
    
    1️⃣ **Content Extraction**
    - View detailed extraction metrics
    - Inspect structured content
    - Review data sent to AI
    
    2️⃣ **AI Analysis**  
    - See processing details
    - View raw AI responses
    - Check violation summaries
    
    3️⃣ **Professional Report**
    - Download Word document
    """)

def show_user_info():
    """Show user-specific information"""
    st.markdown("### ℹ️ How to Use")
    st.markdown("""
    **Simple Process:**
    
    1️⃣ **Choose Content Source**
    - URL, HTML file, or ZIP
    
    2️⃣ **Select Analysis Mode**
    - Regular or Casino review
    
    3️⃣ **Run Analysis**
    - AI processes content (2-5 min)
    
    4️⃣ **Download Report**
    - Professional Word document
    """)

def show_system_status():
    """Show system configuration status"""
    st.markdown("### 🔧 System Status")
    
    try:
        from config.settings import validate_configuration
        is_valid, errors = validate_configuration()
        
        if is_valid:
            st.success("✅ Configuration OK")
        else:
            st.error("❌ Configuration Issues")
            for error in errors[:3]:  # Show max 3 errors
                st.text(f"• {error}")
                
    except Exception as e:
        st.error(f"❌ Config check failed")

if __name__ == "__main__":
    main()
