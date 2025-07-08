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
import time

# Set page configuration
st.set_page_config(
    page_title="MediScan - AI Drug Analyzer",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏥"
)

# Custom CSS for enhanced UI
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Container */
    .main-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        animation: fadeInUp 0.8s ease-out;
    }
    
    /* Animations */
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
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    /* Header Styling */
    .main-header {
        text-align: center;
        background: linear-gradient(45deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 1rem;
        animation: slideIn 1s ease-out;
    }
    
    .subtitle {
        text-align: center;
        color: #64748b;
        font-size: 1.2rem;
        margin-bottom: 2rem;
        animation: slideIn 1.2s ease-out;
    }
    
    /* Card Styling */
    .feature-card {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
        animation: fadeInUp 0.6s ease-out;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }
    
    .upload-card {
        background: linear-gradient(135deg, #e0f2fe 0%, #b3e5fc 100%);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        border: 2px dashed #29b6f6;
        text-align: center;
        transition: all 0.3s ease;
        animation: fadeInUp 0.8s ease-out;
    }
    
    .upload-card:hover {
        border-color: #0288d1;
        background: linear-gradient(135deg, #b3e5fc 0%, #81d4fa 100%);
        transform: scale(1.02);
    }
    
    .results-card {
        background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        border-left: 4px solid #9c27b0;
        animation: slideIn 0.8s ease-out;
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(45deg, #667eea, #764ba2) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        animation: pulse 2s infinite !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4) !important;
        animation: none !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Download Button */
    .stDownloadButton > button {
        background: linear-gradient(45deg, #4caf50, #8bc34a) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3) !important;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(76, 175, 80, 0.4) !important;
    }
    
    /* Alert Styling */
    .alert-success {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 1px solid #28a745;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        animation: slideIn 0.6s ease-out;
    }
    
    .alert-warning {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 1px solid #ffc107;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        animation: slideIn 0.6s ease-out;
    }
    
    .alert-error {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border: 1px solid #dc3545;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        animation: slideIn 0.6s ease-out;
    }
    
    .alert-info {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border: 1px solid #17a2b8;
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        animation: slideIn 0.6s ease-out;
    }
    
    /* Section Headers */
    .section-header {
        background: linear-gradient(45deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 1.5rem;
        font-weight: 600;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(102, 126, 234, 0.2);
        animation: slideIn 0.8s ease-out;
    }
    
    /* Safety Information Cards */
    .safety-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transition: all 0.3s ease;
        animation: fadeInUp 0.6s ease-out;
    }
    
    .safety-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    }
    
    .safety-card.success {
        border-left-color: #28a745;
        background: linear-gradient(135deg, #f8fff9 0%, #e8f5e8 100%);
    }
    
    .safety-card.warning {
        border-left-color: #ffc107;
        background: linear-gradient(135deg, #fffef7 0%, #fff3cd 100%);
    }
    
    .safety-card.error {
        border-left-color: #dc3545;
        background: linear-gradient(135deg, #fff8f8 0%, #f8d7da 100%);
    }
    
    /* Medication Names */
    .medication-name {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-radius: 8px;
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        display: inline-block;
        font-weight: 500;
        color: #1976d2;
        border: 1px solid #2196f3;
        transition: all 0.3s ease;
        animation: fadeInUp 0.4s ease-out;
    }
    
    .medication-name:hover {
        transform: scale(1.05);
        background: linear-gradient(135deg, #bbdefb 0%, #90caf9 100%);
    }
    
    /* Progress Bar */
    .progress-bar {
        background: linear-gradient(90deg, #667eea, #764ba2);
        height: 4px;
        border-radius: 2px;
        animation: pulse 2s infinite;
    }
    
    /* Disclaimer Box */
    .disclaimer-box {
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
        border: 2px solid #f44336;
        border-radius: 16px;
        padding: 2rem;
        margin: 2rem 0;
        animation: fadeInUp 1s ease-out;
    }
    
    /* Image Container */
    .image-container {
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
        transition: all 0.3s ease;
        animation: fadeInUp 0.6s ease-out;
    }
    
    .image-container:hover {
        transform: scale(1.02);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
    }
    
    /* Interaction Analysis */
    .interaction-analysis {
        background: linear-gradient(135deg, #fff9c4 0%, #f0f4c3 100%);
        border-radius: 16px;
        padding: 2rem;
        margin: 2rem 0;
        border: 1px solid #fbc02d;
        animation: slideIn 0.8s ease-out;
    }
    
    .interaction-severe {
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
        border-color: #f44336;
    }
    
    .interaction-moderate {
        background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
        border-color: #ff9800;
    }
    
    .interaction-minor {
        background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
        border-color: #4caf50;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: 16px;
        margin-top: 3rem;
        color: #64748b;
        animation: fadeInUp 1.2s ease-out;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
        }
        
        .feature-card, .upload-card, .results-card {
            margin: 0.5rem 0;
            padding: 1.5rem;
        }
    }
    
    /* Loading Animation */
    .loading {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 2rem;
    }
    
    .spinner {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Hide Streamlit Default Elements */
    .stDeployButton {
        display: none;
    }
    
    #MainMenu {
        visibility: hidden;
    }
    
    footer {
        visibility: hidden;
    }
    
    header {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)

# API Keys
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")

# Check if API keys are available
if not TAVILY_API_KEY or not GOOGLE_API_KEY:
    st.error("🔑 API keys are missing. Please check your configuration.")
    st.stop()

MAX_IMAGE_WIDTH = 300

SYSTEM_PROMPT = """
You are an expert in pharmaceutical analysis and AI-driven drug composition recognition with specialized knowledge in drug safety and interactions.
Your role is to analyze a tablet's composition from an image, identify its ingredients, and provide comprehensive insights about the drug including safety considerations.

Additionally, once a drug composition is identified, retrieve and display its uses, side effects, cost, available tablet names/brands, usage instructions, and critical safety information using reliable medical sources.
Ensure that you fetch accurate and specific details instead of generic placeholders.
"""

INSTRUCTIONS = """
- Extract only the drug composition from the tablet image.
- Use this composition to fetch and return detailed information from trusted medical sources.
- For tablet names, search for brand names, generic names, and commercial names that contain the identified composition.
- Provide comprehensive safety information including alcohol interactions, pregnancy safety, breastfeeding considerations, and driving safety.
- Return all information in a structured format:
  *Composition:* <composition>
  *Available Tablet Names:* <list of brand names and generic names that contain this composition>
  *Uses:* <accurate uses based on online sources>
  *How to Use:* <detailed dosage instructions, timing, with or without food>
  *Side Effects:* <verified side effects>
  *Cost:* <actual cost from trusted sources>
  *Safety with Alcohol:* <specific advice about alcohol consumption>
  *Pregnancy Safety:* <pregnancy category and safety advice>
  *Breastfeeding Safety:* <safety for nursing mothers>
  *Driving Safety:* <effects on driving ability>
  *General Safety Advice:* <additional precautions and contraindications>
"""

DRUG_INTERACTION_PROMPT = """
You are a pharmaceutical expert specializing in drug interactions and safety analysis.
Analyze the potential interactions between the identified drug composition and the additional medications provided by the user.

Provide detailed interaction analysis including:
- Severity level of interactions (None, Minor, Moderate, Major, Severe)
- Specific interaction mechanisms
- Clinical significance
- Recommended actions or precautions
- Alternative suggestions if dangerous interactions exist

Be thorough and prioritize patient safety in your analysis.
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

@st.cache_resource
def get_interaction_agent():
    """Initialize and cache the drug interaction agent."""
    try:
        return Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY),
            system_prompt=DRUG_INTERACTION_PROMPT,
            tools=[TavilyTools(api_key=TAVILY_API_KEY)],
            markdown=True,
        )
    except Exception as e:
        st.error(f"❌ Error initializing interaction agent: {e}")
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
        # Show loading animation
        progress_placeholder = st.empty()
        with progress_placeholder.container():
            st.markdown('<div class="loading"><div class="spinner"></div></div>', unsafe_allow_html=True)
            st.markdown("### 🔬 Analyzing tablet image...")
            
            # Add progress bar
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.02)
                progress_bar.progress(i + 1)
        
        progress_placeholder.empty()
        
        with st.spinner("🔍 Extracting composition and retrieving medical information..."):
            response = agent.run(
                "Extract the drug composition from this tablet image and provide its uses, side effects, cost, available tablet names/brands, usage instructions, and comprehensive safety information including alcohol interactions, pregnancy safety, breastfeeding considerations, and driving safety.",
                images=[image_path],
            )
            return response.content.strip()
    except Exception as e:
        st.error(f"🚨 Error extracting composition and details: {e}")
        return None

def analyze_drug_interactions(drug_composition, additional_medications):
    """Analyze potential drug interactions."""
    if not additional_medications.strip():
        return None
    
    interaction_agent = get_interaction_agent()
    if interaction_agent is None:
        return None

    try:
        with st.spinner("💊 Analyzing drug interactions..."):
            query = f"""
            Analyze potential drug interactions between:
            Primary Drug: {drug_composition}
            Additional Medications: {additional_medications}
            
            Provide detailed interaction analysis with severity levels and safety recommendations.
            """
            response = interaction_agent.run(query)
            return response.content.strip()
    except Exception as e:
        st.error(f"🚨 Error analyzing drug interactions: {e}")
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

def create_pdf(image_data, analysis_results, interaction_analysis=None, additional_meds=None):
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
        content.append(Paragraph("🏥 MediScan - Comprehensive Drug Analysis Report", title_style))
        content.append(Spacer(1, 0.25*inch))
        
        # Disclaimer
        content.append(Paragraph(
            "⚠️ MEDICAL DISCLAIMER: This information is provided for educational purposes only and should not replace professional medical advice. "
            "Always consult with a healthcare professional before making any medical decisions or changes to your medication regimen.",
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
        content.append(Paragraph("🔬 Drug Analysis Results:", heading_style))
        
        # Format the analysis results for PDF
        if analysis_results:
            # Use regex to find sections
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
        
        # Drug interaction analysis
        if interaction_analysis and additional_meds:
            content.append(Paragraph("💊 Drug Interaction Analysis:", heading_style))
            content.append(Paragraph(f"<b>Additional Medications:</b> {additional_meds}", normal_style))
            content.append(Spacer(1, 0.1*inch))
            
            clean_interaction = interaction_analysis.replace('<', '&lt;').replace('>', '&gt;')
            content.append(Paragraph(clean_interaction, normal_style))
            content.append(Spacer(1, 0.25*inch))
        
        # Footer
        content.append(Spacer(1, 0.5*inch))
        content.append(Paragraph("© 2025 MediScan - Comprehensive Drug Analyzer | Powered by Gemini AI + Tavily", 
                                ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.gray)))
        
        # Build PDF
        pdf.build(content)
        
        # Get the PDF value from the buffer
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"📄 Error creating PDF: {e}")
        return None

def display_tablet_names(tablet_names_text):
    """Display tablet names in a formatted way."""
    if not tablet_names_text:
        return
    
    # Try to parse the tablet names into a list
    tablet_names = []
    
    # Split by common delimiters
    for delimiter in ['\n', ',', ';', '•', '-']:
        if delimiter in tablet_names_text:
            names = tablet_names_text.split(delimiter)
            tablet_names = [name.strip() for name in names if name.strip()]
            break
    
    # If no delimiters found, treat as single text
    if not tablet_names:
        tablet_names = [tablet_names_text.strip()]
    
    # Display in a more visually appealing way
    if len(tablet_names) > 1:
        st.markdown('<div style="margin: 1rem 0;">', unsafe_allow_html=True)
        for name in tablet_names:
            if name:
                st.markdown(f'<div class="medication-name">🏷️ {name}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="medication-name">🏷️ {tablet_names[0] if tablet_names else tablet_names_text}</div>', unsafe_allow_html=True)

def display_safety_info(content, safety_type):
    """Display safety information with appropriate styling."""
    if not content:
        return
    
    # Color coding for different safety levels
    if "safe" in content.lower() or "no interaction" in content.lower():
        st.markdown(f'<div class="safety-card success">✅ <strong>{safety_type}:</strong><br>{content}</div>', unsafe_allow_html=True)
    elif "avoid" in content.lower() or "contraindicated" in content.lower() or "not recommended" in content.lower():
        st.markdown(f'<div class="safety-card error">❌ <strong>{safety_type}:</strong><br>{content}</div>', unsafe_allow_html=True)
    elif "caution" in content.lower() or "monitor" in content.lower() or "consult" in content.lower():
        st.markdown(f'<div class="safety-card warning">⚠️ <strong>{safety_type}:</strong><br>{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="safety-card">ℹ️ <strong>{safety_type}:</strong><br>{content}</div>', unsafe_allow_html=True)

def main():
    # Initialize session state for button tracking
    if 'analyze_clicked' not in st.session_state:
        st.session_state.analyze_clicked = False
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'original_image' not in st.session_state:
        st.session_state.original_image = None
    if 'drug_composition' not in st.session_state:
        st.session_state.drug_composition = None
    if 'interaction_analysis' not in st.session_state:
        st.session_state.interaction_analysis = None
    if 'additional_medications' not in st.session_state:
        st.session_state.additional_medications = ""

    # Main container
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # Header
    st.markdown('<h1 class="main-header">🏥 MediScan</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">AI-Powered Drug Composition Analyzer & Safety Checker</p>', unsafe_allow_html=True)
    
    # Medical disclaimer
    st.markdown("""
    <div class="disclaimer-box">
        <h3 style="color: #f44336; margin-bottom: 1rem;">⚠️ MEDICAL DISCLAIMER</h3>
        <p style="margin-bottom: 0.5rem;">The information provided by MediScan is for educational and informational purposes only and is not intended to replace professional medical advice, diagnosis, or treatment.</p>
        <p style="margin: 0;"><strong>Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition, medication, or drug interactions.</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content in two columns
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">📤 Upload Tablet Image</h2>', unsafe_allow_html=True)
        
        st.markdown('<div class="upload-card">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "📷 Choose a clear image of the tablet",
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload a clear, high-quality image of the tablet or its packaging for accurate analysis",
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            # Display uploaded image with enhanced styling
            resized_image = resize_image_for_display(uploaded_file)
            if resized_image:
                st.markdown('<div class="image-container">', unsafe_allow_html=True)
                st.image(resized_image, caption="📸 Uploaded Tablet Image", width=MAX_IMAGE_WIDTH)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Display file info with better formatting
                file_size = len(uploaded_file.getvalue()) / 1024  # Convert to KB
                st.markdown(f"""
                <div style="text-align: center; margin-top: 1rem; padding: 1rem; background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%); border-radius: 8px;">
                    <strong>📄 {uploaded_file.name}</strong> • {file_size:.1f} KB
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; color: #64748b;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">📱</div>
                <h3>Upload Your Tablet Image</h3>
                <p>Drag and drop or click to browse</p>
                <p style="font-size: 0.9rem; color: #94a3b8;">Supported formats: JPG, JPEG, PNG, WEBP</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Additional medications input with enhanced styling
        st.markdown('<h2 class="section-header">💊 Additional Medications</h2>', unsafe_allow_html=True)
        st.markdown('<div class="feature-card">', unsafe_allow_html=True)
        
        additional_meds = st.text_area(
            "Enter any other medications you are currently taking:",
            placeholder="e.g., Aspirin 75mg daily, Metformin 500mg twice daily, Lisinopril 10mg once daily",
            help="Include medication names, dosages, and frequency. This helps check for potential drug interactions.",
            key="additional_medications_input",
            height=100
        )
        
        st.markdown('<p style="font-size: 0.9rem; color: #64748b; margin-top: 0.5rem;">💡 Include dosages and frequency for better interaction analysis</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Analyze button with enhanced styling
        if uploaded_file:
            st.markdown('<div style="text-align: center; margin: 2rem 0;">', unsafe_allow_html=True)
            if st.button("🔬 Analyze Tablet & Check Safety", key="analyze_btn", use_container_width=True):
                st.session_state.analyze_clicked = True
                st.session_state.additional_medications = additional_meds
                
                # Save uploaded file and analyze
                temp_path = save_uploaded_file(uploaded_file)
                if temp_path:
                    try:
                        extracted_info = extract_composition_and_details(temp_path)
                        
                        if extracted_info:
                            # Store results in session state
                            st.session_state.analysis_results = extracted_info
                            st.session_state.original_image = uploaded_file.getvalue()
                            
                            # Extract drug composition for interaction analysis
                            composition_match = re.search(r"\*Composition:\*(.*?)(?=\*[\w\s]+:\*|$)", extracted_info, re.DOTALL | re.IGNORECASE)
                            if composition_match:
                                st.session_state.drug_composition = composition_match.group(1).strip()
                            
                            # Analyze drug interactions if additional medications provided
                            if additional_meds.strip():
                                interaction_result = analyze_drug_interactions(
                                    st.session_state.drug_composition or "Unknown composition",
                                    additional_meds
                                )
                                st.session_state.interaction_analysis = interaction_result
                            
                            st.markdown("""
                            <div class="alert-success">
                                <strong>✅ Analysis Complete!</strong><br>
                                Comprehensive drug analysis has been completed successfully. Check the results panel for detailed information.
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div class="alert-error">
                                <strong>❌ Analysis Failed</strong><br>
                                Please try with a clearer image or different angle.
                            </div>
                            """, unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.markdown(f"""
                        <div class="alert-error">
                            <strong>🚨 Analysis Error</strong><br>
                            {str(e)}
                        </div>
                        """, unsafe_allow_html=True)
                    finally:
                        # Clean up temp file
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; margin: 2rem 0; padding: 1rem; background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); border-radius: 12px; border: 2px dashed #cbd5e1;">
                <p style="color: #64748b; margin: 0;">📤 Please upload a tablet image to begin analysis</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="results-card">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">📊 Analysis Results</h2>', unsafe_allow_html=True)
        
        # Display results if available
        if st.session_state.analysis_results:
            st.markdown('<div class="feature-card">', unsafe_allow_html=True)
            st.markdown("### 🔬 Comprehensive Drug Analysis")
            
            # Parse and display results
            analysis_text = st.session_state.analysis_results
            
            # Enhanced sections list
            sections = [
                "Composition", "Available Tablet Names", "Uses", "How to Use",
                "Side Effects", "Cost", "Safety with Alcohol", "Pregnancy Safety",
                "Breastfeeding Safety", "Driving Safety", "General Safety Advice"
            ]
            
            for section in sections:
                # Pattern to match sections
                pattern = rf"\*{re.escape(section)}:\*(.*?)(?=\*(?:{'|'.join(re.escape(s) for s in sections)}):\*|$)"
                match = re.search(pattern, analysis_text, re.DOTALL | re.IGNORECASE)
                
                if match:
                    content = match.group(1).strip()
                    
                    # Choose appropriate icon for each section
                    icons = {
                        "Composition": "🧬",
                        "Available Tablet Names": "🏷️",
                        "Uses": "💊",
                        "How to Use": "📋",
                        "Side Effects": "⚠️",
                        "Cost": "💰",
                        "Safety with Alcohol": "🍺",
                        "Pregnancy Safety": "🤱",
                        "Breastfeeding Safety": "🍼",
                        "Driving Safety": "🚗",
                        "General Safety Advice": "🛡️"
                    }
                    
                    st.markdown(f"**{icons.get(section, '📋')} {section}:**")
                    
                    # Special handling for different sections
                    if section == "Available Tablet Names":
                        display_tablet_names(content)
                    elif section in ["Safety with Alcohol", "Pregnancy Safety", "Breastfeeding Safety", "Driving Safety"]:
                        display_safety_info(content, section)
                    else:
                        st.markdown(f'<div class="safety-card"><p style="margin: 0;">{content}</p></div>', unsafe_allow_html=True)
                    
                    st.markdown('<div style="margin: 1rem 0; height: 2px; background: linear-gradient(90deg, #667eea, #764ba2); opacity: 0.3;"></div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Display drug interaction analysis if available
            if st.session_state.interaction_analysis:
                st.markdown('<div class="interaction-analysis">', unsafe_allow_html=True)
                st.markdown("### 💊 Drug Interaction Analysis")
                st.markdown(f"**Additional Medications:** {st.session_state.additional_medications}")
                
                # Parse interaction analysis for severity levels
                interaction_text = st.session_state.interaction_analysis
                
                if "severe" in interaction_text.lower() or "major" in interaction_text.lower():
                    st.markdown("""
                    <div class="interaction-analysis interaction-severe">
                        <h4 style="color: #f44336; margin-bottom: 1rem;">🚨 SEVERE/MAJOR INTERACTION DETECTED</h4>
                    </div>
                    """, unsafe_allow_html=True)
                elif "moderate" in interaction_text.lower():
                    st.markdown("""
                    <div class="interaction-analysis interaction-moderate">
                        <h4 style="color: #ff9800; margin-bottom: 1rem;">⚠️ MODERATE INTERACTION</h4>
                    </div>
                    """, unsafe_allow_html=True)
                elif "minor" in interaction_text.lower():
                    st.markdown("""
                    <div class="interaction-analysis interaction-minor">
                        <h4 style="color: #4caf50; margin-bottom: 1rem;">ℹ️ MINOR INTERACTION</h4>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="interaction-analysis interaction-minor">
                        <h4 style="color: #4caf50; margin-bottom: 1rem;">✅ LOW INTERACTION RISK</h4>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown(f'<div class="safety-card"><p style="margin: 0;">{interaction_text}</p></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # PDF download section with enhanced styling
            if st.session_state.original_image:
                st.markdown('<div class="feature-card">', unsafe_allow_html=True)
                st.markdown("### 📄 Download Complete Report")
                
                pdf_bytes = create_pdf(
                    st.session_state.original_image,
                    st.session_state.analysis_results,
                    st.session_state.interaction_analysis,
                    st.session_state.additional_medications
                )
                if pdf_bytes:
                    download_filename = f"mediscan_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    st.download_button(
                        label="📥 Download Complete PDF Report",
                        data=pdf_bytes,
                        file_name=download_filename,
                        mime="application/pdf",
                        help="Download a comprehensive PDF report with all analysis results and safety information",
                        use_container_width=True
                    )
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; padding: 3rem; color: #64748b;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🔍</div>
                <h3>Ready for Analysis</h3>
                <p>Upload a tablet image and click 'Analyze' to see comprehensive results here.</p>
                <div style="margin-top: 2rem; padding: 1rem; background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%); border-radius: 12px;">
                    <strong>What you'll get:</strong>
                    <ul style="text-align: left; margin-top: 0.5rem; color: #2e7d32;">
                        <li>🧬 Drug composition analysis</li>
                        <li>💊 Medical uses and dosage</li>
                        <li>⚠️ Side effects and precautions</li>
                        <li>🔍 Drug interaction checking</li>
                        <li>📄 Downloadable PDF report</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Additional Safety Information Section
    if st.session_state.analysis_results:
        st.markdown('<div style="margin-top: 3rem;">', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">🛡️ Important Safety Reminders</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            st.markdown("""
            <div class="safety-card">
                <h4 style="color: #667eea; margin-bottom: 1rem;">🍺 Alcohol Interactions</h4>
                <ul style="margin: 0; padding-left: 1.5rem;">
                    <li>Always check the specific alcohol interaction information above</li>
                    <li>Some medications can cause severe reactions with alcohol</li>
                    <li>Consult your doctor about alcohol consumption while on medication</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="safety-card">
                <h4 style="color: #667eea; margin-bottom: 1rem;">🤱 Pregnancy & Breastfeeding</h4>
                <ul style="margin: 0; padding-left: 1.5rem;">
                    <li>Medication safety varies by trimester</li>
                    <li>Many drugs can pass through breast milk</li>
                    <li>Always inform your healthcare provider if you're pregnant or breastfeeding</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="safety-card">
                <h4 style="color: #667eea; margin-bottom: 1rem;">🚗 Driving Safety</h4>
                <ul style="margin: 0; padding-left: 1.5rem;">
                    <li>Some medications can cause drowsiness or dizziness</li>
                    <li>Check the driving safety information above</li>
                    <li>Avoid driving if you feel impaired</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="safety-card">
                <h4 style="color: #667eea; margin-bottom: 1rem;">💊 Drug Interactions</h4>
                <ul style="margin: 0; padding-left: 1.5rem;">
                    <li>Always provide a complete list of medications to your doctor</li>
                    <li>Include over-the-counter drugs and supplements</li>
                    <li>Check for interactions before starting new medications</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div class="footer">
        <p style="font-size: 1.1rem; font-weight: 500; margin-bottom: 0.5rem;">🏥 MediScan - AI-Powered Drug Analysis</p>
        <p style="margin: 0;">© 2025 MediScan | Powered by Gemini AI + Tavily | Made with ❤️ for Healthcare</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
