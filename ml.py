import streamlit as st
import os
import pandas as pd
from PIL import Image
from io import BytesIO
# Using the phi-agent library components
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

# Custom CSS for white theme and enhanced UI
st.markdown("""
<style>
    /* Main theme colors */
    .stApp {
        background-color: #ffffff;
        color: #000000;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 30px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 10px 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    /* Card styling */
    .info-card {
        background: #ffffff;
        border: 2px solid #e8e8e8;
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    .info-card:hover {
        border-color: #667eea;
        box-shadow: 0 4px 20px rgba(102,126,234,0.1);
    }
    
    .section-header {
        color: #2c3e50;
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 3px solid #667eea;
    }
    
    /* Upload section */
    .upload-section {
        background: #f8f9ff;
        border: 2px dashed #667eea;
        border-radius: 12px;
        padding: 30px;
        text-align: center;
        margin: 20px 0;
    }
    
    /* Result cards */
    .result-card {
        background: #ffffff;
        border-left: 4px solid #667eea;
        border-radius: 8px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .result-header {
        color: #2c3e50;
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .result-content {
        color: #34495e;
        line-height: 1.6;
        font-size: 1rem;
    }
    
    /* Safety indicators */
    .safety-safe {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 6px;
        padding: 12px;
        margin: 8px 0;
        color: #155724;
    }
    
    .safety-warning {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 6px;
        padding: 12px;
        margin: 8px 0;
        color: #856404;
    }
    
    .safety-danger {
        background: #f8d7da;
        border: 1px solid #f1c2c7;
        border-radius: 6px;
        padding: 12px;
        margin: 8px 0;
        color: #721c24;
    }
    
    /* Tablet names styling */
    .tablet-name {
        background: #e8f4f8;
        border: 1px solid #b8daff;
        border-radius: 20px;
        padding: 8px 16px;
        margin: 5px;
        display: inline-block;
        color: #004085;
        font-weight: 500;
    }
    
    /* Interaction analysis */
    .interaction-severe {
        background: #ffebee;
        border: 2px solid #f44336;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #c62828;
    }
    
    .interaction-moderate {
        background: #fff8e1;
        border: 2px solid #ff9800;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #ef6c00;
    }
    
    .interaction-minor {
        background: #f3e5f5;
        border: 2px solid #9c27b0;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #7b1fa2;
    }
    
    .interaction-low {
        background: #e8f5e8;
        border: 2px solid #4caf50;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        color: #2e7d32;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 15px 30px;
        font-size: 1.1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102,126,234,0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102,126,234,0.4);
    }
    
    /* Disclaimer box */
    .disclaimer {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
        border-left: 5px solid #ffc107;
    }
    
    .disclaimer strong {
        color: #856404;
        font-size: 1.1rem;
    }
    
    /* Progress and loading */
    .stProgress > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Text input styling */
    .stTextArea textarea {
        border: 2px solid #e8e8e8;
        border-radius: 8px;
        padding: 12px;
        font-size: 1rem;
        transition: border-color 0.3s ease;
    }
    
    .stTextArea textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
    }
    
    /* File uploader */
    .stFileUploader {
        border: 2px dashed #667eea;
        border-radius: 12px;
        padding: 20px;
        background: #f8f9ff;
    }
    
    /* Metrics styling */
    .metric-card {
        background: white;
        border: 1px solid #e8e8e8;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #667eea;
        margin-bottom: 5px;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        
        .main-header p {
            font-size: 1rem;
        }
        
        .info-card {
            padding: 15px;
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

# START OF CRITICAL CHANGE: REVISED INSTRUCTIONS FOR STRUCTURE AND CONTENT
INSTRUCTIONS = """
- Extract the drug composition from the tablet image.
- Use this composition to fetch and return detailed, medically accurate information from trusted sources.
- **CRITICAL FORMATTING:** Return ALL information in a strict key-value format using asterisks. Do NOT use bullet points, numbered lists, or fragmented text outside of the section content.
- **CRITICAL CONTENT:** Provide only medical/scientific uses and avoid manufacturer promotional language.

- Return all information in this exact structured format:
  *Composition:* <composition>
  *Uses:* <accurate medical/scientific uses based on online sources>
  *Available Tablet Names:* <list of brand names and generic names that contain this composition>
  *How to Use:* <detailed dosage instructions, timing, with or without food>
  *Side Effects:* <verified side effects>
  *Cost:* <actual cost from trusted sources>
  *Safety with Alcohol:* <specific advice about alcohol consumption>
  *Pregnancy Safety:* <pregnancy category and safety advice>
  *Breastfeeding Safety:* <safety for nursing mothers>
  *Driving Safety:* <effects on driving ability>
  *General Safety Advice:* <additional precautions and contraindications>
"""
# END OF CRITICAL CHANGE

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
        # FIX APPLIED: Changed to the stable, higher-limit model
        return Agent(
            model=Gemini(id="gemini-2.5-flash", api_key=GOOGLE_API_KEY),
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
        # FIX APPLIED: Changed to the stable, higher-limit model
        return Agent(
            model=Gemini(id="gemini-2.5-flash", api_key=GOOGLE_API_KEY),
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
        content.append(Paragraph("💊 MediScan - Comprehensive Drug Analysis Report", title_style))
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
    
    # Display tablet names with custom styling
    tablet_html = ""
    for name in tablet_names:
        if name:
            tablet_html += f'<span class="tablet-name">💊 {name}</span>'
    
    if tablet_html:
        st.markdown(tablet_html, unsafe_allow_html=True)

def display_safety_info(content, safety_type):
    """Display safety information with appropriate styling."""
    if not content:
        return
    
    # Determine safety level and apply appropriate styling
    if "safe" in content.lower() or "no interaction" in content.lower():
        st.markdown(f'<div class="safety-safe">✅ <strong>{safety_type}:</strong> {content}</div>', unsafe_allow_html=True)
    elif "avoid" in content.lower() or "contraindicated" in content.lower() or "not recommended" in content.lower():
        st.markdown(f'<div class="safety-danger">❌ <strong>{safety_type}:</strong> {content}</div>', unsafe_allow_html=True)
    elif "caution" in content.lower() or "monitor" in content.lower() or "consult" in content.lower():
        st.markdown(f'<div class="safety-warning">⚠️ <strong>{safety_type}:</strong> {content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="safety-safe">ℹ️ <strong>{safety_type}:</strong> {content}</div>', unsafe_allow_html=True)

def display_interaction_analysis(interaction_text):
    """Display interaction analysis with appropriate styling."""
    if not interaction_text:
        return
    
    # Determine interaction severity
    if "severe" in interaction_text.lower() or "major" in interaction_text.lower():
        st.markdown(f'<div class="interaction-severe">🚨 <strong>SEVERE/MAJOR INTERACTION DETECTED</strong></div>', unsafe_allow_html=True)
    elif "moderate" in interaction_text.lower():
        st.markdown(f'<div class="interaction-moderate">⚠️ <strong>MODERATE INTERACTION</strong></div>', unsafe_allow_html=True)
    elif "minor" in interaction_text.lower():
        st.markdown(f'<div class="interaction-minor">ℹ️ <strong>MINOR INTERACTION</strong></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="interaction-low">✅ <strong>LOW INTERACTION RISK</strong></div>', unsafe_allow_html=True)

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
        <h1>💊 MediScan</h1>
        <p>Comprehensive Drug Composition Analyzer & Safety Checker</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Medical disclaimer
    st.markdown("""
    <div class="disclaimer">
        <strong>⚠️ MEDICAL DISCLAIMER</strong><br>
        The information provided by MediScan is for educational and informational purposes only and is not intended to replace professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition, medication, or drug interactions.
    </div>
    """, unsafe_allow_html=True)
    
    # Main content in two columns
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">📤 Upload Tablet Image</div>', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Upload a clear image of the tablet",
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload a clear, high-quality image of the tablet or its packaging"
        )
        
        if uploaded_file:
            # Display uploaded image
            resized_image = resize_image_for_display(uploaded_file)
            if resized_image:
                st.image(resized_image, caption="Uploaded Tablet Image", width=MAX_IMAGE_WIDTH)
                
                # Display file info
                file_size = len(uploaded_file.getvalue()) / 1024  # Convert to KB
                st.success(f"📎 **{uploaded_file.name}** • {file_size:.1f} KB")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Additional medications input
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">💊 Drug Interaction Checker</div>', unsafe_allow_html=True)
        additional_meds = st.text_area(
            "Enter any other medications you are currently taking:",
            placeholder="e.g., Aspirin 75mg daily, Metformin 500mg twice daily, Lisinopril 10mg once daily",
            help="Include medication names, dosages, and frequency. This helps check for potential drug interactions.",
            key="additional_medications_input",
            height=100
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Analyze button
        if uploaded_file:
            if st.button("🔬 Analyze Tablet & Check Safety", use_container_width=True):
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
                            st.rerun()
                        else:
                            st.error("❌ Analysis failed. Please try with a clearer image.")
                        
                    except Exception as e:
                        st.error(f"🚨 Analysis failed: {e}")
                    finally:
                        # Clean up temp file
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
    
    with col2:
        st.markdown('<div class="section-header">📊 Analysis Results</div>', unsafe_allow_html=True)
        
        # Display results if available
        if st.session_state.analysis_results:
            # Parse and display results
            analysis_text = st.session_state.analysis_results
            
            # Enhanced sections list with proper organization
            sections = [
                ("Composition", "🧬", "composition"),
                ("Uses", "🎯", "uses"), 
                ("Available Tablet Names", "💊", "tablet_names"),
                ("How to Use", "📋", "usage"),
                ("Side Effects", "⚠️", "side_effects"),
                ("Cost", "💰", "cost"),
                ("Safety with Alcohol", "🍺", "safety"),
                ("Pregnancy Safety", "🤱", "safety"),
                ("Breastfeeding Safety", "🍼", "safety"),
                ("Driving Safety", "🚗", "safety"),
                ("General Safety Advice", "🛡️", "safety")
            ]
            
            for section_name, icon, section_type in sections:
                # Pattern to match sections
                pattern = rf"\*{re.escape(section_name)}:\*(.*?)(?=\*(?:{'|'.join(re.escape(s[0]) for s in sections)}):\*|$)"
                match = re.search(pattern, analysis_text, re.DOTALL | re.IGNORECASE)
                
                if match:
                    content = match.group(1).strip()
                    
                    # Create result card for each section
                    st.markdown(f'<div class="result-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="result-header">{icon} {section_name}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="result-content">', unsafe_allow_html=True)
                    
                    # Special handling for different section types
                    if section_type == "tablet_names":
                        display_tablet_names(content)
                    elif section_type == "safety":
                        display_safety_info(content, section_name)
                    elif section_type == "composition":
                        st.markdown(f"**{content}**")
                    elif section_type == "uses":
                        # Format uses as bullet points if multiple
                        if '\n' in content or ',' in content or '•' in content: # Added '•' check for robustness
                            uses_list = content.replace('\n', ', ').split(',')
                            for use in uses_list:
                                if use.strip():
                                    st.markdown(f"• {use.strip()}")
                        else:
                            st.markdown(content)
                    elif section_type == "side_effects":
                        # Format side effects with warning styling
                        if '\n' in content or ',' in content or '•' in content: # Added '•' check for robustness
                            effects_list = content.replace('\n', ', ').split(',')
                            for effect in effects_list:
                                if effect.strip():
                                    st.markdown(f"⚠️ {effect.strip()}")
                        else:
                            st.markdown(f"⚠️ {content}")
                    elif section_type == "cost":
                        # Highlight cost information
                        st.markdown(f"💰 **{content}**")
                    else:
                        st.markdown(content)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Display drug interaction analysis if available
            if st.session_state.interaction_analysis:
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown('<div class="result-header">🔍 Drug Interaction Analysis</div>', unsafe_allow_html=True)
                st.markdown('<div class="result-content">', unsafe_allow_html=True)
                
                st.markdown(f"**Additional Medications:** {st.session_state.additional_medications}")
                st.markdown("---")
                
                # Display interaction severity indicator
                display_interaction_analysis(st.session_state.interaction_analysis)
                
                # Display detailed interaction analysis
                st.markdown(st.session_state.interaction_analysis)
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # PDF download section
            if st.session_state.original_image:
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                st.markdown('<div class="result-header">📄 Download Report</div>', unsafe_allow_html=True)
                st.markdown('<div class="result-content">', unsafe_allow_html=True)
                
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
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="result-card">
                <div class="result-header">📋 Ready for Analysis</div>
                <div class="result-content">
                    Upload a tablet image and click 'Analyze Tablet & Check Safety' to see comprehensive results here.
                    <br><br>
                    <strong>What you'll get:</strong>
                    <ul>
                        <li>🧬 Drug composition identification</li>
                        <li>💊 Available tablet names and brands</li>
                        <li>🎯 Medical uses and indications</li>
                        <li>📋 Proper usage instructions</li>
                        <li>⚠️ Side effects and precautions</li>
                        <li>💰 Cost information</li>
                        <li>🛡️ Comprehensive safety analysis</li>
                        <li>🔍 Drug interaction checking</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Additional Safety Information Section
    if st.session_state.analysis_results:
        st.markdown("---")
        st.markdown('<div class="section-header">🛡️ Important Safety Guidelines</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="info-card">
                <h4>🍺 Alcohol Interactions</h4>
                <ul>
                    <li>Check the specific alcohol interaction information above</li>
                    <li>Some medications can cause severe reactions with alcohol</li>
                    <li>Always consult your doctor about alcohol consumption</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="info-card">
                <h4>🤱 Pregnancy & Breastfeeding</h4>
                <ul>
                    <li>Medication safety varies by trimester</li>
                    <li>Many drugs can pass through breast milk</li>
                    <li>Always inform healthcare providers about pregnancy/breastfeeding</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="info-card">
                <h4>🚗 Driving Safety</h4>
                <ul>
                    <li>Some medications cause drowsiness or dizziness</li>
                    <li>Check the driving safety information above</li>
                    <li>Avoid driving if you feel impaired</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="info-card">
                <h4>💊 Drug Interactions</h4>
                <ul>
                    <li>Always provide complete medication list to doctors</li>
                    <li>Include over-the-counter drugs and supplements</li>
                    <li>Check for interactions before starting new medications</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # Key Features Section
    if not st.session_state.analysis_results:
        st.markdown("---")
        st.markdown('<div class="section-header">✨ Key Features</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">🔬</div>
                <div class="metric-label">AI-Powered Analysis</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("Advanced image recognition technology for accurate drug identification")
        
        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">🛡️</div>
                <div class="metric-label">Safety First</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("Comprehensive safety analysis including interactions and contraindications")
        
        with col3:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-value">📊</div>
                <div class="metric-label">Detailed Reports</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("Complete analysis with downloadable PDF reports for your records")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 20px; color: #666; font-size: 0.9rem;">
        <p><strong>© 2025 MediScan - Comprehensive Drug Analyzer</strong></p>
        <p>Powered by Gemini AI + Tavily | Built with ❤️ for Healthcare</p>
        <p><em>Always consult healthcare professionals for medical advice</em></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
