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
    page_title="MediScan - Drug Composition Analyzer",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏥"
)

# Custom CSS for modern design with animations and gradients
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Inter', sans-serif;
        min-height: 100vh;
    }
    
    /* Header styles */
    .main-header {
        background: linear-gradient(135deg, #ff6b6b, #4ecdc4, #45b7d1);
        background-size: 200% 200%;
        animation: gradient-shift 8s ease infinite;
        padding: 2rem 0;
        text-align: center;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        backdrop-filter: blur(10px);
    }
    
    .main-header h1 {
        color: white;
        font-size: 3rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        animation: pulse 2s ease-in-out infinite alternate;
    }
    
    .subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 1.2rem;
        margin-top: 0.5rem;
        font-weight: 400;
    }
    
    @keyframes gradient-shift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        100% { transform: scale(1.05); }
    }
    
    /* Card styles */
    .glass-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        animation: slideInUp 0.6s ease-out;
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.2);
    }
    
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Upload section */
    .upload-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        animation: float 3s ease-in-out infinite;
    }
    
    .upload-section::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
        animation: shimmer 3s infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    /* Button styles */
    .stButton > button {
        background: linear-gradient(135deg, #ff6b6b, #4ecdc4);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 0.8rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 8px 20px rgba(255,107,107,0.3);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        transition: left 0.6s;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 30px rgba(255,107,107,0.4);
    }
    
    /* Results section */
    .results-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 2rem;
        animation: slideInRight 0.8s ease-out;
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .result-section {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #4ecdc4;
        transition: all 0.3s ease;
        animation: fadeInUp 0.6s ease-out;
    }
    
    .result-section:hover {
        transform: translateX(10px);
        background: rgba(255, 255, 255, 0.15);
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Tablet name tags */
    .tablet-tag {
        background: linear-gradient(135deg, #ff6b6b, #4ecdc4);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        display: inline-block;
        margin: 0.3rem;
        font-weight: 500;
        animation: bounceIn 0.8s ease-out;
        transition: all 0.3s ease;
    }
    
    .tablet-tag:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(255,107,107,0.3);
    }
    
    @keyframes bounceIn {
        0% { transform: scale(0.3); opacity: 0; }
        50% { transform: scale(1.05); }
        70% { transform: scale(0.9); }
        100% { transform: scale(1); opacity: 1; }
    }
    
    /* Spinner animation */
    .stSpinner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Warning/Info boxes */
    .stAlert {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        animation: slideInLeft 0.6s ease-out;
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    /* File uploader */
    .stFileUploader {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 2px dashed rgba(255, 255, 255, 0.3);
        padding: 2rem;
        transition: all 0.3s ease;
    }
    
    .stFileUploader:hover {
        border-color: #4ecdc4;
        background: rgba(255, 255, 255, 0.15);
    }
    
    /* Progress bar */
    .stProgress .progress-bar {
        background: linear-gradient(135deg, #ff6b6b, #4ecdc4);
        border-radius: 10px;
        animation: progressGlow 2s ease-in-out infinite alternate;
    }
    
    @keyframes progressGlow {
        0% { box-shadow: 0 0 5px rgba(255,107,107,0.5); }
        100% { box-shadow: 0 0 20px rgba(255,107,107,0.8); }
    }
    
    /* Download button */
    .download-btn {
        background: linear-gradient(135deg, #4ecdc4, #44a08d);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 1rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 8px 20px rgba(78,205,196,0.3);
        animation: pulse 2s ease-in-out infinite alternate;
    }
    
    .download-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 30px rgba(78,205,196,0.4);
    }
    
    /* Footer */
    .footer {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 1rem;
        text-align: center;
        margin-top: 2rem;
        animation: fadeIn 1s ease-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    /* Text styles */
    h1, h2, h3 {
        color: white;
        font-weight: 700;
    }
    
    p, div {
        color: rgba(255, 255, 255, 0.9);
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        
        .glass-card {
            padding: 1rem;
        }
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #ff6b6b, #4ecdc4);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #4ecdc4, #ff6b6b);
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
        # Create a progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Animate progress bar
        for i in range(100):
            progress_bar.progress(i + 1)
            if i < 30:
                status_text.text("🔬 Analyzing tablet image...")
            elif i < 60:
                status_text.text("🔍 Identifying composition...")
            elif i < 80:
                status_text.text("📊 Retrieving medical information...")
            else:
                status_text.text("✨ Finalizing analysis...")
            time.sleep(0.02)
        
        response = agent.run(
            "Extract the drug composition from this tablet image and provide its uses, side effects, cost, and available tablet names/brands that contain this composition.",
            images=[image_path],
        )
        
        progress_bar.empty()
        status_text.empty()
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
    """Display tablet names in a formatted way with beautiful tags."""
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
    
    # Display in a beautiful tag format
    st.markdown('<div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">', unsafe_allow_html=True)
    for name in tablet_names:
        if name:  # Only display non-empty names
            st.markdown(f'<span class="tablet-tag">🏷️ {name}</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    # Initialize session state for button tracking
    if 'analyze_clicked' not in st.session_state:
        st.session_state.analyze_clicked = False
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'original_image' not in st.session_state:
        st.session_state.original_image = None

    # Animated Header
    st.markdown("""
    <div class="main-header">
        <h1>🏥 MediScan</h1>
        <p class="subtitle">AI-Powered Drug Composition Analyzer</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Medical disclaimer with glass effect
    st.markdown("""
    <div class="glass-card">
        <h3>⚠️ MEDICAL DISCLAIMER</h3>
        <p>The information provided by MediScan is for educational and informational purposes only and is not intended to replace professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition or medication.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content in two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        <div class="upload-section">
            <h2>📤 Upload Tablet Image</h2>
            <p>Upload a clear, high-quality image of the tablet or its packaging</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload a clear, high-quality image of the tablet or its packaging"
        )
        
        if uploaded_file:
            # Display uploaded image with animation
            resized_image = resize_image_for_display(uploaded_file)
            if resized_image:
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.image(resized_image, caption="Uploaded Tablet Image", width=MAX_IMAGE_WIDTH)
                
                # Display file info
                file_size = len(uploaded_file.getvalue()) / 1024  # Convert to KB
                st.success(f"**{uploaded_file.name}** • {file_size:.1f} KB")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Analyze button with custom styling
            if st.button("🔬 Analyze Tablet Composition", key="analyze_btn"):
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
                            st.balloons()  # Celebration animation
                            st.success("✅ Analysis completed successfully!")
                        else:
                            st.error("❌ Analysis failed. Please try with a clearer image.")
                        
                    except Exception as e:
                        st.error(f"🚨 Analysis failed: {e}")
                    finally:
                        # Clean up temp file
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
    
    with col2:
        st.markdown("""
        <div class="results-container">
            <h2>📊 Analysis Results</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Display results if available
        if st.session_state.analysis_results:
            analysis_text = st.session_state.analysis_results
            
            # Extract sections using regex
            sections = ["Composition", "Available Tablet Names", "Uses", "Side Effects", "Cost"]
            
            for section in sections:
                pattern = rf"\*{re.escape(section)}:\*(.*?)(?=\*(?:Composition|Available Tablet Names|Uses|Side Effects|Cost):\*|$)"
                match = re.search(pattern, analysis_text, re.DOTALL | re.IGNORECASE)
                
                if match:
                    content = match.group(1).strip()
                    
                    # Choose appropriate icon for each section
                    icons = {
                        "Composition": "🧬",
                        "Available Tablet Names": "🏷️",
                        "Uses": "💊", 
                        "Side Effects": "⚠️",
                        "Cost": "💰"
                    }
                    
                    st.markdown(f"""
                    <div class="result-section">
                        <h3>{icons.get(section, '📋')} {section}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Special handling for tablet names
                    if section == "Available Tablet Names":
                        display_tablet_names(content)
                    else:
                        st.markdown(f'<div class="glass-card">{content}</div>', unsafe_allow_html=True)
            
            # PDF download section with custom styling
            if st.session_state.original_image:
                st.markdown("""
                <div class="glass-card">
                    <h3>📄 Download Report</h3>
                </div>
                """, unsafe_allow_html=True)
                
                pdf_bytes = create_pdf(st.session_state.original_image, st.session_state.analysis_results)
                if pdf_bytes:
                    download_filename = f"mediscan_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_bytes,
                        file_name=download_filename,
                        mime="application/pdf",
                        help="Download a professionally formatted PDF report",
                        key="download_pdf"
                    )
        else:
            st.markdown("""
            <div class="glass-card">
                <p>🚀 Upload a tablet image and click 'Analyze' to see magical results here!</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Animated Footer
    st.markdown("""
    <div class="footer">
        <p>© 2025 MediScan - Drug Composition Analyzer | Powered by Gemini AI + Tavily ✨</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
