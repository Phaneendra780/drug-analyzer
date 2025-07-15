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

# Set page configuration with white theme
st.set_page_config(
    page_title="MediScan - Drug Composition Analyzer",
    layout="centered",
    initial_sidebar_state="collapsed",
    page_icon="💊"
)

# Apply custom CSS for white theme and better contrast
st.markdown("""
    <style>
        body {
            color: #333333;
            background-color: #FFFFFF;
        }
        .stApp {
            background-color: #FFFFFF;
            max-width: 900px;
            padding: 2rem;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border-radius: 4px;
            padding: 0.5rem 1rem;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
        }
        .stFileUploader>div>div {
            border: 1px solid #CCCCCC;
            background-color: #FFFFFF;
        }
        .stAlert {
            border-left: 4px solid #FF6B6B;
        }
        .stSuccess {
            border-left: 4px solid #4CAF50;
        }
        .stWarning {
            border-left: 4px solid #FFC107;
        }
        .stInfo {
            border-left: 4px solid #2196F3;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #2E7D32;
        }
        hr {
            border-color: #EEEEEE;
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
    """Create a formal PDF report of the analysis."""
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        
        content = []
        
        # Custom styles for formal report
        styles = getSampleStyleSheet()
        
        # Title style
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Title'],
            fontSize=16,
            alignment=1,
            spaceAfter=12,
            textColor=colors.HexColor("#2E7D32"),
            fontName='Helvetica-Bold'
        )
        
        # Header style
        header_style = ParagraphStyle(
            'Header',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor("#2E7D32"),
            spaceAfter=6,
            fontName='Helvetica-Bold'
        )
        
        # Normal text style
        normal_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=10,
            leading=12,
            spaceAfter=6,
            fontName='Helvetica'
        )
        
        # Disclaimer style
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.red,
            borderWidth=1,
            borderColor=colors.red,
            borderPadding=5,
            backColor=colors.HexColor("#FFEBEE"),
            alignment=1,
            fontName='Helvetica-Oblique'
        )
        
        # Add title
        content.append(Paragraph("MediScan - Pharmaceutical Analysis Report", title_style))
        content.append(Spacer(1, 12))
        
        # Add date
        current_datetime = datetime.now().strftime("%B %d, %Y at %H:%M")
        content.append(Paragraph(f"Report generated on: {current_datetime}", normal_style))
        content.append(Spacer(1, 12))
        
        # Add disclaimer
        content.append(Paragraph(
            "Important: This report is for informational purposes only and should not replace professional medical advice. "
            "Always consult with a qualified healthcare provider regarding medications.",
            disclaimer_style
        ))
        content.append(Spacer(1, 12))
        
        # Add image if available
        if image_data:
            try:
                img_temp = BytesIO(image_data)
                img = Image.open(img_temp)
                img_width, img_height = img.size
                aspect = img_height / float(img_width)
                display_width = 3 * inch
                display_height = display_width * aspect
                
                img_temp.seek(0)
                img_obj = ReportLabImage(img_temp, width=display_width, height=display_height)
                content.append(Paragraph("Analyzed Medication Image:", header_style))
                content.append(img_obj)
                content.append(Spacer(1, 12))
            except Exception as img_error:
                st.warning(f"Could not add image to PDF: {img_error}")
        
        # Analysis results
        content.append(Paragraph("Pharmaceutical Analysis Findings:", header_style))
        
        # Format the analysis results for PDF
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
                    
                    content.append(Spacer(1, 6))
        
        # Drug interaction analysis
        if interaction_analysis and additional_meds:
            content.append(Spacer(1, 12))
            content.append(Paragraph("Drug Interaction Analysis:", header_style))
            content.append(Paragraph(f"<b>Concurrent Medications:</b> {additional_meds}", normal_style))
            content.append(Spacer(1, 6))
            
            clean_interaction = interaction_analysis.replace('<', '&lt;').replace('>', '&gt;')
            content.append(Paragraph(clean_interaction, normal_style))
        
        # Build PDF
        doc.build(content)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"📄 Error creating PDF: {e}")
        return None

def display_analysis_results(analysis_text):
    """Display analysis results in a structured format with proper contrast."""
    if not analysis_text:
        return
    
    sections = [
        ("Composition", "🧬"),
        ("Available Tablet Names", "💊"),
        ("Uses", "🎯"),
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
        pattern = rf"\*{re.escape(section_name)}:\*(.*?)(?=\*(?:{'|'.join(re.escape(s[0]) for s in sections)}):\*|$)"
        match = re.search(pattern, analysis_text, re.DOTALL | re.IGNORECASE)
        
        if match:
            content = match.group(1).strip()
            
            with st.container():
                st.markdown(f"<h3 style='color:#2E7D32;'>{icon} {section_name}</h3>", unsafe_allow_html=True)
                
                if section_name == "Available Tablet Names":
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
                            st.markdown(f"<div style='margin-left: 1rem;'>• {name}</div>", unsafe_allow_html=True)
                
                elif section_name == "Uses":
                    if '\n' in content or ',' in content:
                        uses_list = content.replace('\n', ', ').split(',')
                        for use in uses_list:
                            if use.strip():
                                st.markdown(f"<div style='margin-left: 1rem;'>• {use.strip()}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div>{content}</div>", unsafe_allow_html=True)
                
                elif section_name == "Side Effects":
                    if '\n' in content or ',' in content:
                        effects_list = content.replace('\n', ', ').split(',')
                        for effect in effects_list:
                            if effect.strip():
                                st.markdown(f"<div style='margin-left: 1rem; color: #D32F2F;'>⚠️ {effect.strip()}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='color: #D32F2F;'>⚠️ {content}</div>", unsafe_allow_html=True)
                
                elif "Safety" in section_name:
                    if "safe" in content.lower() or "no interaction" in content.lower():
                        st.markdown(f"<div style='color: #388E3C;'>✅ {content}</div>", unsafe_allow_html=True)
                    elif "avoid" in content.lower() or "contraindicated" in content.lower() or "not recommended" in content.lower():
                        st.markdown(f"<div style='color: #D32F2F;'>❌ {content}</div>", unsafe_allow_html=True)
                    elif "caution" in content.lower() or "monitor" in content.lower() or "consult" in content.lower():
                        st.markdown(f"<div style='color: #FFA000;'>⚠️ {content}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='color: #1976D2;'>ℹ️ {content}</div>", unsafe_allow_html=True)
                
                else:
                    st.markdown(f"<div>{content}</div>", unsafe_allow_html=True)
                
                st.markdown("<hr style='border: 1px solid #EEEEEE;'>", unsafe_allow_html=True)

def display_interaction_analysis(interaction_text):
    """Display interaction analysis with appropriate styling."""
    if not interaction_text:
        return
    
    with st.container():
        st.markdown("<h3 style='color:#2E7D32;'>🔍 Drug Interaction Analysis</h3>", unsafe_allow_html=True)
        
        # Determine interaction severity
        if "severe" in interaction_text.lower() or "major" in interaction_text.lower():
            st.markdown("<div style='background-color: #FFEBEE; padding: 1rem; border-left: 4px solid #D32F2F; margin-bottom: 1rem;'>"
                       "🚨 <strong>SEVERE/MAJOR INTERACTION DETECTED</strong></div>", unsafe_allow_html=True)
        elif "moderate" in interaction_text.lower():
            st.markdown("<div style='background-color: #FFF8E1; padding: 1rem; border-left: 4px solid #FFA000; margin-bottom: 1rem;'>"
                       "⚠️ <strong>MODERATE INTERACTION</strong></div>", unsafe_allow_html=True)
        elif "minor" in interaction_text.lower():
            st.markdown("<div style='background-color: #E8F5E9; padding: 1rem; border-left: 4px solid #388E3C; margin-bottom: 1rem;'>"
                       "ℹ️ <strong>MINOR INTERACTION</strong></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='background-color: #E3F2FD; padding: 1rem; border-left: 4px solid #1976D2; margin-bottom: 1rem;'>"
                       "✅ <strong>LOW INTERACTION RISK</strong></div>", unsafe_allow_html=True)
        
        st.markdown(f"<div style='line-height: 1.6;'>{interaction_text}</div>", unsafe_allow_html=True)

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

    # Header with improved contrast
    st.markdown("<h1 style='color:#2E7D32; text-align: center;'>💊 MediScan</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='color:#2E7D32; text-align: center; margin-top: -0.5rem;'>Pharmaceutical Analysis System</h2>", unsafe_allow_html=True)
    
    # Medical disclaimer
    st.markdown("""
        <div style='background-color: #FFEBEE; padding: 1rem; border-left: 4px solid #D32F2F; margin-bottom: 2rem;'>
            <strong>⚠️ MEDICAL DISCLAIMER:</strong> The information provided by MediScan is for educational purposes only 
            and should not replace professional medical advice. Always consult with a qualified healthcare provider 
            regarding medications and treatment.
        </div>
    """, unsafe_allow_html=True)
    
    # Main content in single column layout
    st.header("📤 Medication Image Upload")
    
    uploaded_file = st.file_uploader(
        "Upload a clear image of the medication (tablet, capsule, or packaging)",
        type=["jpg", "jpeg", "png", "webp"],
        help="For best results, upload a high-quality image with good lighting"
    )
    
    if uploaded_file:
        # Display uploaded image
        resized_image = resize_image_for_display(uploaded_file)
        if resized_image:
            st.image(resized_image, caption="Uploaded Medication Image", width=MAX_IMAGE_WIDTH)
            
            # Display file info
            file_size = len(uploaded_file.getvalue()) / 1024
            st.success(f"📎 **{uploaded_file.name}** • {file_size:.1f} KB")
    
    # Additional medications input
    st.header("💊 Medication Safety Check")
    additional_meds = st.text_area(
        "List any other medications you're currently taking (for interaction check):",
        placeholder="Example: Aspirin 81mg daily, Lisinopril 10mg once daily, Metformin 500mg twice daily",
        help="Include medication names, dosages, and frequency for comprehensive interaction analysis",
        height=100
    )
    
    # Analyze button
    if uploaded_file:
        if st.button("🔬 Analyze Medication & Check Safety", use_container_width=True, type="primary"):
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
                        
                        st.success("✅ Analysis completed successfully!")
                    
                    else:
                        st.error("❌ Analysis failed. Please try with a clearer image.")
                
                except Exception as e:
                    st.error(f"🚨 Analysis failed: {e}")
                finally:
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
    
    # Display results if available
    if st.session_state.analysis_results:
        st.header("📋 Analysis Results")
        display_analysis_results(st.session_state.analysis_results)
        
        # Display drug interaction analysis if available
        if st.session_state.interaction_analysis:
            st.markdown(f"<div style='margin-bottom: 1rem;'><strong>Additional Medications:</strong> {st.session_state.additional_medications}</div>", unsafe_allow_html=True)
            display_interaction_analysis(st.session_state.interaction_analysis)
        
        # PDF download section
        if st.session_state.original_image:
            st.header("📄 Download Formal Report")
            
            pdf_bytes = create_pdf(
                st.session_state.original_image,
                st.session_state.analysis_results,
                st.session_state.interaction_analysis,
                st.session_state.additional_medications
            )
            
            if pdf_bytes:
                download_filename = f"MediScan_Report_{datetime.now().strftime('%Y%m%d')}.pdf"
                st.download_button(
                    label="📥 Download Professional PDF Report",
                    data=pdf_bytes,
                    file_name=download_filename,
                    mime="application/pdf",
                    help="Download a formal PDF report suitable for sharing with healthcare providers",
                    use_container_width=True,
                    type="primary"
                )
    else:
        st.info("""
        **How to use MediScan:**
        1. Upload an image of your medication (tablet, capsule, or packaging)
        2. Optionally list other medications you're taking
        3. Click "Analyze Medication & Check Safety"
        
        **You'll receive:**
        - Comprehensive medication identification
        - Usage instructions and safety information
        - Potential drug interaction analysis
        - Professional PDF report
        """)
    
    # Safety guidelines in expander
    with st.expander("🛡️ Important Medication Safety Guidelines", expanded=False):
        st.markdown("""
        <div style='line-height: 1.6;'>
            <h4 style='color:#2E7D32;'>General Safety Principles</h4>
            <ul>
                <li>Always take medications exactly as prescribed by your healthcare provider</li>
                <li>Keep an updated list of all medications, including over-the-counter drugs and supplements</li>
                <li>Store medications properly according to package instructions</li>
                <li>Never share prescription medications with others</li>
            </ul>
            
            <h4 style='color:#2E7D32;'>When to Seek Medical Advice</h4>
            <ul>
                <li>If you experience unexpected side effects</li>
                <li>Before starting or stopping any medication</li>
                <li>If you're pregnant, planning pregnancy, or breastfeeding</li>
                <li>When considering alcohol consumption with medications</li>
            </ul>
            
            <h4 style='color:#2E7D32;'>Emergency Situations</h4>
            <ul>
                <li>In case of suspected overdose, contact poison control immediately</li>
                <li>For severe allergic reactions (difficulty breathing, swelling), seek emergency care</li>
                <li>If you experience chest pain, severe dizziness, or loss of consciousness</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
