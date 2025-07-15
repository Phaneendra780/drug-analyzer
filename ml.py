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
    page_icon="💊"
)

# Custom CSS for white theme and relaxing UI
st.markdown("""
<style>
    /* Main app styling */
    .main > div {
        padding: 2rem 3rem;
        background: #ffffff;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 15px;
        margin-bottom: 2rem;
        border: 2px solid #e3f2fd;
    }
    
    .main-title {
        color: #2c3e50;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .main-subtitle {
        color: #5a6c7d;
        font-size: 1.2rem;
        font-weight: 400;
        margin-bottom: 1rem;
    }
    
    /* Card styling */
    .card {
        background: #ffffff;
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #e8f4f8;
    }
    
    .upload-card {
        background: #f8fffe;
        border: 2px dashed #4a90e2;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .upload-card:hover {
        background: #f0f8ff;
        border-color: #2980b9;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #4a90e2 0%, #2980b9 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(74, 144, 226, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(74, 144, 226, 0.4);
    }
    
    /* Section headers */
    .section-header {
        color: #2c3e50;
        font-size: 1.5rem;
        font-weight: 600;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e3f2fd;
    }
    
    /* Analysis results styling */
    .analysis-section {
        background: #ffffff;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #4a90e2;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .analysis-title {
        color: #2c3e50;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .analysis-content {
        color: #34495e;
        font-size: 1rem;
        line-height: 1.6;
    }
    
    /* Alert styling */
    .stAlert {
        border-radius: 8px;
        border: none;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .stAlert > div {
        color: #2c3e50;
        font-weight: 500;
    }
    
    /* Text input styling */
    .stTextArea textarea {
        border: 2px solid #e3f2fd;
        border-radius: 8px;
        padding: 1rem;
        font-size: 1rem;
        color: #2c3e50;
        background: #ffffff;
    }
    
    .stTextArea textarea:focus {
        border-color: #4a90e2;
        box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
    }
    
    /* File uploader styling */
    .stFileUploader {
        border: 2px dashed #4a90e2;
        border-radius: 8px;
        padding: 2rem;
        background: #f8fffe;
    }
    
    /* Divider styling */
    .stDivider {
        margin: 2rem 0;
        border-color: #e3f2fd;
    }
    
    /* Info box styling */
    .info-box {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        color: #495057;
    }
    
    /* Success/Error message styling */
    .stSuccess {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    
    .stError {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    
    .stWarning {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: #ffffff;
    }
    
    /* Remove default padding */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Spinner styling */
    .stSpinner {
        color: #4a90e2;
    }
    
    /* Download button styling */
    .download-section {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 10px;
        padding: 1.5rem;
        margin: 2rem 0;
        text-align: center;
        border: 1px solid #e3f2fd;
    }
    
    /* Safety guidelines styling */
    .safety-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .safety-item {
        background: #ffffff;
        border-radius: 8px;
        padding: 1.5rem;
        border: 1px solid #e3f2fd;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .safety-item h4 {
        color: #2c3e50;
        margin-bottom: 1rem;
        font-size: 1.1rem;
    }
    
    .safety-item ul {
        color: #34495e;
        line-height: 1.6;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main > div {
            padding: 1rem;
        }
        
        .main-title {
            font-size: 2rem;
        }
        
        .card {
            padding: 1rem;
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

MAX_IMAGE_WIDTH = 400

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
    """Create a formal PDF report of the analysis."""
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
        
        # Formal styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'FormalTitle',
            parent=styles['Title'],
            fontSize=20,
            alignment=1,
            spaceAfter=20,
            textColor=colors.HexColor('#2c3e50'),
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'FormalSubtitle',
            parent=styles['Heading1'],
            fontSize=14,
            alignment=1,
            spaceAfter=15,
            textColor=colors.HexColor('#34495e'),
            fontName='Helvetica'
        )
        
        heading_style = ParagraphStyle(
            'FormalHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=10,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'FormalBody',
            parent=styles['Normal'],
            fontSize=11,
            leading=16,
            textColor=colors.HexColor('#2c3e50'),
            fontName='Helvetica'
        )
        
        disclaimer_style = ParagraphStyle(
            'FormalDisclaimer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#721c24'),
            borderWidth=2,
            borderColor=colors.HexColor('#dc3545'),
            borderPadding=12,
            backColor=colors.HexColor('#f8d7da'),
            alignment=0,
            fontName='Helvetica-Bold'
        )
        
        # Report Header
        content.append(Paragraph("PHARMACEUTICAL ANALYSIS REPORT", title_style))
        content.append(Paragraph("Drug Composition & Safety Assessment", subtitle_style))
        content.append(Spacer(1, 0.3*inch))
        
        # Medical Disclaimer
        content.append(Paragraph(
            "<b>MEDICAL DISCLAIMER:</b> This analysis is provided for informational purposes only and should not replace professional medical advice. "
            "Always consult with a qualified healthcare professional before making any medical decisions or changes to your medication regimen. "
            "The information contained in this report is based on AI analysis and publicly available medical data.",
            disclaimer_style
        ))
        content.append(Spacer(1, 0.3*inch))
        
        # Report Information
        current_datetime = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        content.append(Paragraph(f"<b>Report Generated:</b> {current_datetime}", normal_style))
        content.append(Paragraph(f"<b>Analysis System:</b> MediScan AI-Powered Drug Analyzer", normal_style))
        content.append(Spacer(1, 0.3*inch))
        
        # Add analyzed image
        if image_data:
            try:
                img_temp = BytesIO(image_data)
                img = Image.open(img_temp)
                img_width, img_height = img.size
                aspect = img_height / float(img_width)
                display_width = 3.5 * inch
                display_height = display_width * aspect
                
                if display_height > 4 * inch:
                    display_height = 4 * inch
                    display_width = display_height / aspect
                
                img_temp.seek(0)
                img_obj = ReportLabImage(img_temp, width=display_width, height=display_height)
                content.append(Paragraph("ANALYZED SPECIMEN", heading_style))
                content.append(img_obj)
                content.append(Spacer(1, 0.2*inch))
            except Exception as img_error:
                st.warning(f"Could not add image to PDF: {img_error}")
        
        # Analysis Results
        content.append(Paragraph("PHARMACEUTICAL ANALYSIS RESULTS", heading_style))
        
        # Format the analysis results for PDF
        if analysis_results:
            section_pattern = r"\*([\w\s]+):\*(.*?)(?=\*[\w\s]+:\*|$)"
            matches = re.findall(section_pattern, analysis_results, re.DOTALL | re.IGNORECASE)
            
            if matches:
                for section_title, section_content in matches:
                    section_heading = ParagraphStyle(
                        f'Section_{section_title}',
                        parent=normal_style,
                        fontSize=12,
                        fontName='Helvetica-Bold',
                        textColor=colors.HexColor('#2c3e50'),
                        spaceAfter=8,
                        spaceBefore=12
                    )
                    
                    content.append(Paragraph(f"{section_title.strip()}:", section_heading))
                    
                    paragraphs = section_content.strip().split("\n")
                    for para in paragraphs:
                        if para.strip():
                            clean_para = para.strip().replace('<', '&lt;').replace('>', '&gt;')
                            # Add bullet points for lists
                            if any(keyword in section_title.lower() for keyword in ['names', 'uses', 'effects']):
                                if not clean_para.startswith('•'):
                                    clean_para = f"• {clean_para}"
                            content.append(Paragraph(clean_para, normal_style))
                    
                    content.append(Spacer(1, 0.1*inch))
        
        # Drug Interaction Analysis
        if interaction_analysis and additional_meds:
            content.append(Spacer(1, 0.2*inch))
            content.append(Paragraph("DRUG INTERACTION ANALYSIS", heading_style))
            content.append(Paragraph(f"<b>Additional Medications Considered:</b> {additional_meds}", normal_style))
            content.append(Spacer(1, 0.1*inch))
            
            # Determine interaction severity and format accordingly
            interaction_style = normal_style
            if "severe" in interaction_analysis.lower() or "major" in interaction_analysis.lower():
                interaction_style = ParagraphStyle(
                    'SevereInteraction',
                    parent=normal_style,
                    textColor=colors.HexColor('#721c24'),
                    backColor=colors.HexColor('#f8d7da'),
                    borderWidth=1,
                    borderColor=colors.HexColor('#dc3545'),
                    borderPadding=8
                )
            elif "moderate" in interaction_analysis.lower():
                interaction_style = ParagraphStyle(
                    'ModerateInteraction',
                    parent=normal_style,
                    textColor=colors.HexColor('#856404'),
                    backColor=colors.HexColor('#fff3cd'),
                    borderWidth=1,
                    borderColor=colors.HexColor('#ffc107'),
                    borderPadding=8
                )
            
            clean_interaction = interaction_analysis.replace('<', '&lt;').replace('>', '&gt;')
            content.append(Paragraph(clean_interaction, interaction_style))
            content.append(Spacer(1, 0.2*inch))
        
        # Professional closing
        content.append(Spacer(1, 0.4*inch))
        content.append(Paragraph("IMPORTANT REMINDERS", heading_style))
        content.append(Paragraph("• Always follow your healthcare provider's instructions", normal_style))
        content.append(Paragraph("• Report any unusual symptoms or side effects immediately", normal_style))
        content.append(Paragraph("• Keep all medications in their original containers", normal_style))
        content.append(Paragraph("• Store medications as directed on the label", normal_style))
        content.append(Paragraph("• Never share prescription medications with others", normal_style))
        
        # Build PDF
        pdf.build(content)
        
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"📄 Error creating PDF: {e}")
        return None

def display_analysis_results(analysis_text):
    """Display analysis results in a clean, structured format."""
    if not analysis_text:
        return
    
    sections = [
        ("Composition", "🧬", "#e8f5e8"),
        ("Available Tablet Names", "💊", "#f0f8ff"),
        ("Uses", "🎯", "#fff8e1"),
        ("How to Use", "📋", "#f3e5f5"),
        ("Side Effects", "⚠️", "#ffebee"),
        ("Cost", "💰", "#e0f2f1"),
        ("Safety with Alcohol", "🍺", "#fff3e0"),
        ("Pregnancy Safety", "🤱", "#fce4ec"),
        ("Breastfeeding Safety", "🍼", "#e8f5e8"),
        ("Driving Safety", "🚗", "#e3f2fd"),
        ("General Safety Advice", "🛡️", "#f1f8e9")
    ]
    
    for section_name, icon, bg_color in sections:
        pattern = rf"\*{re.escape(section_name)}:\*(.*?)(?=\*(?:{'|'.join(re.escape(s[0]) for s in sections)}):\*|$)"
        match = re.search(pattern, analysis_text, re.DOTALL | re.IGNORECASE)
        
        if match:
            content = match.group(1).strip()
            
            # Create styled container
            st.markdown(f"""
            <div class="analysis-section" style="background-color: {bg_color}; border-left-color: #4a90e2;">
                <div class="analysis-title">{icon} {section_name}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if section_name == "Available Tablet Names":
                # Display tablet names as formatted list
                tablet_names = []
                for delimiter in ['\n', ',', ';', '•', '-']:
                    if delimiter in content:
                        names = content.split(delimiter)
                        tablet_names = [name.strip() for name in names if name.strip()]
                        break
                
                if not tablet_names:
                    tablet_names = [content.strip()]
                
                for name in tablet_names:
                    if name:
                        st.markdown(f"• **{name}**")
            
            elif section_name == "Uses":
                # Format uses as structured list
                if '\n' in content or ',' in content:
                    uses_list = content.replace('\n', ', ').split(',')
                    for use in uses_list:
                        if use.strip():
                            st.markdown(f"• {use.strip()}")
                else:
                    st.markdown(content)
            
            elif section_name == "Side Effects":
                # Format side effects with appropriate styling
                if '\n' in content or ',' in content:
                    effects_list = content.replace('\n', ', ').split(',')
                    for effect in effects_list:
                        if effect.strip():
                            st.markdown(f"⚠️ {effect.strip()}")
                else:
                    st.markdown(f"⚠️ {content}")
            
            elif "Safety" in section_name:
                # Display safety information with appropriate indicators
                if "safe" in content.lower() or "no interaction" in content.lower():
                    st.success(f"✅ {content}")
                elif "avoid" in content.lower() or "contraindicated" in content.lower() or "not recommended" in content.lower():
                    st.error(f"❌ {content}")
                elif "caution" in content.lower() or "monitor" in content.lower() or "consult" in content.lower():
                    st.warning(f"⚠️ {content}")
                else:
                    st.info(f"ℹ️ {content}")
            
            else:
                st.markdown(f"<div class='analysis-content'>{content}</div>", unsafe_allow_html=True)
            
            st.markdown("---")

def display_interaction_analysis(interaction_text):
    """Display interaction analysis with appropriate styling."""
    if not interaction_text:
        return
    
    st.markdown("""
    <div class="analysis-section" style="background-color: #fff3cd; border-left-color: #ffc107;">
        <div class="analysis-title">🔍 Drug Interaction Analysis</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Determine interaction severity
    if "severe" in interaction_text.lower() or "major" in interaction_text.lower():
        st.error("🚨 **SEVERE/MAJOR INTERACTION DETECTED**")
    elif "moderate" in interaction_text.lower():
        st.warning("⚠️ **MODERATE INTERACTION**")
    elif "minor" in interaction_text.lower():
        st.info("ℹ️ **MINOR INTERACTION**")
    else:
        st.success("✅ **LOW INTERACTION RISK**")
    
    st.markdown(f"<div class='analysis-content'>{interaction_text}</div>", unsafe_allow_html=True)

def main():
    # Initialize session state
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
        <div class="main-title">💊 MediScan</div>
        <div class="main-subtitle">Advanced Drug Composition Analysis & Safety Assessment</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Medical disclaimer
    st.error("""
    ⚠️ **MEDICAL DISCLAIMER:** The information provided by MediScan is for educational and informational purposes only and is not intended to replace professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition, medication, or drug interactions.
    """)
    
    # Single column layout
    st.markdown('<div class="section-header">📤 Upload Tablet Image</div>', unsafe_allow_html=True)
    
    # Upload section
    uploaded_file = st.file_uploader(
        "Choose a clear image of your tablet or medication",
        type=["jpg", "jpeg", "png", "webp"],
        help="Please upload a clear, well-lit image of the tablet or its packaging for accurate analysis"
    )
    
    if uploaded_file:
        # Display uploaded image in a card
        st.markdown('<div class="card">', unsafe_allow_html=True)
        resized_image = resize_image_for_display(uploaded_file)
        if resized_image:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(resized_image, caption="Uploaded Tablet Image", use_column_width=True)
                
            # Display file info
            file_size = len(uploaded_file.getvalue()) / 1024
            st.success(f"📎 **{uploaded_file.name}** • {file_size:.1f} KB uploaded successfully")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Drug interaction checker section
    st.markdown('<div class="section-header">💊 Drug Interaction Checker</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    additional_meds = st.text_area(
        "Enter any other medications you are currently taking (optional):",
        placeholder="Example: Aspirin 75mg daily, Metformin 500mg twice daily, Lisinopril 10mg once daily",
        help="Include medication names, dosages, and frequency. This helps identify potential drug interactions.",
        height=100
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Analysis button
    if uploaded_file:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        if st.button("🔬 Analyze Tablet & Generate Safety Report", use_container_width=True):
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
                        st.rerun()
                    else:
                        st.error("❌ Analysis failed. Please try with a clearer image.")
                
                except Exception as e:
                    st.error(f"🚨 Analysis failed: {e}")
                finally:
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Results section
    st.markdown('<div class="section-header">📊 Analysis Results</div>', unsafe_allow_html=True)
    
    # Display results if available
    if st.session_state.analysis_results:
        display_analysis_results(st.session_state.analysis_results)
        
        # Display drug interaction analysis if available
        if st.session_state.interaction_analysis:
            st.markdown(f"**Additional Medications Analyzed:** {st.session_state.additional_medications}")
            st.markdown("---")
            display_interaction_analysis(st.session_state.interaction_analysis)
        
        # PDF download section
        if st.session_state.original_image:
            st.markdown('<div class="section-header">📄 Download Professional Report</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="download-section">', unsafe_allow_html=True)
            
            pdf_bytes = create_pdf(
                st.session_state.original_image,
                st.session_state.analysis_results,
                st.session_state.interaction_analysis,
                st.session_state.additional_medications
            )
            
            if pdf_bytes:
                download_filename = f"mediscan_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                st.download_button(
                    label="📥 Download Professional PDF Report",
                    data=pdf_bytes,
                    file_name=download_filename,
                    mime="application/pdf",
                    help="Download a comprehensive, professional PDF report with all analysis results and safety information",
                    use_container_width=True
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="info-box">
            <h3>📋 Ready for Analysis</h3>
            <p>Upload a clear image of your tablet and click 'Analyze Tablet & Generate Safety Report' to receive:</p>
            <ul>
                <li>🧬 <strong>Drug composition identification</strong></li>
                <li>💊 <strong>Available tablet names and brands</strong></li>
                <li>🎯 <strong>Medical uses and indications</strong></li>
                <li>📋 <strong>Proper usage instructions</strong></li>
                <li>⚠️ <strong>Side effects and precautions</strong></li>
                <li>💰 <strong>Cost information</strong></li>
                <li>🛡️ <strong>Comprehensive safety analysis</strong></li>
                <li>🔍 <strong>Drug interaction assessment</strong></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Safety Guidelines Section
    if st.session_state.analysis_results:
        st.markdown('<div class="section-header">🛡️ Important Safety Guidelines</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="safety-grid">
            <div class="safety-item">
                <h4>🍺 Alcohol Interactions</h4>
                <ul>
                    <li>Review specific alcohol interaction information in your analysis</li>
                    <li>Some medications can cause severe reactions with alcohol</li>
                    <li>Always consult your healthcare provider about alcohol consumption</li>
                    <li>Never assume it's safe to drink while taking medication</li>
                </ul>
            </div>
            
            <div class="safety-item">
                <h4>🤱 Pregnancy & Breastfeeding</h4>
                <ul>
                    <li>Medication safety varies by pregnancy trimester</li>
                    <li>Many drugs can pass through breast milk</li>
                    <li>Always inform healthcare providers about pregnancy/breastfeeding</li>
                    <li>Never stop medications without consulting your doctor</li>
                </ul>
            </div>
            
            <div class="safety-item">
                <h4>🚗 Driving Safety</h4>
                <ul>
                    <li>Some medications cause drowsiness or dizziness</li>
                    <li>Review driving safety information in your analysis</li>
                    <li>Avoid driving if you feel impaired</li>
                    <li>Wait until you know how medication affects you</li>
                </ul>
            </div>
            
            <div class="safety-item">
                <h4>💊 Drug Interactions</h4>
                <ul>
                    <li>Provide complete medication list to healthcare providers</li>
                    <li>Include over-the-counter drugs and supplements</li>
                    <li>Check for interactions before starting new medications</li>
                    <li>Use the same pharmacy for all prescriptions when possible</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6c757d; font-size: 0.9rem; margin-top: 2rem;">
        <p><strong>MediScan</strong> - Advanced AI-Powered Drug Analysis System</p>
        <p>Always consult qualified healthcare professionals for medical advice</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
