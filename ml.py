import streamlit as st
import os
import pandas as pd
from PIL import Image
from io import BytesIO
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.tavily import TavilyTools
from tempfile import NamedTemporaryFile
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.units import inch
from datetime import datetime
import re

# Set page configuration with custom theme
st.set_page_config(
    page_title="MediScan - Drug Composition Analyzer",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏥"
)

# Enhanced CSS with trustworthy medical theme and animations
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root variables for consistent theming */
    :root {
        --primary-blue: #1e40af;
        --primary-dark: #1e3a8a;
        --secondary-blue: #3b82f6;
        --light-blue: #eff6ff;
        --accent-green: #059669;
        --accent-green-dark: #047857;
        --neutral-50: #f8fafc;
        --neutral-100: #f1f5f9;
        --neutral-200: #e2e8f0;
        --neutral-300: #cbd5e1;
        --neutral-600: #475569;
        --neutral-700: #334155;
        --neutral-800: #1e293b;
        --white: #ffffff;
        --success-green: #10b981;
        --warning-amber: #f59e0b;
        --error-red: #ef4444;
    }
    
    /* Force light theme with medical color palette */
    .stApp {
        background: linear-gradient(135deg, var(--neutral-50) 0%, var(--light-blue) 100%) !important;
        color: var(--neutral-800) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Main container styling with animation */
    .main .block-container {
        background-color: transparent !important;
        color: var(--neutral-800) !important;
        animation: fadeInUp 0.8s ease-out;
        max-width: 1400px !important;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInFromLeft {
        from {
            opacity: 0;
            transform: translateX(-50px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideInFromRight {
        from {
            opacity: 0;
            transform: translateX(50px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
        }
    }
    
    @keyframes shimmer {
        0% {
            background-position: -200% 0;
        }
        100% {
            background-position: 200% 0;
        }
    }
    
    /* Header styling with professional medical look */
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, var(--primary-blue), var(--secondary-blue));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 1rem;
        padding-bottom: 1.5rem;
        border-bottom: 3px solid var(--neutral-200);
        position: relative;
        animation: slideInFromLeft 1s ease-out;
    }
    
    .main-header::after {
        content: '';
        position: absolute;
        bottom: -3px;
        left: 50%;
        transform: translateX(-50%);
        width: 100px;
        height: 3px;
        background: linear-gradient(90deg, var(--accent-green), var(--secondary-blue));
        border-radius: 2px;
        animation: expandWidth 1s ease-out 0.5s both;
    }
    
    @keyframes expandWidth {
        from { width: 0; }
        to { width: 100px; }
    }
    
    .subheader {
        font-size: 1.75rem;
        font-weight: 600;
        color: var(--primary-dark);
        margin-top: 2rem;
        margin-bottom: 1rem;
        position: relative;
        padding-left: 1rem;
    }
    
    .subheader::before {
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 4px;
        height: 100%;
        background: linear-gradient(180deg, var(--accent-green), var(--secondary-blue));
        border-radius: 2px;
    }
    
    /* Enhanced card styling with glassmorphism effect */
    .card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 
            0 8px 32px rgba(30, 64, 175, 0.1),
            0 4px 16px rgba(0, 0, 0, 0.05);
        margin-bottom: 2rem;
        color: var(--neutral-800);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        animation: slideInFromRight 1s ease-out 0.3s both;
    }
    
    .card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(59, 130, 246, 0.1),
            transparent
        );
        transition: left 0.6s;
    }
    
    .card:hover::before {
        left: 100%;
    }
    
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 
            0 20px 40px rgba(30, 64, 175, 0.15),
            0 8px 24px rgba(0, 0, 0, 0.1);
    }
    
    /* Status boxes with enhanced styling */
    .success-box {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.1));
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-left: 5px solid var(--success-green);
        padding: 1.5rem;
        border-radius: 12px;
        color: var(--neutral-800);
        animation: slideInFromLeft 0.6s ease-out;
    }
    
    .warning-box {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(217, 119, 6, 0.1));
        border: 1px solid rgba(245, 158, 11, 0.3);
        border-left: 5px solid var(--warning-amber);
        padding: 1.5rem;
        border-radius: 12px;
        color: var(--neutral-800);
        animation: slideInFromLeft 0.6s ease-out;
    }
    
    .info-box {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(30, 64, 175, 0.1));
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-left: 5px solid var(--secondary-blue);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        color: var(--neutral-800);
        animation: slideInFromLeft 0.6s ease-out;
    }
    
    .disclaimer-box {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.05), rgba(220, 38, 38, 0.05));
        border: 1px solid rgba(239, 68, 68, 0.2);
        border-left: 5px solid var(--error-red);
        padding: 1rem;
        border-radius: 12px;
        margin: 0 0 1.5rem 0;
        color: var(--neutral-800);
        animation: slideInFromLeft 0.8s ease-out;
    }
    
    /* Enhanced button styling */
    .stButton>button {
        background: linear-gradient(135deg, var(--primary-blue), var(--secondary-blue)) !important;
        color: white !important;
        font-weight: 600;
        font-size: 1.1rem;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        width: 100%;
        border: none;
        box-shadow: 0 4px 16px rgba(30, 64, 175, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .stButton>button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(255, 255, 255, 0.2),
            transparent
        );
        transition: left 0.6s;
    }
    
    .stButton>button:hover::before {
        left: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(30, 64, 175, 0.4);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* Upload section with enhanced styling */
    .upload-section {
        border: 2px dashed var(--neutral-300);
        border-radius: 20px;
        padding: 3rem 2rem;
        text-align: center;
        margin-bottom: 2rem;
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(5px);
        color: var(--neutral-700);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        animation: slideInFromLeft 1s ease-out 0.5s both;
    }
    
    .upload-section::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: conic-gradient(
            from 0deg,
            transparent,
            rgba(59, 130, 246, 0.1),
            transparent,
            rgba(16, 185, 129, 0.1),
            transparent
        );
        animation: rotate 8s linear infinite;
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .upload-section:hover::before {
        opacity: 1;
    }
    
    @keyframes rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .upload-section:hover {
        border-color: var(--secondary-blue);
        background: rgba(255, 255, 255, 0.95);
        transform: scale(1.02);
    }
    
    /* Enhanced tagline styling */
    .tagline {
        text-align: center;
        font-size: 1.3rem;
        font-weight: 600;
        color: var(--white);
        margin: 1.5rem auto;
        padding: 1rem 1.5rem;
        border-radius: 25px;
        background: linear-gradient(135deg, var(--accent-green), var(--success-green));
        max-width: 450px;
        box-shadow: 0 8px 24px rgba(5, 150, 105, 0.3);
        position: relative;
        overflow: hidden;
        animation: slideInFromLeft 1s ease-out 0.2s both;
    }
    
    .tagline::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(255, 255, 255, 0.2),
            transparent
        );
        animation: shimmer 2s infinite;
    }
    
    .dark-tagline {
        text-align: center;
        font-size: 1.3rem;
        font-weight: 600;
        color: var(--white);
        margin: 1.5rem auto;
        padding: 1rem 1.5rem;
        border-radius: 25px;
        background: linear-gradient(135deg, var(--primary-blue), var(--primary-dark));
        max-width: 450px;
        box-shadow: 0 8px 24px rgba(30, 64, 175, 0.3);
        position: relative;
        overflow: hidden;
        animation: slideInFromRight 1s ease-out 0.2s both;
    }
    
    .dark-tagline::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(255, 255, 255, 0.2),
            transparent
        );
        animation: shimmer 2s infinite;
    }
    
    /* Enhanced info labels */
    .info-label {
        font-weight: 700;
        color: var(--primary-dark);
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
        font-size: 1.1rem;
        padding: 0.5rem 0;
        border-bottom: 2px solid var(--neutral-200);
        position: relative;
    }
    
    .info-label::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 50px;
        height: 2px;
        background: linear-gradient(90deg, var(--accent-green), var(--secondary-blue));
        border-radius: 1px;
    }
    
    /* Download button styling */
    .stDownloadButton > button {
        background: linear-gradient(135deg, var(--accent-green), var(--accent-green-dark)) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        box-shadow: 0 4px 16px rgba(5, 150, 105, 0.3) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(5, 150, 105, 0.4) !important;
    }
    
    /* Centered image container */
    .centered-image {
        display: flex;
        justify-content: center;
        margin: 1.5rem 0;
        animation: fadeInUp 0.8s ease-out 0.3s both;
    }
    
    .centered-image img {
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
    }
    
    .centered-image img:hover {
        transform: scale(1.05);
    }
    
    /* Loading spinner customization */
    .stSpinner > div {
        border-color: var(--secondary-blue) !important;
        border-top-color: transparent !important;
    }
    
    /* Results section animation */
    .results-container {
        animation: fadeInUp 0.8s ease-out 0.5s both;
    }
    
    /* Pulse animation for important elements */
    .pulse-animation {
        animation: pulse 2s infinite;
    }
    
    /* Floating effect for important cards */
    .floating-card {
        animation: float 3s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% {
            transform: translateY(0px);
        }
        50% {
            transform: translateY(-10px);
        }
    }
    
    /* Professional medical footer */
    .medical-footer {
        background: linear-gradient(135deg, var(--neutral-100), var(--neutral-50));
        border-top: 2px solid var(--neutral-200);
        padding: 2rem 0;
        margin-top: 3rem;
        text-align: center;
        color: var(--neutral-600);
        font-size: 0.9rem;
        position: relative;
    }
    
    .medical-footer::before {
        content: '';
        position: absolute;
        top: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 100px;
        height: 2px;
        background: linear-gradient(90deg, var(--accent-green), var(--secondary-blue));
    }
    
    /* Responsive enhancements */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2.5rem;
        }
        
        .tagline, .dark-tagline {
            font-size: 1.1rem;
            padding: 0.75rem 1rem;
        }
        
        .card {
            padding: 1.5rem;
            border-radius: 16px;
        }
        
        .upload-section {
            padding: 2rem 1rem;
        }
    }
    
    /* Force all text to use professional colors */
    .stMarkdown, .stText, p, div, span {
        color: var(--neutral-800) !important;
    }
    
    /* File uploader styling */
    .stFileUploader > div {
        background-color: transparent !important;
        color: var(--neutral-800) !important;
    }
    
    .stFileUploader label {
        color: var(--neutral-800) !important;
        font-weight: 600 !important;
    }
    
    /* Professional container backgrounds */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, var(--neutral-50) 0%, var(--light-blue) 100%) !important;
    }
    
    [data-testid="stHeader"] {
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(10px) !important;
    }
    
    [data-testid="stToolbar"] {
        background: transparent !important;
    }
    
    /* Enhanced loading states */
    .loading-shimmer {
        background: linear-gradient(
            90deg,
            var(--neutral-200) 25%,
            var(--neutral-100) 50%,
            var(--neutral-200) 75%
        );
        background-size: 200% 100%;
        animation: shimmer 1.5s infinite;
    }
</style>
""", unsafe_allow_html=True)

# API Keys - Fixed variable name consistency
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")

# Check if API keys are available
if not TAVILY_API_KEY or not GOOGLE_API_KEY:
    st.error("🔑 API keys are missing. Please check your configuration.")
    st.stop()

MAX_IMAGE_WIDTH = 300

SYSTEM_PROMPT = """
You are an expert in pharmaceutical analysis and AI-driven drug composition recognition.
Your role is to analyze a tablet's composition from an image, identify its ingredients, and provide insights about the drug.

Additionally, once a drug composition is identified, retrieve and display its uses, side effects, and cost using reliable medical sources.
Ensure that you fetch accurate and specific details instead of generic placeholders.
"""

INSTRUCTIONS = """
- Extract only the drug composition from the tablet image.
- Use this composition to fetch and return its uses, side effects, and cost from trusted medical sources.
- Ensure that the AI provides detailed and relevant drug information.
- Return all information in a structured format:
  *Composition:* <composition>
  *Uses:* <accurate uses based on online sources>
  *Side Effects:* <verified side effects>
  *Cost:* <actual cost from trusted sources>
"""

@st.cache_resource
def get_agent():
    """Initialize and cache the AI agent."""
    try:
        return Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY),
            system_prompt=SYSTEM_PROMPT,
            instructions=INSTRUCTIONS,
            tools=[TavilyTools(api_key=TAVILY_API_KEY)],
            markdown=True,
        )
    except Exception as e:
        st.error(f"❌ Error initializing agent: {e}")
        return None

def resize_image_for_display(image_file):
    """Resize image for display only, returns bytes."""
    try:
        # Reset file pointer to beginning
        image_file.seek(0)
        img = Image.open(image_file)
        # Reset again for later use
        image_file.seek(0)
        
        aspect_ratio = img.height / img.width
        new_height = int(MAX_IMAGE_WIDTH * aspect_ratio)
        img = img.resize((MAX_IMAGE_WIDTH, new_height), Image.Resampling.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        st.error(f"🖼️ Error resizing image: {e}")
        return None

def extract_composition_and_details(image_path):
    """Extract composition and related drug details from the tablet image using AI."""
    agent = get_agent()
    if agent is None:
        return None

    try:
        with st.spinner("🔬 Analyzing tablet image and retrieving medical information..."):
            response = agent.run(
                "Extract the drug composition from this tablet image and provide its uses, side effects, and cost.",
                images=[image_path],
            )
            return response.content.strip()
    except Exception as e:
        st.error(f"🚨 Error extracting composition and details: {e}")
        return None

def save_uploaded_file(uploaded_file):
    """Save the uploaded file to disk."""
    try:
        # Get file extension from the uploaded file name
        file_extension = os.path.splitext(uploaded_file.name)[1]
        
        with NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_path = temp_file.name
        return temp_path
    except Exception as e:
        st.error(f"💾 Error saving uploaded file: {e}")
        return None

def create_pdf(image_data, analysis_results):
    """Create a PDF report of the analysis."""
    try:
        buffer = BytesIO()
        pdf = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Content to add to PDF
        content = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=18,
            alignment=1,
            spaceAfter=12,
            textColor=colors.navy
        )
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.navy,
            spaceAfter=6
        )
        normal_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=12,
            leading=14
        )
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.red,
            borderWidth=1,
            borderColor=colors.red,
            borderPadding=5,
            backColor=colors.pink,
            alignment=1
        )
        
        # Title
        content.append(Paragraph("🏥 MediScan - Drug Composition Analysis Report", title_style))
        content.append(Spacer(1, 0.25*inch))
        
        # Disclaimer
        content.append(Paragraph(
            "⚠️ MEDICAL DISCLAIMER: This information is provided for educational purposes only and should not replace professional medical advice. "
            "Always consult with a healthcare professional before making any medical decisions.",
            disclaimer_style
        ))
        content.append(Spacer(1, 0.25*inch))
        
        # Date and time
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content.append(Paragraph(f"📅 Generated on: {current_datetime}", normal_style))
        content.append(Spacer(1, 0.25*inch))
        
        # Add image if available
        if image_data:
            try:
                img_temp = BytesIO(image_data)
                img = Image.open(img_temp)
                img_width, img_height = img.size
                aspect = img_height / float(img_width)
                display_width = 4 * inch
                display_height = display_width * aspect
                
                # Reset BytesIO position for ReportLab
                img_temp.seek(0)
                img_obj = ReportLabImage(img_temp, width=display_width, height=display_height)
                content.append(Paragraph("📸 Analyzed Image:", heading_style))
                content.append(img_obj)
                content.append(Spacer(1, 0.25*inch))
            except Exception as img_error:
                st.warning(f"Could not add image to PDF: {img_error}")
        
        # Analysis results
        content.append(Paragraph("🔬 Analysis Results:", heading_style))
        
        # Format the analysis results for PDF
        if analysis_results:
            # Use regex to find sections in the format "*SectionName:* Content"
            section_pattern = r"\*([\w\s]+):\*(.*?)(?=\*[\w\s]+:\*|$)"
            matches = re.findall(section_pattern, analysis_results, re.DOTALL | re.IGNORECASE)
            
            if matches:
                for section_title, section_content in matches:
                    content.append(Paragraph(f"<b>{section_title.strip()}:</b>", normal_style))
                    
                    # Handle multiline content
                    paragraphs = section_content.strip().split("\n")
                    for para in paragraphs:
                        if para.strip():
                            # Escape HTML characters for ReportLab
                            clean_para = para.strip().replace('<', '&lt;').replace('>', '&gt;')
                            content.append(Paragraph(clean_para, normal_style))
                    
                    content.append(Spacer(1, 0.15*inch))
            else:
                # Fallback: add the entire analysis as-is if regex doesn't match
                clean_results = analysis_results.replace('<', '&lt;').replace('>', '&gt;')
                content.append(Paragraph(clean_results, normal_style))
        
        # Footer
        content.append(Spacer(1, 0.5*inch))
        content.append(Paragraph("© 2025 MediScan - Drug Composition Analyzer | Powered by Gemini AI + Tavily", 
                                ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.gray)))
        
        # Build PDF
        pdf.build(content)
        
        # Get the PDF value from the buffer
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"📄 Error creating PDF: {e}")
        return None

def main():
    # Initialize session state for button tracking
    if 'analyze_clicked' not in st.session_state:
        st.session_state.analyze_clicked = False
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'original_image' not in st.session_state:
        st.session_state.original_image = None

    # Header with enhanced medical branding
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="main-header">🏥 MediScan</div>', unsafe_allow_html=True)
        st.markdown('<div class="subheader" style="text-align: center; margin-top: 0; padding-left: 0;">Drug Composition Analyzer</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem; color: var(--neutral-600); font-size: 1.1rem; line-height: 1.6;">
            🔬 Advanced AI-powered pharmaceutical analysis for healthcare professionals and patients<br/>
            <span style="font-size: 0.95rem; opacity: 0.8;">Upload a tablet image to get comprehensive composition, usage, and safety information</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Enhanced medical disclaimer with professional styling
    st.markdown("""
    <div class="disclaimer-box" style="margin-top: 0; margin-bottom: 2rem;">
        <div style="display: flex; align-items: flex-start;">
            <span style="font-size: 1.5rem; margin-right: 0.75rem; margin-top: 0.1rem;">⚠️</span>
            <div>
                <div style="font-weight: 700; margin-bottom: 0.5rem; color: var(--error-red); font-size: 1.1rem;">MEDICAL DISCLAIMER</div>
                <div style="font-size: 0.95rem; line-height: 1.5; color: var(--neutral-700);">
                    The information provided by MediScan is for <strong>educational and informational purposes only</strong> and is not intended to replace professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition or medication. Never disregard professional medical advice or delay seeking it because of information obtained from this application.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content in a two-column layout with enhanced spacing
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        # Enhanced tagline with medical focus
        st.markdown('<div class="tagline">⚡ Instant pharmaceutical insights at your fingertips</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "📤 Upload Tablet Image",
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload a clear, high-quality image of the tablet or its packaging showing ingredient information",
            label_visibility="visible",
            key="image_uploader"
        )
        
        if uploaded_file:
            resized_image = resize_image_for_display(uploaded_file)
            if resized_image:
                st.markdown('<div class="centered-image">', unsafe_allow_html=True)
                st.image(resized_image, caption="📸 Uploaded Tablet Image", width=MAX_IMAGE_WIDTH)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Display file info
                file_size = len(uploaded_file.getvalue()) / 1024  # Convert to KB
                st.markdown(f"""
                <div style="text-align: center; margin-top: 1rem; padding: 0.5rem; background: rgba(59, 130, 246, 0.1); border-radius: 8px; color: var(--neutral-600); font-size: 0.9rem;">
                    📄 <strong>{uploaded_file.name}</strong> • {file_size:.1f} KB • Ready for analysis
                </div>
                """, unsafe_allow_html=True)
            
            # Enhanced analyze button with loading state
            if st.button("🔬 Analyze Tablet Composition", key="analyze_btn", help="Click to start AI-powered pharmaceutical analysis"):
                st.session_state.analyze_clicked = True
                
                # Save uploaded file and analyze
                temp_path = save_uploaded_file(uploaded_file)
                if temp_path:
                    try:
                        # Show progress indicator
                        progress_placeholder = st.empty()
                        with progress_placeholder.container():
                            st.markdown("""
                            <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(16, 185, 129, 0.1)); border-radius: 12px; margin: 1rem 0;">
                                <div class="loading-shimmer" style="height: 4px; border-radius: 2px; margin-bottom: 1rem;"></div>
                                <div style="color: var(--primary-blue); font-weight: 600;">🤖 AI Analysis in Progress...</div>
                                <div style="color: var(--neutral-600); font-size: 0.9rem; margin-top: 0.5rem;">Processing image • Identifying compounds • Fetching medical data</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        extracted_info = extract_composition_and_details(temp_path)
                        
                        # Clear progress indicator
                        progress_placeholder.empty()
                        
                        # Store results in session state
                        st.session_state.analysis_results = extracted_info
                        st.session_state.original_image = uploaded_file.getvalue()
                        
                        if extracted_info:
                            st.success("✅ Analysis completed successfully!")
                        else:
                            st.error("❌ Analysis failed. Please try with a clearer image.")
                        
                    except Exception as e:
                        st.error(f"🚨 Analysis failed: {e}")
                    finally:
                        # Clean up temp file
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
        else:
            st.markdown("""
            <div style="text-align: center; color: var(--neutral-500); margin-top: 3rem;">
                <div style="font-size: 4rem; margin-bottom: 1rem; opacity: 0.6;">📱</div>
                <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem; color: var(--neutral-700);">Upload Your Tablet Image</div>
                <div style="font-size: 1rem; margin-bottom: 1rem; line-height: 1.5;">
                    Drag and drop or click to select a clear photo of your tablet<br/>
                    <span style="font-size: 0.9rem; opacity: 0.8;">Supported formats: JPG, JPEG, PNG, WebP • Max size: 10MB</span>
                </div>
                <div style="display: flex; justify-content: center; gap: 1rem; margin-top: 1.5rem; flex-wrap: wrap;">
                    <div style="background: rgba(59, 130, 246, 0.1); padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.85rem; color: var(--secondary-blue);">✨ AI-Powered</div>
                    <div style="background: rgba(16, 185, 129, 0.1); padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.85rem; color: var(--accent-green);">🔒 HIPAA Compliant</div>
                    <div style="background: rgba(245, 158, 11, 0.1); padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.85rem; color: var(--warning-amber);">⚡ Instant Results</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Enhanced tagline for results section
        st.markdown('<div class="dark-tagline">🎯 Comprehensive pharmaceutical intelligence</div>', unsafe_allow_html=True)
        
        # Display results if available
        if st.session_state.analysis_results:
            st.markdown('<div class="card results-container floating-card">', unsafe_allow_html=True)
            st.markdown('<div class="subheader">📊 Analysis Results</div>', unsafe_allow_html=True)
            
            # Enhanced formatting for extracted information
            analysis_text = st.session_state.analysis_results
            
            # Create formatted sections with enhanced styling
            formatted_sections = []
            sections = ["Composition", "Uses", "Side Effects", "Cost"]
            
            for section in sections:
                pattern = rf"\*{section}:\*(.*?)(?=\*(?:Composition|Uses|Side Effects|Cost):\*|$)"
                match = re.search(pattern, analysis_text, re.DOTALL | re.IGNORECASE)
                
                if match:
                    content = match.group(1).strip()
                    
                    # Choose appropriate icon and color for each section
                    if section == "Composition":
                        icon = "🧬"
                        color_class = "primary-blue"
                    elif section == "Uses":
                        icon = "💊"
                        color_class = "accent-green"
                    elif section == "Side Effects":
                        icon = "⚠️"
                        color_class = "warning-amber"
                    else:  # Cost
                        icon = "💰"
                        color_class = "secondary-blue"
                    
                    formatted_sections.append(f"""
                    <div style="margin: 1.5rem 0; padding: 1.25rem; background: rgba(255, 255, 255, 0.7); border-radius: 12px; border-left: 4px solid var(--{color_class});">
                        <div style="font-weight: 700; color: var(--{color_class}); margin-bottom: 0.75rem; font-size: 1.15rem; display: flex; align-items: center;">
                            <span style="margin-right: 0.5rem; font-size: 1.3rem;">{icon}</span>
                            {section}
                        </div>
                        <div style="color: var(--neutral-700); line-height: 1.6; font-size: 1rem;">
                            {content.replace(chr(10), '<br/>')}
                        </div>
                    </div>
                    """)
            
            # Display all formatted sections
            for section_html in formatted_sections:
                st.markdown(section_html, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Enhanced PDF download section
            if st.session_state.original_image:
                st.markdown("""
                <div style="text-align: center; margin-top: 2rem; padding: 1.5rem; background: linear-gradient(135deg, rgba(5, 150, 105, 0.1), rgba(16, 185, 129, 0.1)); border-radius: 16px; border: 1px solid rgba(5, 150, 105, 0.2);">
                    <div style="font-size: 1.1rem; font-weight: 600; color: var(--accent-green); margin-bottom: 1rem;">
                        📄 Professional Medical Report
                    </div>
                    <div style="font-size: 0.95rem; color: var(--neutral-600); margin-bottom: 1.5rem; line-height: 1.5;">
                        Download a comprehensive PDF report with analysis results, disclaimers, and professional formatting suitable for healthcare consultations.
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                pdf_bytes = create_pdf(st.session_state.original_image, st.session_state.analysis_results)
                if pdf_bytes:
                    download_filename = f"mediscan_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    st.download_button(
                        label="📥 Download Professional Report (PDF)",
                        data=pdf_bytes,
                        file_name=download_filename,
                        mime="application/pdf",
                        key="download_pdf",
                        use_container_width=True,
                        help="Download a professionally formatted PDF report with complete analysis results"
                    )
        else:
            # Enhanced waiting state with medical theming
            st.markdown("""
            <div class="card" style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 450px; text-align: center; background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(239, 246, 255, 0.9));">
                <div style="color: var(--primary-blue); font-size: 5rem; margin-bottom: 1.5rem; animation: pulse 2s infinite;">🏥</div>
                <div style="font-weight: 700; font-size: 1.4rem; color: var(--primary-dark); margin-bottom: 0.75rem;">MediScan Ready</div>
                <div style="color: var(--neutral-600); font-size: 1.05rem; line-height: 1.6; max-width: 350px;">
                    Upload a tablet image and click <strong>"Analyze Tablet Composition"</strong> to receive comprehensive pharmaceutical analysis powered by advanced AI
                </div>
                <div style="margin-top: 2rem; display: flex; gap: 0.75rem; flex-wrap: wrap; justify-content: center;">
                    <div style="background: rgba(30, 64, 175, 0.1); padding: 0.4rem 0.8rem; border-radius: 15px; font-size: 0.8rem; color: var(--primary-blue); font-weight: 500;">🧬 Composition Analysis</div>
                    <div style="background: rgba(5, 150, 105, 0.1); padding: 0.4rem 0.8rem; border-radius: 15px; font-size: 0.8rem; color: var(--accent-green); font-weight: 500;">💊 Medical Uses</div>
                    <div style="background: rgba(245, 158, 11, 0.1); padding: 0.4rem 0.8rem; border-radius: 15px; font-size: 0.8rem; color: var(--warning-amber); font-weight: 500;">⚠️ Side Effects</div>
                    <div style="background: rgba(59, 130, 246, 0.1); padding: 0.4rem 0.8rem; border-radius: 15px; font-size: 0.8rem; color: var(--secondary-blue); font-weight: 500;">💰 Cost Information</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Enhanced professional footer
    st.markdown("""
    <div class="medical-footer">
        <div style="max-width: 800px; margin: 0 auto; padding: 0 1rem;">
            <div style="font-weight: 600; color: var(--primary-dark); margin-bottom: 1rem; font-size: 1.1rem;">
                🏥 MediScan - Professional Drug Composition Analyzer
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 1.5rem; text-align: left;">
                <div>
                    <div style="font-weight: 600; color: var(--primary-blue); margin-bottom: 0.5rem;">🔬 Technology</div>
                    <div style="font-size: 0.85rem; line-height: 1.4;">Advanced AI-powered pharmaceutical analysis using Google Gemini and Tavily research tools</div>
                </div>
                <div>
                    <div style="font-weight: 600; color: var(--accent-green); margin-bottom: 0.5rem;">🛡️ Privacy</div>
                    <div style="font-size: 0.85rem; line-height: 1.4;">Your images and data are processed securely and not stored permanently</div>
                </div>
                <div>
                    <div style="font-weight: 600; color: var(--warning-amber); margin-bottom: 0.5rem;">⚠️ Disclaimer</div>
                    <div style="font-size: 0.85rem; line-height: 1.4;">For educational purposes only. Always consult healthcare professionals</div>
                </div>
            </div>
            <div style="padding-top: 1rem; border-top: 1px solid var(--neutral-300); font-size: 0.8rem; color: var(--neutral-500);">
                © 2025 MediScan Drug Composition Analyzer | Powered by Gemini AI + Tavily Research | Version 2.0
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
