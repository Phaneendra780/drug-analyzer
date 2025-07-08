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
                    st.markdown(f"🏷️ **{name}**")
    else:
        st.write(tablet_names[0] if tablet_names else tablet_names_text)

def display_safety_info(content, safety_type):
    """Display safety information with appropriate styling."""
    if not content:
        return
    
    # Color coding for different safety levels
    if "safe" in content.lower() or "no interaction" in content.lower():
        st.success(f"✅ {content}")
    elif "avoid" in content.lower() or "contraindicated" in content.lower() or "not recommended" in content.lower():
        st.error(f"❌ {content}")
    elif "caution" in content.lower() or "monitor" in content.lower() or "consult" in content.lower():
        st.warning(f"⚠️ {content}")
    else:
        st.info(f"ℹ️ {content}")

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
    st.title("🏥 MediScan - Comprehensive Drug Analyzer")
    
    # Medical disclaimer
    st.warning("""
    ⚠️ **MEDICAL DISCLAIMER**
    
    The information provided by MediScan is for educational and informational purposes only and is not intended to replace professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition, medication, or drug interactions.
    """)
    
    # Main content in two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📤 Upload Tablet Image")
        
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
                st.info(f"**{uploaded_file.name}** • {file_size:.1f} KB")
        
        # Additional medications input
        st.subheader("💊 Additional Medications (Optional)")
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
    
    with col2:
        st.subheader("📊 Analysis Results")
        
        # Display results if available
        if st.session_state.analysis_results:
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
                        st.write(content)
                    
                    st.markdown("---")
            
            # Display drug interaction analysis if available
            if st.session_state.interaction_analysis:
                st.markdown("### 💊 Drug Interaction Analysis")
                st.markdown(f"**Additional Medications:** {st.session_state.additional_medications}")
                
                # Parse interaction analysis for severity levels
                interaction_text = st.session_state.interaction_analysis
                
                if "severe" in interaction_text.lower() or "major" in interaction_text.lower():
                    st.error("🚨 **SEVERE/MAJOR INTERACTION DETECTED**")
                elif "moderate" in interaction_text.lower():
                    st.warning("⚠️ **MODERATE INTERACTION**")
                elif "minor" in interaction_text.lower():
                    st.info("ℹ️ **MINOR INTERACTION**")
                else:
                    st.success("✅ **LOW INTERACTION RISK**")
                
                st.write(interaction_text)
                st.markdown("---")
            
            # PDF download section
            if st.session_state.original_image:
                st.subheader("📄 Download Comprehensive Report")
                
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
        else:
            st.info("Upload a tablet image and click 'Analyze Tablet & Check Safety' to see comprehensive results here.")
    
    # Additional Safety Information Section
    if st.session_state.analysis_results:
        st.markdown("---")
        st.subheader("🛡️ Important Safety Reminders")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🍺 Alcohol Interaction:**
            - Always check the specific alcohol interaction information above
            - Some medications can cause severe reactions with alcohol
            - Consult your doctor about alcohol consumption while on medication
            """)
            
            st.markdown("""
            **🤱 Pregnancy & Breastfeeding:**
            - Medication safety varies by trimester
            - Many drugs can pass through breast milk
            - Always inform your healthcare provider if you're pregnant or breastfeeding
            """)
        
        with col2:
            st.markdown("""
            **🚗 Driving Safety:**
            - Some medications can cause drowsiness or dizziness
            - Check the driving safety information above
            - Avoid driving if you feel impaired
            """)
            
            st.markdown("""
            **💊 Drug Interactions:**
            - Always provide a complete list of medications to your doctor
            - Include over-the-counter drugs and supplements
            - Check for interactions before starting new medications
            """)
    
    # Footer
    st.markdown("---")
    st.markdown("© 2025 MediScan - Comprehensive Drug Analyzer | Powered by Gemini AI + Tavily")

if __name__ == "__main__":
    main()
