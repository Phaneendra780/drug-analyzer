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
    page_title="Drug Composition Analyzer",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="💊"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #E5E7EB;
    }
    .subheader {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1E3A8A;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .card {
        background-color: #F9FAFB;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
    }
    .success-box {
        background-color: #D1FAE5;
        border-left: 5px solid #059669;
        padding: 1rem;
        border-radius: 5px;
    }
    .warning-box {
        background-color: #FEF3C7;
        border-left: 5px solid #D97706;
        padding: 1rem;
        border-radius: 5px;
    }
    .info-box {
        background-color: #E0F2FE;
        border-left: 5px solid #0284C7;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .disclaimer-box {
        background-color: #FEE2E2;
        border-left: 5px solid #DC2626;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .stButton>button {
        background-color: #1E3A8A;
        color: white;
        font-weight: 600;
        border-radius: 5px;
        padding: 0.5rem 2rem;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #1E40AF;
    }
    .upload-section {
        border: 2px dashed #CBD5E1;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin-bottom: 2rem;
        background-color: #F8FAFC;
    }
    .info-label {
        font-weight: 600;
        color: #1E3A8A;
    }
    .centered-image {
        display: flex;
        justify-content: center;
    }
    .file-uploader {
        margin-bottom: 1rem;
    }
    .tagline {
        text-align: center;
        font-size: 1.2rem;
        font-weight: 600;
        color: #4F46E5;
        margin: 1.5rem auto;
        padding: 0.75rem;
        border-radius: 0.5rem;
        background-color: #EEF2FF;
        max-width: 400px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .dark-tagline {
        text-align: center;
        font-size: 1.2rem;
        font-weight: 600;
        color: #E0F2FE;
        margin: 1.5rem auto;
        padding: 0.75rem;
        border-radius: 0.5rem;
        background-color: #1E3A8A;
        max-width: 400px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .download-btn {
        background-color: #047857 !important;
        margin-top: 1rem;
    }
    .download-btn:hover {
        background-color: #065F46 !important;
    }
</style>
""", unsafe_allow_html=True)

# API Keys
os.environ["TAVILY_API_KEY"] = "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"
os.environ["GOOGLE_API_KEY"] = "AIzaSyDwfkMVSSm5xUiMLagaE1NdMDLYaBz-9S8"

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

if not TAVILY_API_KEY or not GOOGLE_API_KEY:
    st.error("API keys are missing. Please check your configuration.")
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
        st.error(f"Error initializing agent: {e}")
        return None

def resize_image_for_display(image_file):
    """Resize image for display only, returns bytes."""
    try:
        img = Image.open(image_file)
        image_file.seek(0)
        aspect_ratio = img.height / img.width
        new_height = int(MAX_IMAGE_WIDTH * aspect_ratio)
        img = img.resize((MAX_IMAGE_WIDTH, new_height), Image.Resampling.LANCZOS)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        st.error(f"Error resizing image: {e}")
        return None

def extract_composition_and_details(image_path):
    """Extract composition and related drug details from the tablet image using AI."""
    agent = get_agent()
    if agent is None:
        return None

    try:
        with st.spinner("🔍 Analyzing tablet image and retrieving medical information..."):
            response = agent.run(
                "Extract the drug composition from this tablet image and provide its uses, side effects, and cost.",
                images=[image_path],
            )
            return response.content.strip()
    except Exception as e:
        st.error(f"Error extracting composition and details: {e}")
        return None

def save_uploaded_file(uploaded_file):
    """Save the uploaded file to disk."""
    try:
        with NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_path = temp_file.name
        return temp_path
    except Exception as e:
        st.error(f"Error saving uploaded file: {e}")
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
            fontSize=16,
            alignment=1,
            spaceAfter=12
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
            borderRadius=5,
            backColor=colors.pink,
            alignment=1
        )
        
        # Title
        content.append(Paragraph("Drug Composition Analysis Report", title_style))
        content.append(Spacer(1, 0.25*inch))
        
        # Disclaimer
        content.append(Paragraph(
            "DISCLAIMER: This information is provided for educational purposes only and should not replace professional medical advice. "
            "Always consult with a healthcare professional before making any medical decisions.",
            disclaimer_style
        ))
        content.append(Spacer(1, 0.25*inch))
        
        # Date and time
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content.append(Paragraph(f"Generated on: {current_datetime}", normal_style))
        content.append(Spacer(1, 0.25*inch))
        
        # Add image if available
        if image_data:
            img_temp = BytesIO(image_data)
            img = Image.open(img_temp)
            img_width, img_height = img.size
            aspect = img_height / float(img_width)
            display_width = 4 * inch
            display_height = display_width * aspect
            img_obj = ReportLabImage(img_temp, width=display_width, height=display_height)
            content.append(Paragraph("Analyzed Image:", heading_style))
            content.append(img_obj)
            content.append(Spacer(1, 0.25*inch))
        
        # Analysis results
        content.append(Paragraph("Analysis Results:", heading_style))
        
        # Format the analysis results for PDF - fixed version using regex
        if analysis_results:
            # Use regex to find sections in the format "*SectionName:* Content"
            section_pattern = r"\*([\w\s]+):\*(.*?)(?=\*[\w\s]+:\*|$)"
            matches = re.findall(section_pattern, analysis_results, re.DOTALL)
            
            for section_title, section_content in matches:
                content.append(Paragraph(f"<b>{section_title}:</b>", normal_style))
                
                # Handle multiline content
                paragraphs = section_content.strip().split("\n")
                for para in paragraphs:
                    if para.strip():
                        content.append(Paragraph(para.strip(), normal_style))
                
                content.append(Spacer(1, 0.15*inch))
        
        # Footer
        content.append(Spacer(1, 0.5*inch))
        content.append(Paragraph("© 2025 Drug Composition Analyzer | Powered by Gemini AI + Tavily", 
                                ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.gray)))
        
        # Build PDF
        pdf.build(content)
        
        # Get the PDF value from the buffer
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"Error creating PDF: {e}")
        return None

def get_pdf_download_link(pdf_bytes, filename="drug_analysis_report.pdf"):
    """Generate a download link for the PDF file."""
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" class="download-link">Download PDF Report</a>'
    return href

def main():
    # Header with logo
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="main-header">💊 Drug Composition Analyzer</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem; color: #6B7280;">
            Upload a tablet image to analyze its composition, uses, side effects, and cost
        </div>
        """, unsafe_allow_html=True)
    
    # Disclaimer
    st.markdown("""
    <div class="disclaimer-box">
        <div style="display: flex; align-items: center;">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">⚠️</span>
            <div>
                <div style="font-weight: 600;">MEDICAL DISCLAIMER</div>
                <div>The information provided by this application is for educational purposes only and is not intended to replace professional medical advice, diagnosis, or treatment. 
                     Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition or medication.
                     Never disregard professional medical advice or delay in seeking it because of something you have read on this application.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main content in a two-column layout
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        # Tagline above the upload section
        st.markdown('<div class="tagline">📋 Find your tablets in minutes, not hours!</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload tablet image",
            type=["jpg", "jpeg", "png"],
            help="Upload a clear image of the tablet's ingredient list",
            label_visibility="collapsed",
            key="image_uploader"
        )
        
        if uploaded_file:
            resized_image = resize_image_for_display(uploaded_file)
            if resized_image:
                st.markdown('<div class="centered-image">', unsafe_allow_html=True)
                st.image(resized_image, caption="Uploaded Image", width=MAX_IMAGE_WIDTH)
                st.markdown('</div>', unsafe_allow_html=True)
                
                analyze_button = st.button("🔍 Analyze Tablet")
        else:
            st.markdown("""
            <div style="text-align: center; color: #6B7280; margin-top: 2rem;">
                <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" fill="currentColor" viewBox="0 0 16 16" style="margin-bottom: 1rem;">
                    <path d="M4.406 1.342A5.53 5.53 0 0 1 8 0c2.69 0 4.923 2 5.166 4.579C14.758 4.804 16 6.137 16 7.773 16 9.569 14.502 11 12.687 11H10a.5.5 0 0 1 0-1h2.688C13.979 10 15 8.988 15 7.773c0-1.216-1.02-2.228-2.313-2.228h-.5v-.5C12.188 2.825 10.328 1 8 1a4.53 4.53 0 0 0-2.941 1.1c-.757.652-1.153 1.438-1.153 2.055v.448l-.445.049C2.064 4.805 1 5.952 1 7.318 1 8.785 2.23 10 3.781 10H6a.5.5 0 0 1 0-1H3.781C1.708 11 0 9.366 0 7.318c0-1.763 1.266-3.223 2.942-3.593.143-.863.698-1.723 1.464-2.383z"/>
                    <path d="M7.646 4.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 5.707V14.5a.5.5 0 0 1-1 0V5.707L5.354 7.854a.5.5 0 1 1-.708-.708l3-3z"/>
                </svg>
                <p>Drag and drop or click to upload a tablet image</p>
                <p style="font-size: 0.8rem;">Supported formats: JPG, JPEG, PNG</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Tagline above the results section
        st.markdown('<div class="dark-tagline">🔍 Accurate medication details in seconds!</div>', unsafe_allow_html=True)
        
        if uploaded_file and 'analyze_button' in locals() and analyze_button:
            temp_path = save_uploaded_file(uploaded_file)
            if temp_path:
                extracted_info = extract_composition_and_details(temp_path)
                os.unlink(temp_path)  # Clean up

                # Store original image for PDF
                original_image = uploaded_file.getvalue()

                if extracted_info:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown('<div class="subheader">Analysis Results</div>', unsafe_allow_html=True)
                    
                    # Format the extracted information with better styling
                    formatted_info = extracted_info.replace(
                        "*Composition:*", "<div class='info-label'>Composition:</div>"
                    ).replace(
                        "*Uses:*", "<div class='info-label'>Uses:</div>"
                    ).replace(
                        "*Side Effects:*", "<div class='info-label'>Side Effects:</div>"
                    ).replace(
                        "*Cost:*", "<div class='info-label'>Cost:</div>"
                    )
                    
                    st.markdown(formatted_info, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Create PDF report
                    pdf_bytes = create_pdf(original_image, extracted_info)
                    if pdf_bytes:
                        st.markdown("<div style='text-align: center; margin-top: 1rem;'>", unsafe_allow_html=True)
                        download_filename = f"drug_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        st.download_button(
                            label="📄 Download PDF Report",
                            data=pdf_bytes,
                            file_name=download_filename,
                            mime="application/pdf",
                            key="download_pdf",
                            use_container_width=True,
                            help="Download a PDF report with analysis results",
                        )
                        st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="card" style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 400px; text-align: center;">
                <div style="color: #6B7280; font-size: 4rem; margin-bottom: 1rem;">🔬</div>
                <div style="font-weight: 600; font-size: 1.2rem; color: #1E3A8A; margin-bottom: 0.5rem;">Ready to Analyze</div>
                <div style="color: #6B7280;">Upload a tablet image and click "Analyze Tablet" to see the results here</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #E5E7EB; color: #6B7280; font-size: 0.8rem;">
        © 2025 Drug Composition Analyzer | Powered by Gemini AI + Tavily
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()