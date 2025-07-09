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

# Custom CSS for professional white theme
st.markdown("""
<style>
    /* Main app styling */
    .main > div {
        padding: 0rem 1rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem 1.5rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Card styling */
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border: 1px solid #e1e8ed;
        margin-bottom: 1.5rem;
    }
    
    .card h3 {
        color: #2c3e50;
        margin-top: 0;
        font-weight: 600;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 25px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Upload area styling */
    .upload-section {
        background: #f8f9fa;
        border: 2px dashed #3498db;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    /* Analysis results styling */
    .analysis-section {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border-left: 4px solid #3498db;
    }
    
    .section-header {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #3498db;
    }
    
    .section-header h4 {
        margin: 0;
        color: #2c3e50;
        font-weight: 600;
    }
    
    /* Safety styling */
    .safety-success {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .safety-warning {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .safety-danger {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    /* Disclaimer styling */
    .disclaimer {
        background: #ffe6e6;
        border: 2px solid #ff9999;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        color: #cc0000;
        font-weight: 500;
    }
    
    /* File info styling */
    .file-info {
        background: #e8f4fd;
        border: 1px solid #b8daff;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #0c5460;
    }
    
    /* Progress styling */
    .stProgress > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Spinner styling */
    .stSpinner {
        color: #667eea;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Tablet names grid */
    .tablet-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .tablet-item {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        font-weight: 500;
        color: #495057;
    }
    
    /* Download button special styling */
    .download-btn {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 25px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
        width: 100%;
        margin-top: 1rem;
    }
    
    .download-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4);
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
    """Display tablet names in a formatted grid."""
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
    
    # Display in a grid layout
    if len(tablet_names) > 1:
        # Create a grid of tablet names
        grid_html = '<div class="tablet-grid">'
        for name in tablet_names:
            if name:
                grid_html += f'<div class="tablet-item">🏷️ {name}</div>'
        grid_html += '</div>'
        st.markdown(grid_html, unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="tablet-item">🏷️ {tablet_names[0] if tablet_names else tablet_names_text}</div>', unsafe_allow_html=True)

def display_safety_info(content, safety_type):
    """Display safety information with appropriate styling."""
    if not content:
        return
    
    # Determine safety level and apply appropriate styling
    if "safe" in content.lower() or "no interaction" in content.lower():
        st.markdown(f'<div class="safety-success">✅ {content}</div>', unsafe_allow_html=True)
    elif "avoid" in content.lower() or "contraindicated" in content.lower() or "not recommended" in content.lower():
        st.markdown(f'<div class="safety-danger">❌ {content}</div>', unsafe_allow_html=True)
    elif "caution" in content.lower() or "monitor" in content.lower() or "consult" in content.lower():
        st.markdown(f'<div class="safety-warning">⚠️ {content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="safety-success">ℹ️ {content}</div>', unsafe_allow_html=True)

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

    # Professional Header
    st.markdown("""
    <div class="main-header">
        <h1>🏥 MediScan</h1>
        <p>Advanced Drug Composition Analyzer & Safety Checker</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Medical Disclaimer
    st.markdown("""
    <div class="disclaimer">
        <h4>⚠️ MEDICAL DISCLAIMER</h4>
        <p>The information provided by MediScan is for educational and informational purposes only and is not intended to replace professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition, medication, or drug interactions.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Upload Section
    st.markdown("""
    <div class="card">
        <h3>📤 Upload Tablet Image</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # File upload in a styled container
    with st.container():
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Choose a clear image of the tablet or its packaging",
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload a high-quality image for best analysis results"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        if uploaded_file:
            # Display uploaded image with file info
            col1, col2 = st.columns([2, 1])
            
            with col1:
                resized_image = resize_image_for_display(uploaded_file)
                if resized_image:
                    st.image(resized_image, caption="Uploaded Image", use_column_width=True)
            
            with col2:
                file_size = len(uploaded_file.getvalue()) / 1024
                st.markdown(f"""
                <div class="file-info">
                    <h4>📋 File Information</h4>
                    <p><strong>Name:</strong> {uploaded_file.name}</p>
                    <p><strong>Size:</strong> {file_size:.1f} KB</p>
                    <p><strong>Type:</strong> {uploaded_file.type}</p>
                </div>
                """, unsafe_allow_html=True)
    
    # Additional Medications Section
    st.markdown("""
    <div class="card">
        <h3>💊 Additional Medications (Optional)</h3>
    </div>
    """, unsafe_allow_html=True)
    
    additional_meds = st.text_area(
        "Enter any other medications you are currently taking:",
        placeholder="e.g., Aspirin 75mg daily, Metformin 500mg twice daily, Lisinopril 10mg once daily",
        help="Include medication names, dosages, and frequency for comprehensive interaction analysis",
        key="additional_medications_input",
        height=100
    )
    
    # Analyze Button
    if uploaded_file:
        if st.button("🔬 Analyze Tablet & Check Safety", key="analyze_button"):
            st.session_state.analyze_clicked = True
            st.session_state.additional_medications = additional_meds
            
            # Save uploaded file and analyze
            temp_path = save_uploaded_file(uploaded_file)
            if temp_path:
                try:
                    # Analysis progress
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("🔬 Processing image...")
                    progress_bar.progress(25)
                    
                    extracted_info = extract_composition_and_details(temp_path)
                    progress_bar.progress(70)
                    
                    if extracted_info:
                        # Store results in session state
                        st.session_state.analysis_results = extracted_info
                        st.session_state.original_image = uploaded_file.getvalue()
                        
                        # Extract drug composition for interaction analysis
                        composition_match = re.search(r"\*Composition:\*(.*?)(?=\*[\w\s]+:\*|$)", extracted_info, re.DOTALL | re.IGNORECASE)
                        if composition_match:
                            st.session_state.drug_composition = composition_match.group(1).strip()
                        
                        progress_bar.progress(85)
                        status_text.text("🔍 Analyzing drug interactions...")
                        
                        # Analyze drug interactions if additional medications provided
                        if additional_meds.strip():
                            interaction_result = analyze_drug_interactions(
                                st.session_state.drug_composition or "Unknown composition",
                                additional_meds
                            )
                            st.session_state.interaction_analysis = interaction_result
                        
                        progress_bar.progress(100)
                        status_text.text("✅ Analysis completed!")
                        
                        # Clear progress indicators after a moment
                        import time
                        time.sleep(1)
                        progress_bar.empty()
                        status_text.empty()
                        
                        st.success("🎉 Comprehensive analysis completed successfully!")
                    else:
                        st.error("❌ Analysis failed. Please try with a clearer image.")
                    
                except Exception as e:
                    st.error(f"🚨 Analysis failed: {e}")
                finally:
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
    
    # Display Results
    if st.session_state.analysis_results:
        st.markdown("""
        <div class="card">
            <h3>📊 Comprehensive Analysis Results</h3>
        </div>
        """, unsafe_allow_html=True)
        
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
            pattern = rf"\*{re.escape(section_name)}:\*(.*?)(?=\*(?:{'|'.join(re.escape(s) for s, _ in sections)}):\*|$)"
            match = re.search(pattern, analysis_text, re.DOTALL | re.IGNORECASE)
            
            if match:
                content = match.group(1).strip()
                
                # Section container
                st.markdown(f"""
                <div class="section-header">
                    <h4>{icon} {section_name}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # Special handling for different sections
                if section_name == "Available Tablet Names":
                    display_tablet_names(content)
                elif section_name in ["Safety with Alcohol", "Pregnancy Safety", "Breastfeeding Safety", "Driving Safety"]:
                    display_safety_info(content, section_name)
                else:
                    st.markdown(f'<div class="analysis-section">{content}</div>', unsafe_allow_html=True)
        
        # Display drug interaction analysis if available
        if st.session_state.interaction_analysis:
            st.markdown("""
            <div class="card">
                <h3>💊 Drug Interaction Analysis</h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"**Additional Medications:** {st.session_state.additional_medications}")
            
            # Parse interaction analysis for severity levels
            interaction_text = st.session_state.interaction_analysis
            
            if "severe" in interaction_text.lower() or "major" in interaction_text.lower():
                st.markdown('<div class="safety-danger">🚨 <strong>SEVERE/MAJOR INTERACTION DETECTED</strong></div>', unsafe_allow_html=True)
            elif "moderate" in interaction_text.lower():
                st.markdown('<div class="safety-warning">⚠️ <strong>MODERATE INTERACTION</strong></div>', unsafe_allow_html=True)
            elif "minor" in interaction_text.lower():
                st.markdown('<div class="safety-success">ℹ️ <strong>MINOR INTERACTION</strong></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="safety-success">✅ <strong>LOW INTERACTION RISK</strong></div>', unsafe_allow_html=True)
            
            st.markdown(f'<div class="analysis-section">{interaction_text}</div>', unsafe_allow_html=True)
        
        # PDF Download Section
        if st.session_state.original_image:
            st.markdown("""
            <div class="card">
                <h3>📄 Download Comprehensive Report</h3>
            </div>
            """, unsafe_allow_html=True)
            
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
                    key="pdf_download"
                )
        
        # Safety Reminders Section
        st.markdown("""
        <div class="card">
            <h3>🛡️ Important Safety Reminders</h3>
        </div>
        """, unsafe_allow_html=True)
        
        safety_col1, safety_col2 = st.columns(2)
        
        with safety_col1:
            st.markdown("""
            <div class="analysis-section">
                <h4>🍺 Alcohol Interaction Guidelines</h4>
                <ul>
                    <li>Always check specific alcohol interaction information above</li>
                    <li>Some medications can cause severe reactions with alcohol</li>
                    <li>Consult your doctor about alcohol consumption while on medication</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analysis-section">
                <h4>🤱 Pregnancy & Breastfeeding Safety</h4>
                <ul>
                    <li>Medication safety varies by trimester</li>
                    <li>Many drugs can pass through breast milk</li>
                    <li>Always inform healthcare providers about pregnancy/breastfeeding</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with safety_col2:
            st.markdown("""
            <div class="analysis-section">
                <h4>🚗 Driving Safety Guidelines</h4>
                <ul>
                    <li>Some medications cause drowsiness or dizziness</li>
                    <li>Check driving safety information above</li>
                    <li>Avoid driving if you feel impaired</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="analysis-section">
                <h4>💊 Drug Interaction Prevention</h4>
                <ul>
                    <li>Provide complete medication lists to healthcare providers</li>
                    <li>Include over-the-counter drugs and supplements</li>
                    <li>Check for interactions before starting new medications</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        # Welcome message when no results
        st.markdown("""
        <div class="card">
            <h3>🎯 How to Use MediScan</h3>
            <div class="analysis-section">
                <ol>
                    <li><strong>Upload Image:</strong> Choose a clear photo of your tablet or its packaging</li>
                    <li><strong>Add Medications:</strong> Optionally list other medications you're taking</li>
                    <li><strong>Analyze:</strong> Click the analyze button to get comprehensive results</li>
                    <li><strong>Review Results:</strong> Get detailed information about composition, uses, and safety</li>
                    <li><strong>Download Report:</strong> Save a PDF report for your records</li>
                </ol>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Features overview
        st.markdown("""
        <div class="card">
            <h3>✨ Key Features</h3>
            <div class="analysis-section">
                <div class="tablet-grid">
                    <div class="tablet-item">
                        <h4>🔬 AI-Powered Analysis</h4>
                        <p>Advanced image recognition for accurate composition identification</p>
                    </div>
                    <div class="tablet-item">
                        <h4>💊 Comprehensive Drug Info</h4>
                        <p>Detailed information about uses, dosage, and side effects</p>
                    </div>
                    <div class="tablet-item">
                        <h4>🛡️ Safety Checks</h4>
                        <p>Pregnancy, alcohol, and driving safety assessments</p>
                    </div>
                    <div class="tablet-item">
                        <h4>🔍 Interaction Analysis</h4>
                        <p>Check for dangerous drug interactions</p>
                    </div>
                    <div class="tablet-item">
                        <h4>📄 PDF Reports</h4>
                        <p>Download comprehensive analysis reports</p>
                    </div>
                    <div class="tablet-item">
                        <h4>💰 Cost Information</h4>
                        <p>Get pricing information for medications</p>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 2rem; margin-top: 3rem; border-top: 1px solid #e1e8ed; color: #6c757d;">
        <p>© 2025 MediScan - Comprehensive Drug Analyzer | Powered by Gemini AI + Tavily</p>
        <p><small>Professional healthcare technology for informed medication decisions</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
