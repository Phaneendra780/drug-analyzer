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

# Custom CSS for enhanced UI
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Main Title */
    .main-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    
    .main-title h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-title p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Warning Banner */
    .warning-banner {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        border-left: 5px solid #c23616;
        box-shadow: 0 4px 15px rgba(238, 90, 36, 0.3);
    }
    
    .warning-banner h3 {
        margin: 0 0 0.5rem 0;
        font-size: 1.3rem;
        font-weight: 600;
    }
    
    .warning-banner p {
        margin: 0;
        line-height: 1.6;
        font-size: 0.95rem;
    }
    
    /* Card Containers */
    .card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #e1e8ed;
        margin-bottom: 2rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }
    
    /* Section Headers */
    .section-header {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        font-weight: 600;
        font-size: 1.2rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
        box-shadow: 0 3px 10px rgba(79, 172, 254, 0.3);
    }
    
    /* Analysis Result Cards */
    .result-card {
        background: white;
        border: 2px solid #e1e8ed;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .result-card:before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    .result-card:hover {
        border-color: #667eea;
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.15);
    }
    
    .result-header {
        color: #2c3e50;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .result-content {
        color: #34495e;
        line-height: 1.6;
        font-size: 0.95rem;
    }
    
    /* Safety Status Cards */
    .safety-safe {
        background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        font-weight: 500;
        box-shadow: 0 3px 10px rgba(0, 184, 148, 0.3);
    }
    
    .safety-warning {
        background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        font-weight: 500;
        box-shadow: 0 3px 10px rgba(253, 203, 110, 0.3);
    }
    
    .safety-danger {
        background: linear-gradient(135deg, #d63031 0%, #74b9ff 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        font-weight: 500;
        box-shadow: 0 3px 10px rgba(214, 48, 49, 0.3);
    }
    
    .safety-info {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        font-weight: 500;
        box-shadow: 0 3px 10px rgba(116, 185, 255, 0.3);
    }
    
    /* Tablet Names Grid */
    .tablet-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .tablet-name {
        background: linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%);
        color: white;
        padding: 0.8rem 1rem;
        border-radius: 8px;
        text-align: center;
        font-weight: 500;
        box-shadow: 0 3px 10px rgba(108, 92, 231, 0.3);
        transition: transform 0.2s ease;
    }
    
    .tablet-name:hover {
        transform: translateY(-2px);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.8rem 2rem;
        border-radius: 25px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Download Button */
    .download-section {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin-top: 2rem;
        box-shadow: 0 4px 15px rgba(86, 171, 47, 0.3);
    }
    
    /* Interaction Analysis */
    .interaction-severe {
        background: linear-gradient(135deg, #d63031 0%, #e17055 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 5px solid #b71c1c;
        box-shadow: 0 4px 15px rgba(214, 48, 49, 0.3);
    }
    
    .interaction-moderate {
        background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 5px solid #f39c12;
        box-shadow: 0 4px 15px rgba(253, 203, 110, 0.3);
    }
    
    .interaction-minor {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 5px solid #3498db;
        box-shadow: 0 4px 15px rgba(116, 185, 255, 0.3);
    }
    
    .interaction-low {
        background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border-left: 5px solid #27ae60;
        box-shadow: 0 4px 15px rgba(0, 184, 148, 0.3);
    }
    
    /* Safety Reminders */
    .safety-reminders {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-top: 2rem;
        box-shadow: 0 6px 25px rgba(240, 147, 251, 0.3);
    }
    
    .safety-reminders h3 {
        margin-bottom: 1.5rem;
        font-size: 1.5rem;
        font-weight: 600;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    
    .safety-item {
        background: rgba(255, 255, 255, 0.1);
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid rgba(255, 255, 255, 0.5);
    }
    
    .safety-item h4 {
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    
    /* File Upload Area */
    .uploadedFile {
        background: white;
        border: 2px dashed #667eea;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .uploadedFile:hover {
        border-color: #764ba2;
        background: #f8f9ff;
    }
    
    /* Footer */
    .footer {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-top: 3rem;
        box-shadow: 0 4px 20px rgba(44, 62, 80, 0.3);
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main-title h1 {
            font-size: 2rem;
        }
        
        .card {
            padding: 1.5rem;
        }
        
        .tablet-grid {
            grid-template-columns: 1fr;
        }
    }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
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
        image_file.seek(0)
        img = Image.open(image_file)
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
        
        content = []
        
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
        
        content.append(Paragraph("🏥 MediScan - Comprehensive Drug Analysis Report", title_style))
        content.append(Spacer(1, 0.25*inch))
        
        content.append(Paragraph(
            "⚠️ MEDICAL DISCLAIMER: This information is provided for educational purposes only and should not replace professional medical advice. "
            "Always consult with a healthcare professional before making any medical decisions or changes to your medication regimen.",
            disclaimer_style
        ))
        content.append(Spacer(1, 0.25*inch))
        
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content.append(Paragraph(f"📅 Generated on: {current_datetime}", normal_style))
        content.append(Spacer(1, 0.25*inch))
        
        if image_data:
            try:
                img_temp = BytesIO(image_data)
                img = Image.open(img_temp)
                img_width, img_height = img.size
                aspect = img_height / float(img_width)
                display_width = 4 * inch
                display_height = display_width * aspect
                
                img_temp.seek(0)
                img_obj = ReportLabImage(img_temp, width=display_width, height=display_height)
                content.append(Paragraph("📸 Analyzed Image:", heading_style))
                content.append(img_obj)
                content.append(Spacer(1, 0.25*inch))
            except Exception as img_error:
                st.warning(f"Could not add image to PDF: {img_error}")
        
        content.append(Paragraph("🔬 Drug Analysis Results:", heading_style))
        
        if analysis_results:
            section_pattern = r"\*([\w\s]+):\*(.*?)(?=\*[\w\s]+:\*|$)"
            matches = re.findall(section_pattern, analysis_results, re.DOTALL | re.IGNORECASE)
            
            if matches:
                for section_title, section_content in matches:
                    content.append(Paragraph(f"<b>{section_title.strip()}:</b>", normal_style))
                    
                    paragraphs = section_content.strip().split("\n")
                    for para in paragraphs:
                        if para.strip():
                            clean_para = para.strip().replace('<', '&lt;').replace('>', '&gt;')
                            content.append(Paragraph(clean_para, normal_style))
                    
                    content.append(Spacer(1, 0.15*inch))
        
        if interaction_analysis and additional_meds:
            content.append(Paragraph("💊 Drug Interaction Analysis:", heading_style))
            content.append(Paragraph(f"<b>Additional Medications:</b> {additional_meds}", normal_style))
            content.append(Spacer(1, 0.1*inch))
            
            clean_interaction = interaction_analysis.replace('<', '&lt;').replace('>', '&gt;')
            content.append(Paragraph(clean_interaction, normal_style))
            content.append(Spacer(1, 0.25*inch))
        
        content.append(Spacer(1, 0.5*inch))
        content.append(Paragraph("© 2025 MediScan - Comprehensive Drug Analyzer | Powered by Gemini AI + Tavily", 
                                ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.gray)))
        
        pdf.build(content)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"📄 Error creating PDF: {e}")
        return None

def display_tablet_names(tablet_names_text):
    """Display tablet names in a formatted grid."""
    if not tablet_names_text:
        return
    
    tablet_names = []
    
    for delimiter in ['\n', ',', ';', '•', '-']:
        if delimiter in tablet_names_text:
            names = tablet_names_text.split(delimiter)
            tablet_names = [name.strip() for name in names if name.strip()]
            break
    
    if not tablet_names:
        tablet_names = [tablet_names_text.strip()]
    
    # Display tablet names in a grid
    st.markdown('<div class="tablet-grid">', unsafe_allow_html=True)
    
    cols = st.columns(min(3, len(tablet_names)))
    for i, name in enumerate(tablet_names):
        if name:
            with cols[i % len(cols)]:
                st.markdown(f'<div class="tablet-name">🏷️ {name}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_safety_info(content, safety_type):
    """Display safety information with appropriate styling."""
    if not content:
        return
    
    if "safe" in content.lower() or "no interaction" in content.lower():
        st.markdown(f'<div class="safety-safe">✅ {content}</div>', unsafe_allow_html=True)
    elif "avoid" in content.lower() or "contraindicated" in content.lower() or "not recommended" in content.lower():
        st.markdown(f'<div class="safety-danger">❌ {content}</div>', unsafe_allow_html=True)
    elif "caution" in content.lower() or "monitor" in content.lower() or "consult" in content.lower():
        st.markdown(f'<div class="safety-warning">⚠️ {content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="safety-info">ℹ️ {content}</div>', unsafe_allow_html=True)

def main():
    # Initialize session state
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

    # Main Title
    st.markdown("""
    <div class="main-title">
        <h1>🏥 MediScan</h1>
        <p>Comprehensive Drug Composition Analyzer</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Medical Disclaimer
    st.markdown("""
    <div class="warning-banner">
        <h3>⚠️ MEDICAL DISCLAIMER</h3>
        <p>The information provided by MediScan is for educational and informational purposes only and is not intended to replace professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition, medication, or drug interactions.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">📤 Upload Tablet Image</div>', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Upload a clear image of the tablet",
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload a clear, high-quality image of the tablet or its packaging"
        )
        
        if uploaded_file:
            resized_image = resize_image_for_display(uploaded_file)
            if resized_image:
                st.image(resized_image, caption="Uploaded Tablet Image", width=MAX_IMAGE_WIDTH)
                
                file_size = len(uploaded_file.getvalue()) / 1024
                st.info(f"**{uploaded_file.name}** • {file_size:.1f} KB")
        
        st.markdown('<div class="section-header">💊 Additional Medications (Optional)</div>', unsafe_allow_html=True)
        additional_meds = st.text_area(
            "Enter any other medications you are currently taking:",
            placeholder="e.g., Aspirin 75mg daily, Metformin 500mg twice daily, Lisinopril 10mg once daily",
            help="Include medication names, dosages, and frequency. This helps check for potential drug interactions.",
            key="additional_medications_input"
        )
        
        # Analyze button
        if uploaded_file and st.button("🔬 Analyze Tablet & Check Safety"):
            st.session_state.analyze_clicked = True
            st.session_state.additional_medications = additional_meds
            
            # Save uploaded file and analyze
            temp_path = save_uploaded_file(uploaded_file)
            if temp_path:
                try:
                    extracted_info = extract_composition_and_details(temp_path)
                    
                    if extracted_info:
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
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">📊 Analysis Results</div>', unsafe_allow_html=True)
        
        # Display results if available
        if st.session_state.analysis_results:
            st.markdown("### 🔬 Comprehensive Drug Analysis")
            
            # Parse and display results
            analysis_text = st.session_state.analysis_results
            
            # Enhanced sections list
            sections = [
                ("Composition", "🧬"),
                ("Available Tablet Names", "🏷️"),
                ("Uses", "💊"),
                ("How to Use", "📋"),
                ("Side Effects", "⚠️"),
                ("Cost", "💰"),
                ("Safety with Alcohol", "🍺"),
                ("Pregnancy Safety", "🤱"),
                ("Breastfeeding Safety", "🍼"),
                ("Driving Safety", "🚗"),
                ("General Safety Advice", "🛡️")
            ]
            
            for section_name, icon in sections:
                # Pattern to match sections
                pattern = rf"\*{re.escape(section_name)}:\*(.*?)(?=\*(?:{'|'.join(re.escape(s[0]) for s in sections)}):\*|$)"
                match = re.search(pattern, analysis_text, re.DOTALL | re.IGNORECASE)
                
                if match:
                    content = match.group(1).strip()
                    
                    # Create result card
                    st.markdown('<div class="result-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="result-header">{icon} {section_name}</div>', unsafe_allow_html=True)
                    st.markdown('<div class="result-content">', unsafe_allow_html=True)
                    
                    # Special handling for different sections
                    if section_name == "Available Tablet Names":
                        display_tablet_names(content)
                    elif section_name in ["Safety with Alcohol", "Pregnancy Safety", "Breastfeeding Safety", "Driving Safety"]:
                        display_safety_info(content, section_name)
                    else:
                        st.write(content)
                    
                    st.markdown('</div></div>', unsafe_allow_html=True)
            
            # Display drug interaction analysis if available
            if st.session_state.interaction_analysis:
                st.markdown("### 💊 Drug Interaction Analysis")
                st.markdown(f"**Additional Medications:** {st.session_state.additional_medications}")
                
                # Parse interaction analysis for severity levels
                interaction_text = st.session_state.interaction_analysis
                
                if "severe" in interaction_text.lower() or "major" in interaction_text.lower():
                    st.markdown('<div class="interaction-severe"><h4>🚨 SEVERE/MAJOR INTERACTION DETECTED</h4></div>', unsafe_allow_html=True)
                elif "moderate" in interaction_text.lower():
                    st.markdown('<div class="interaction-moderate"><h4>⚠️ MODERATE INTERACTION</h4></div>', unsafe_allow_html=True)
                elif "minor" in interaction_text.lower():
                    st.markdown('<div class="interaction-minor"><h4>ℹ️ MINOR INTERACTION</h4></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="interaction-low"><h4>✅ LOW INTERACTION RISK</h4></div>', unsafe_allow_html=True)
                
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown('<div class="result-content">', unsafe_allow_html=True)
                st.write(interaction_text)
                st.markdown('</div></div>', unsafe_allow_html=True)
            
            # PDF download section
            if st.session_state.original_image:
                st.markdown('<div class="download-section">', unsafe_allow_html=True)
                st.markdown("### 📄 Download Comprehensive Report")
                
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
            st.markdown("""
            <div class="result-card">
                <div class="result-header">📋 Instructions</div>
                <div class="result-content">
                    <p>Upload a tablet image and click 'Analyze Tablet & Check Safety' to see comprehensive results here.</p>
                    <ul>
                        <li>🔍 <strong>Clear Image:</strong> Ensure the tablet is clearly visible</li>
                        <li>💡 <strong>Good Lighting:</strong> Use proper lighting for better analysis</li>
                        <li>📱 <strong>Stable Shot:</strong> Avoid blurry or shaky images</li>
                        <li>🔬 <strong>Text Visible:</strong> Make sure any text on the tablet is readable</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Additional Safety Information Section
    if st.session_state.analysis_results:
        st.markdown('<div class="safety-reminders">', unsafe_allow_html=True)
        st.markdown('<h3>🛡️ Important Safety Reminders</h3>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="safety-item">
                <h4>🍺 Alcohol Interaction</h4>
                <ul>
                    <li>Always check the specific alcohol interaction information above</li>
                    <li>Some medications can cause severe reactions with alcohol</li>
                    <li>Consult your doctor about alcohol consumption while on medication</li>
                </ul>
            </div>
            
            <div class="safety-item">
                <h4>🤱 Pregnancy & Breastfeeding</h4>
                <ul>
                    <li>Medication safety varies by trimester</li>
                    <li>Many drugs can pass through breast milk</li>
                    <li>Always inform your healthcare provider if you're pregnant or breastfeeding</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="safety-item">
                <h4>🚗 Driving Safety</h4>
                <ul>
                    <li>Some medications can cause drowsiness or dizziness</li>
                    <li>Check the driving safety information above</li>
                    <li>Avoid driving if you feel impaired</li>
                </ul>
            </div>
            
            <div class="safety-item">
                <h4>💊 Drug Interactions</h4>
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
        <p>Powered by Gemini AI + Tavily | Built with ❤️ for Better Healthcare</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
