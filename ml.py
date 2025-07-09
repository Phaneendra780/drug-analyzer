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
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Global font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid #e2e8f0;
        text-align: center;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a202c;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .main-subtitle {
        font-size: 1.1rem;
        color: #718096;
        font-weight: 500;
    }
    
    /* Disclaimer banner */
    .disclaimer-banner {
        background: linear-gradient(135deg, #fed7d7 0%, #feb2b2 100%);
        border: 2px solid #fc8181;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 2px 10px rgba(252, 129, 129, 0.1);
    }
    
    .disclaimer-title {
        color: #c53030;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    
    .disclaimer-text {
        color: #742a2a;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    
    /* Card styling */
    .custom-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .custom-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
    }
    
    .card-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #e2e8f0;
    }
    
    .card-title {
        font-size: 1.4rem;
        font-weight: 600;
        color: #2d3748;
    }
    
    /* Upload area styling */
    .upload-area {
        border: 3px dashed #cbd5e0;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        background: #f7fafc;
        margin: 1rem 0;
        transition: all 0.3s ease;
    }
    
    .upload-area:hover {
        border-color: #4299e1;
        background: #ebf8ff;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-size: 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(66, 153, 225, 0.3);
        width: 100%;
        margin-top: 1rem;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(66, 153, 225, 0.4);
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: linear-gradient(135deg, #c6f6d5 0%, #9ae6b4 100%);
        border: 1px solid #68d391;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .stError {
        background: linear-gradient(135deg, #fed7d7 0%, #feb2b2 100%);
        border: 1px solid #fc8181;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Analysis results styling */
    .analysis-section {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #4299e1;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    }
    
    .analysis-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .analysis-content {
        color: #4a5568;
        line-height: 1.6;
    }
    
    /* Tablet names grid */
    .tablet-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .tablet-card {
        background: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        font-weight: 500;
        color: #2d3748;
        transition: all 0.3s ease;
    }
    
    .tablet-card:hover {
        background: #ebf8ff;
        border-color: #4299e1;
    }
    
    /* Footer */
    .footer {
        background: #f7fafc;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        color: #718096;
        font-size: 0.9rem;
        margin-top: 2rem;
        border: 1px solid #e2e8f0;
    }
    
    /* Spinner customization */
    .stSpinner {
        text-align: center;
        padding: 2rem;
    }
    
    /* File uploader styling */
    .stFileUploader {
        background: #f7fafc;
        border: 2px dashed #cbd5e0;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
    }
    
    .stFileUploader:hover {
        border-color: #4299e1;
        background: #ebf8ff;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #38a169 0%, #2f855a 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-size: 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(56, 161, 105, 0.3);
        width: 100%;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(56, 161, 105, 0.4);
    }
    
    /* Info box styling */
    .stInfo {
        background: linear-gradient(135deg, #bee3f8 0%, #90cdf4 100%);
        border: 1px solid #4299e1;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2rem;
        }
        
        .custom-card {
            padding: 1.5rem;
        }
        
        .tablet-grid {
            grid-template-columns: 1fr;
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
You are an expert in pharmaceutical analysis and AI-driven drug composition recognition.
Your role is to analyze a tablet's composition from an image, identify its ingredients, and provide comprehensive insights about the drug.

Additionally, once a drug composition is identified, retrieve and display its uses, side effects, cost, and most importantly, the available tablet names/brands that contain this composition using reliable medical sources.
Ensure that you fetch accurate and specific details instead of generic placeholders.
"""

INSTRUCTIONS = """
- Extract only the drug composition from the tablet image.
- Use this composition to fetch and return its uses, side effects, cost, and available tablet names from trusted medical sources.
- For tablet names, search for brand names, generic names, and commercial names that contain the identified composition.
- Ensure that the AI provides detailed and relevant drug information.
- Return all information in a structured format:
  *Composition:* <composition>
  *Available Tablet Names:* <list of brand names and generic names that contain this composition>
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
                "Extract the drug composition from this tablet image and provide its uses, side effects, cost, and available tablet names/brands that contain this composition.",
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
    
    # Display in a professional grid layout
    if len(tablet_names) > 1:
        st.markdown('<div class="tablet-grid">', unsafe_allow_html=True)
        
        # Create columns for better layout
        cols = st.columns(min(3, len(tablet_names)))
        
        for i, name in enumerate(tablet_names):
            if name:  # Only display non-empty names
                with cols[i % len(cols)]:
                    st.markdown(f'<div class="tablet-card">🏷️ {name}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="tablet-card">🏷️ {tablet_names[0] if tablet_names else tablet_names_text}</div>', unsafe_allow_html=True)

def main():
    # Initialize session state for button tracking
    if 'analyze_clicked' not in st.session_state:
        st.session_state.analyze_clicked = False
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'original_image' not in st.session_state:
        st.session_state.original_image = None

    # Header
    st.markdown("""
    <div class="main-header">
        <h1 class="main-title">🏥 MediScan</h1>
        <p class="main-subtitle">AI-Powered Drug Composition Analyzer</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Medical disclaimer
    st.markdown("""
    <div class="disclaimer-banner">
        <div class="disclaimer-title">⚠️ MEDICAL DISCLAIMER</div>
        <div class="disclaimer-text">
            The information provided by MediScan is for educational and informational purposes only and is not intended to replace professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition or medication.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content in two columns
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown("""
        <div class="custom-card">
            <div class="card-header">
                <span style="font-size: 1.5rem;">📤</span>
                <h2 class="card-title">Upload Tablet Image</h2>
            </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Upload a clear image of the tablet",
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload a clear, high-quality image of the tablet or its packaging",
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            # Display uploaded image
            resized_image = resize_image_for_display(uploaded_file)
            if resized_image:
                st.image(resized_image, caption="Uploaded Tablet Image", width=MAX_IMAGE_WIDTH)
                
                # Display file info
                file_size = len(uploaded_file.getvalue()) / 1024  # Convert to KB
                st.info(f"📄 **{uploaded_file.name}** • {file_size:.1f} KB")
            
            # Analyze button
            if st.button("🔬 Analyze Tablet Composition", type="primary"):
                st.session_state.analyze_clicked = True
                
                # Save uploaded file and analyze
                temp_path = save_uploaded_file(uploaded_file)
                if temp_path:
                    try:
                        extracted_info = extract_composition_and_details(temp_path)
                        
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
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="custom-card">
            <div class="card-header">
                <span style="font-size: 1.5rem;">📊</span>
                <h2 class="card-title">Analysis Results</h2>
            </div>
        """, unsafe_allow_html=True)
        
        # Display results if available
        if st.session_state.analysis_results:
            analysis_text = st.session_state.analysis_results
            
            # Extract sections using regex - Updated to include "Available Tablet Names"
            sections = [
                ("Composition", "🧬"),
                ("Available Tablet Names", "🏷️"),
                ("Uses", "💊"), 
                ("Side Effects", "⚠️"),
                ("Cost", "💰")
            ]
            
            for section, icon in sections:
                # Updated pattern to handle "Available Tablet Names"
                pattern = rf"\*{re.escape(section)}:\*(.*?)(?=\*(?:Composition|Available Tablet Names|Uses|Side Effects|Cost):\*|$)"
                match = re.search(pattern, analysis_text, re.DOTALL | re.IGNORECASE)
                
                if match:
                    content = match.group(1).strip()
                    
                    st.markdown(f"""
                    <div class="analysis-section">
                        <div class="analysis-title">{icon} {section}</div>
                        <div class="analysis-content">
                    """, unsafe_allow_html=True)
                    
                    # Special handling for tablet names
                    if section == "Available Tablet Names":
                        display_tablet_names(content)
                    else:
                        st.write(content)
                    
                    st.markdown("</div></div>", unsafe_allow_html=True)
            
            # PDF download section
            if st.session_state.original_image:
                st.markdown("### 📄 Download Report")
                
                pdf_bytes = create_pdf(st.session_state.original_image, st.session_state.analysis_results)
                if pdf_bytes:
                    download_filename = f"mediscan_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_bytes,
                        file_name=download_filename,
                        mime="application/pdf",
                        help="Download a professionally formatted PDF report"
                    )
        else:
            st.info("📋 Upload a tablet image and click 'Analyze' to see results here.")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div class="footer">
        © 2025 MediScan - Drug Composition Analyzer | Powered by Gemini AI + Tavily
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
