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

# Set page configuration
st.set_page_config(
    page_title="MediScan - Drug Composition Analyzer",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏥"
)

# Custom CSS for white theme with good contrast
st.markdown("""
<style>
    /* Global styles */
    .stApp {
        background-color: #ffffff;
        color: #1a1a1a;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #2c5aa0 0%, #1e3a8a 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
        border: 1px solid #e5e7eb;
    }
    
    .main-header h1 {
        color: white !important;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        color: #f0f9ff;
        font-size: 1.1rem;
        margin: 0;
    }
    
    /* Disclaimer banner */
    .disclaimer-banner {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 2px solid #dc2626;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .disclaimer-banner .stAlert {
        background: transparent !important;
        border: none !important;
        color: white !important;
    }
    
    /* Section cards */
    .section-card {
        background: #f8fafc;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    
    .section-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Upload section */
    .upload-section {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border: 2px dashed #3b82f6;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .upload-section:hover {
        border-color: #1d4ed8;
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        border: 2px solid #16a34a;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #15803d 0%, #166534 100%);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
        border-color: #15803d;
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
        color: white;
        border: 2px solid #7c3aed;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #6d28d9 0%, #5b21b6 100%);
        border-color: #6d28d9;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        transform: translateY(-2px);
    }
    
    /* Results section */
    .results-section {
        background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
        border: 2px solid #22c55e;
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    /* Analysis card */
    .analysis-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #3b82f6;
    }
    
    /* Safety information cards */
    .safety-success {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 2px solid #22c55e;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #166534;
    }
    
    .safety-warning {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border: 2px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #92400e;
    }
    
    .safety-error {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        border: 2px solid #ef4444;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #b91c1c;
    }
    
    .safety-info {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border: 2px solid #3b82f6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #1e40af;
    }
    
    /* Interaction analysis */
    .interaction-severe {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        border: 3px solid #dc2626;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #991b1b;
        font-weight: 600;
    }
    
    .interaction-moderate {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border: 3px solid #d97706;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #92400e;
        font-weight: 600;
    }
    
    .interaction-minor {
        background: linear-gradient(135deg, #f0f9ff 0%, #dbeafe 100%);
        border: 3px solid #2563eb;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #1d4ed8;
        font-weight: 600;
    }
    
    .interaction-low {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 3px solid #16a34a;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #15803d;
        font-weight: 600;
    }
    
    /* Text area styling */
    .stTextArea textarea {
        border: 2px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        font-size: 1rem;
        background: white;
        transition: border-color 0.3s ease;
    }
    
    .stTextArea textarea:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* File uploader */
    .stFileUploader {
        background: white;
        border: 2px dashed #d1d5db;
        border-radius: 8px;
        padding: 1rem;
        transition: all 0.3s ease;
    }
    
    .stFileUploader:hover {
        border-color: #3b82f6;
        background: #f8fafc;
    }
    
    /* Tablet names display */
    .tablet-name {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        font-weight: 500;
        color: #374151;
        border-left: 4px solid #6366f1;
    }
    
    /* Footer */
    .footer {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-top: 2px solid #e2e8f0;
        padding: 2rem;
        margin-top: 3rem;
        text-align: center;
        color: #64748b;
        border-radius: 10px;
    }
    
    /* Improved readability */
    .stMarkdown {
        line-height: 1.6;
    }
    
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #1e293b;
        font-weight: 700;
    }
    
    .stMarkdown h2 {
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }
    
    .stMarkdown h3 {
        color: #475569;
        margin-top: 1.5rem;
    }
    
    /* Info messages */
    .stInfo {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border: 2px solid #0ea5e9;
        border-radius: 8px;
        color: #0c4a6e;
    }
    
    .stSuccess {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 2px solid #22c55e;
        border-radius: 8px;
        color: #166534;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border: 2px solid #f59e0b;
        border-radius: 8px;
        color: #92400e;
    }
    
    .stError {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        border: 2px solid #ef4444;
        border-radius: 8px;
        color: #b91c1c;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(to right, #e2e8f0, #cbd5e1, #e2e8f0);
        margin: 2rem 0;
        border-radius: 1px;
    }
    
    /* Spinner */
    .stSpinner {
        border-color: #3b82f6 !important;
    }
    
    /* Image container */
    .image-container {
        background: white;
        border: 2px solid #e5e7eb;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        
        .section-card {
            padding: 1rem;
        }
        
        .stButton > button,
        .stDownloadButton > button {
            padding: 0.5rem 1rem;
            font-size: 0.9rem;
        }
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
        with st.spinner("🔬 Analyzing tablet image and retrieving comprehensive medical information..."):
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
        with st.spinner("🔍 Analyzing drug interactions..."):
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
    
    # Display in columns for better readability
    if len(tablet_names) > 1:
        # Create columns based on number of names
        num_cols = min(3, len(tablet_names))
        cols = st.columns(num_cols)
        
        for i, name in enumerate(tablet_names):
            if name:  # Only display non-empty names
                with cols[i % num_cols]:
                    st.markdown(f'<div class="tablet-name">🏷️ <strong>{name}</strong></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="tablet-name">🏷️ <strong>{tablet_names[0] if tablet_names else tablet_names_text}</strong></div>', unsafe_allow_html=True)

def display_safety_info(content, safety_type):
    """Display safety information with appropriate styling."""
    if not content:
        return
    
    # Color coding for different safety levels
    if "safe" in content.lower() or "no interaction" in content.lower():
        st.markdown(f'<div class="safety-success">✅ {content}</div>', unsafe_allow_html=True)
    elif "avoid" in content.lower() or "contraindicated" in content.lower() or "not recommended" in content.lower():
        st.markdown(f'<div class="safety-error">❌ {content}</div>', unsafe_allow_html=True)
    elif "caution" in content.lower() or "monitor" in content.lower() or "consult" in content.lower():
        st.markdown(f'<div class="safety-warning">⚠️ {content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="safety-info">ℹ️ {content}</div>', unsafe_allow_html=True)

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

    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏥 MediScan</h1>
        <p>Comprehensive Drug Composition Analyzer with AI-Powered Safety Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Medical disclaimer
    st.markdown("""
    <div class="disclaimer-banner">
        <div class="stAlert">
            <h3>⚠️ MEDICAL DISCLAIMER</h3>
            <p>The information provided by MediScan is for educational and informational purposes only and is not intended to replace professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition, medication, or drug interactions.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content in two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### 📤 Upload Tablet Image")
        
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload a clear image of the tablet",
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload a clear, high-quality image of the tablet or its packaging"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        if uploaded_file:
            # Display uploaded image
            st.markdown('<div class="image-container">', unsafe_allow_html=True)
            resized_image = resize_image_for_display(uploaded_file)
            if resized_image:
                st.image(resized_image, caption="Uploaded Tablet Image", width=MAX_IMAGE_WIDTH)
                
                # Display file info
                file_size = len(uploaded_file.getvalue()) / 1024  # Convert to KB
                st.info(f"**{uploaded_file.name}** • {file_size:.1f} KB")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Additional medications input
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### 💊 Additional Medications (Optional)")
        additional_meds = st.text_area(
            "Enter any other medications you are currently taking:",
            placeholder="e.g., Aspirin 75mg daily, Metformin 500mg twice daily, Lisinopril 10mg once daily",
            help="Include medication names, dosages, and frequency. This helps check for potential drug interactions.",
            key="additional_medications_input"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Analyze button
        if uploaded_file:
            if st.button("🔬 Analyze Tablet & Check Safety", key="analyze_btn"):
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
                            
                            st.success("✅ Comprehensive analysis completed successfully!")
                        else:
                            st.error("❌ Analysis failed. Please try with a clearer image.")
                        
                    except Exception as e:
                        st.error(f"🚨 Analysis failed: {e}")
                    finally:
                        # Clean up temp file
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
        else:
            st.info("📸 Please upload a tablet image to begin analysis")
    
    with col2:
        st.markdown('<div class="results-section">', unsafe_allow_html=True)
        st.markdown("### 📊 Analysis Results")
        
        # Display results if available
        if st.session_state.analysis_results:
            st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
            st.markdown("#### 🔬 Comprehensive Drug Analysis")
            
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
                        st.write(content)
                    
                    st.markdown("---")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Display drug interaction analysis if available
            if st.session_state.interaction_analysis:
                st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
                st.markdown("#### 💊 Drug Interaction Analysis")
                st.markdown(f"**Additional Medications:** {st.session_state.additional_medications}")
                
                # Parse interaction analysis for severity levels
                interaction_text = st.session_state.interaction_analysis
                
                if "severe" in interaction_text.lower() or "major" in interaction_text.lower():
                    st.markdown('<div class="interaction-severe">🚨 <strong>SEVERE/MAJOR INTERACTION DETECTED</strong></div>', unsafe_allow_html=True)
                elif "moderate" in interaction_text.lower():
                    st.markdown('<div class="interaction-moderate">⚠️ <strong>MODERATE INTERACTION</strong></div>', unsafe_allow_html=True)
                elif "minor" in interaction_text.lower():
                    st.markdown('<div class="interaction-minor">ℹ️ <strong>MINOR INTERACTION</strong></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="interaction-low">✅ <strong>LOW INTERACTION RISK</strong></div>', unsafe_allow_html=True)
                
                st.write(interaction_text)
                st.markdown("---")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # PDF download section
            if st.session_state.original_image:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                st.markdown("#### 📄 Download Comprehensive Report")
                
                pdf_bytes = create_pdf(
                    st.session_state.original_image,
                    st.session_state.analysis_results,
                    st.session_state.interaction_analysis,
                    st.session_state.additional_medications
                )
                if pdf_bytes:
                    download_filename = f"mediscan_comprehensive_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    st.download_button(
                        label="📥 Download Complete PDF Report",
                        data=pdf_bytes,
                        file_name=download_filename,
                        mime="application/pdf",
                        help="Download a comprehensive PDF report with all analysis results and safety information"
                    )
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Upload a tablet image and click 'Analyze Tablet & Check Safety' to see comprehensive results here.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Additional Safety Information Section
    if st.session_state.analysis_results:
        st.markdown("---")
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("### 🛡️ Important Safety Reminders")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="safety-info">
                <h4>🍺 Alcohol Interaction:</h4>
                <ul>
                    <li>Always check the specific alcohol interaction information above</li>
                    <li>Some medications can cause severe reactions with alcohol</li>
                    <li>Consult your doctor about alcohol consumption while on medication</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="safety-info">
                <h4>🤱 Pregnancy & Breastfeeding:</h4>
                <ul>
                    <li>Medication safety varies by trimester</li>
                    <li>Many drugs can pass through breast milk</li>
                    <li>Always inform your healthcare provider if you're pregnant or breastfeeding</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="safety-info">
                <h4>🚗 Driving Safety:</h4>
                <ul>
                    <li>Some medications can cause drowsiness or dizziness</li>
                    <li>Check the driving safety information above</li>
                    <li>Avoid driving if you feel impaired</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="safety-info">
                <h4>💊 Drug Interactions:</h4>
                <ul>
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
        <p>© 2025 MediScan - Comprehensive Drug Analyzer</p>
        <p>Powered by Gemini AI + Tavily | Designed for Healthcare Excellence</p>
        <p><small>Always consult healthcare professionals for medical advice</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
