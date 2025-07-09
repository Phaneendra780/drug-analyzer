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

# Set page configuration with 1mg inspired theme
st.set_page_config(
    page_title="MediScan - AI Drug Analyzer",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏥"
)

# Custom CSS inspired by Tata 1mg design
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #f8fffe 0%, #f1f8ff 100%);
    }
    
    /* Header Styles */
    .main-header {
        background: linear-gradient(135deg, #ff6b35 0%, #ff8c42 100%);
        padding: 2rem 0;
        margin: -1rem -1rem 2rem -1rem;
        border-radius: 0 0 20px 20px;
        box-shadow: 0 4px 20px rgba(255, 107, 53, 0.3);
    }
    
    .header-content {
        text-align: center;
        color: white;
    }
    
    .header-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .header-subtitle {
        font-size: 1.2rem;
        font-weight: 400;
        opacity: 0.9;
        margin-bottom: 1rem;
    }
    
    .header-features {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin-top: 1rem;
        flex-wrap: wrap;
    }
    
    .feature-badge {
        background: rgba(255, 255, 255, 0.2);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        backdrop-filter: blur(10px);
    }
    
    /* Card Styles */
    .upload-card, .results-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 2rem;
        transition: all 0.3s ease;
    }
    
    .upload-card:hover, .results-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
    }
    
    .card-header {
        display: flex;
        align-items: center;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #f0f0f0;
    }
    
    .card-icon {
        font-size: 2rem;
        margin-right: 1rem;
        color: #ff6b35;
    }
    
    .card-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #2d3748;
        margin: 0;
    }
    
    /* Upload Area Styles */
    .upload-area {
        border: 2px dashed #ff6b35;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        background: linear-gradient(135deg, #fff5f2 0%, #ffeee8 100%);
        transition: all 0.3s ease;
        margin: 1rem 0;
    }
    
    .upload-area:hover {
        border-color: #ff8c42;
        background: linear-gradient(135deg, #fff2ee 0%, #ffebe4 100%);
    }
    
    .upload-icon {
        font-size: 3rem;
        color: #ff6b35;
        margin-bottom: 1rem;
    }
    
    .upload-text {
        font-size: 1.1rem;
        color: #4a5568;
        margin-bottom: 0.5rem;
    }
    
    .upload-hint {
        font-size: 0.9rem;
        color: #718096;
    }
    
    /* Button Styles */
    .stButton > button {
        background: linear-gradient(135deg, #ff6b35 0%, #ff8c42 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 25px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 107, 53, 0.3);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 107, 53, 0.4);
    }
    
    /* Results Section Styles */
    .result-section {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #ff6b35;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }
    
    .result-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
        font-weight: 600;
        color: #2d3748;
        font-size: 1.2rem;
    }
    
    .result-icon {
        margin-right: 0.5rem;
        font-size: 1.5rem;
    }
    
    .tablet-name-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }
    
    .tablet-name-card {
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .tablet-name-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        border-color: #ff6b35;
    }
    
    /* Disclaimer Styles */
    .disclaimer-box {
        background: linear-gradient(135deg, #fed7d7 0%, #feb2b2 100%);
        border: 1px solid #fc8181;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 12px rgba(252, 129, 129, 0.2);
    }
    
    .disclaimer-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
        font-weight: 600;
        color: #c53030;
        font-size: 1.1rem;
    }
    
    .disclaimer-content {
        color: #742a2a;
        line-height: 1.6;
    }
    
    /* Progress and Status */
    .status-success {
        background: linear-gradient(135deg, #c6f6d5 0%, #9ae6b4 100%);
        border: 1px solid #68d391;
        color: #276749;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .status-error {
        background: linear-gradient(135deg, #fed7d7 0%, #feb2b2 100%);
        border: 1px solid #fc8181;
        color: #c53030;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Image Display */
    .image-container {
        text-align: center;
        margin: 1rem 0;
    }
    
    .image-container img {
        border-radius: 12px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
        max-width: 100%;
        height: auto;
    }
    
    .image-info {
        background: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem;
        margin-top: 1rem;
        font-size: 0.9rem;
        color: #4a5568;
    }
    
    /* Footer */
    .footer {
        background: #2d3748;
        color: white;
        padding: 2rem 0;
        margin: 3rem -1rem -1rem -1rem;
        border-radius: 20px 20px 0 0;
        text-align: center;
    }
    
    .footer-content {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 2rem;
        flex-wrap: wrap;
    }
    
    .footer-badge {
        background: rgba(255, 255, 255, 0.1);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .header-features {
            flex-direction: column;
            gap: 1rem;
        }
        
        .tablet-name-grid {
            grid-template-columns: 1fr;
        }
        
        .header-title {
            font-size: 2rem;
        }
        
        .upload-card, .results-card {
            padding: 1.5rem;
        }
    }
    
    /* Hide Streamlit elements */
    .stDeployButton {
        display: none;
    }
    
    #MainMenu {
        visibility: hidden;
    }
    
    .stFooter {
        display: none;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #ff6b35;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #ff8c42;
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

MAX_IMAGE_WIDTH = 350

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
        
        content.append(Paragraph("🏥 MediScan - Drug Composition Analysis Report", title_style))
        content.append(Spacer(1, 0.25*inch))
        
        content.append(Paragraph(
            "⚠️ MEDICAL DISCLAIMER: This information is provided for educational purposes only and should not replace professional medical advice. "
            "Always consult with a healthcare professional before making any medical decisions.",
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
        
        content.append(Paragraph("🔬 Analysis Results:", heading_style))
        
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
            else:
                clean_results = analysis_results.replace('<', '&lt;').replace('>', '&gt;')
                content.append(Paragraph(clean_results, normal_style))
        
        content.append(Spacer(1, 0.5*inch))
        content.append(Paragraph("© 2025 MediScan - AI Drug Analyzer | Powered by Gemini AI + Tavily", 
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
    
    if len(tablet_names) > 1:
        st.markdown('<div class="tablet-name-grid">', unsafe_allow_html=True)
        for name in tablet_names:
            if name:
                st.markdown(f'<div class="tablet-name-card">🏷️ <strong>{name}</strong></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="tablet-name-card">🏷️ <strong>{tablet_names[0] if tablet_names else tablet_names_text}</strong></div>', unsafe_allow_html=True)

def main():
    # Initialize session state
    if 'analyze_clicked' not in st.session_state:
        st.session_state.analyze_clicked = False
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'original_image' not in st.session_state:
        st.session_state.original_image = None

    # Header Section
    st.markdown("""
    <div class="main-header">
        <div class="header-content">
            <h1 class="header-title">🏥 MediScan</h1>
            <p class="header-subtitle">AI-Powered Drug Composition Analyzer</p>
            <div class="header-features">
                <div class="feature-badge">📱 Instant Analysis</div>
                <div class="feature-badge">🔬 AI-Powered</div>
                <div class="feature-badge">📊 Detailed Reports</div>
                <div class="feature-badge">🌟 Trusted Results</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Medical Disclaimer
    st.markdown("""
    <div class="disclaimer-box">
        <div class="disclaimer-header">
            ⚠️ MEDICAL DISCLAIMER
        </div>
        <div class="disclaimer-content">
            The information provided by MediScan is for educational and informational purposes only and is not intended to replace professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition or medication.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content in two columns
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown("""
        <div class="upload-card">
            <div class="card-header">
                <div class="card-icon">📤</div>
                <h2 class="card-title">Upload Tablet Image</h2>
            </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose a tablet image",
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload a clear, high-quality image of the tablet or its packaging",
            label_visibility="collapsed"
        )
        
        if not uploaded_file:
            st.markdown("""
            <div class="upload-area">
                <div class="upload-icon">📷</div>
                <div class="upload-text">Drag and drop your tablet image here</div>
                <div class="upload-hint">Supports JPG, PNG, WEBP formats</div>
            </div>
            """, unsafe_allow_html=True)
        
        if uploaded_file:
            # Display uploaded image
            resized_image = resize_image_for_display(uploaded_file)
            if resized_image:
                st.markdown('<div class="image-container">', unsafe_allow_html=True)
                st.image(resized_image, caption="Uploaded Tablet Image", width=MAX_IMAGE_WIDTH)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Display file info
                file_size = len(uploaded_file.getvalue()) / 1024
                st.markdown(f"""
                <div class="image-info">
                    📄 <strong>{uploaded_file.name}</strong> • {file_size:.1f} KB
                </div>
                """, unsafe_allow_html=True)
            
            # Analyze button
            if st.button("🔬 Analyze Tablet Composition"):
                st.session_state.analyze_clicked = True
                
                temp_path = save_uploaded_file(uploaded_file)
                if temp_path:
                    try:
                        extracted_info = extract_composition_and_details(temp_path)
                        
                        st.session_state.analysis_results = extracted_info
                        st.session_state.original_image = uploaded_file.getvalue()
                        
                        if extracted_info:
                            st.markdown("""
                            <div class="status-success">
                                ✅ Analysis completed successfully!
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div class="status-error">
                                ❌ Analysis failed. Please try with a clearer image.
                            </div>
                            """, unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.markdown(f"""
                        <div class="status-error">
                            🚨 Analysis failed: {e}
                        </div>
                        """, unsafe_allow_html=True)
                    finally:
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="results-card">
            <div class="card-header">
                <div class="card-icon">📊</div>
                <h2 class="card-title">Analysis Results</h2>
            </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.analysis_results:
            analysis_text = st.session_state.analysis_results
            
            # Extract sections
            sections = [
                ("Composition", "🧬"),
                ("Available Tablet Names", "🏷️"),
                ("Uses", "💊"),
                ("Side Effects", "⚠️"),
                ("Cost", "💰")
            ]
            
            for section, icon in sections:
                pattern = rf"\*{re.escape(section)}:\*(.*?)(?=\*(?:Composition|Available Tablet Names|Uses|Side Effects|Cost):\*|$)"
                match = re.search(pattern, analysis_text, re.DOTALL | re.IGNORECASE)
                
                if match:
                    content = match.group(1).strip()
                    
                    st.markdown(f"""
                    <div class="result-section">
                        <div class="result-header">
                            <span class="result-icon">{icon}</span>
                            {section}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if section == "Available Tablet Names":
                        display_tablet_names(content)
                    else:
                        st.write(content)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
            
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
            st.markdown("""
            <div style="text-align: center; padding: 3rem; color: #718096;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
                <h3 style="color: #4a5568; margin-bottom: 1rem;">Ready to Analyze</h3>
                <p>Upload a tablet image and click 'Analyze' to see comprehensive drug information here.</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div class="footer">
        <div class="footer-content">
            <div class="footer-badge">© 2025 MediScan</div>
            <div class="footer-badge">Powered by Gemini AI</div>
            <div class="footer-badge">Tavily Search</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
