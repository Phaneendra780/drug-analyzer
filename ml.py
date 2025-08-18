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
    page_title="MediScan - Medical Drug Analyzer",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="⚕️"
)

# Clean, minimalistic white theme CSS
st.markdown("""
<style>
    /* Clean white theme */
    .stApp {
        background-color: #ffffff;
        color: #2c3e50;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    }
    
    /* Remove default margins and padding */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Medical header */
    .medical-header {
        background: #ffffff;
        border: 1px solid #e8f2f7;
        border-radius: 12px;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(44, 62, 80, 0.08);
    }
    
    .medical-header h1 {
        color: #2c3e50;
        font-size: 2.2rem;
        font-weight: 600;
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.02em;
    }
    
    .medical-header .subtitle {
        color: #5a6c7d;
        font-size: 1.1rem;
        font-weight: 400;
        margin: 0;
    }
    
    /* Clean card design */
    .med-card {
        background: #ffffff;
        border: 1px solid #e8f2f7;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 1px 4px rgba(44, 62, 80, 0.06);
        transition: box-shadow 0.2s ease;
    }
    
    .med-card:hover {
        box-shadow: 0 4px 12px rgba(44, 62, 80, 0.12);
    }
    
    /* Section headers */
    .section-title {
        color: #2c3e50;
        font-size: 1.2rem;
        font-weight: 600;
        margin: 0 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #e8f2f7;
    }
    
    /* Upload area */
    .upload-area {
        background: #fafbfc;
        border: 2px dashed #cbd5e0;
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
        transition: border-color 0.2s ease;
    }
    
    .upload-area:hover {
        border-color: #4a90a4;
    }
    
    /* Medical result sections */
    .med-result {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 1.25rem;
        margin: 0.75rem 0;
        border-left: 3px solid #4a90a4;
    }
    
    .med-result-header {
        color: #2c3e50;
        font-size: 1.1rem;
        font-weight: 600;
        margin: 0 0 0.75rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .med-result-content {
        color: #4a5568;
        line-height: 1.6;
        font-size: 0.95rem;
    }
    
    /* Drug composition */
    .composition-display {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 1rem;
        font-family: 'Monaco', 'Menlo', monospace;
        font-size: 0.9rem;
        color: #2d3748;
        margin: 0.5rem 0;
    }
    
    /* Brand names */
    .brand-name {
        background: #edf7f9;
        border: 1px solid #bee3f8;
        border-radius: 16px;
        padding: 0.4rem 0.8rem;
        margin: 0.25rem;
        display: inline-block;
        color: #2b6cb0;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    /* Safety indicators */
    .safety-level-safe {
        background: #f0fff4;
        border: 1px solid #9ae6b4;
        border-left: 4px solid #38a169;
        border-radius: 4px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        color: #276749;
    }
    
    .safety-level-caution {
        background: #fffaf0;
        border: 1px solid #fbb042;
        border-left: 4px solid #ed8936;
        border-radius: 4px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        color: #c05621;
    }
    
    .safety-level-warning {
        background: #fff5f5;
        border: 1px solid #fed7d7;
        border-left: 4px solid #e53e3e;
        border-radius: 4px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        color: #c53030;
    }
    
    /* Interaction severity */
    .interaction-high {
        background: #fff5f5;
        border: 1px solid #feb2b2;
        border-radius: 6px;
        padding: 1rem;
        margin: 0.75rem 0;
        color: #c53030;
        border-left: 4px solid #e53e3e;
    }
    
    .interaction-medium {
        background: #fffaf0;
        border: 1px solid #fbd38d;
        border-radius: 6px;
        padding: 1rem;
        margin: 0.75rem 0;
        color: #c05621;
        border-left: 4px solid #ed8936;
    }
    
    .interaction-low {
        background: #f0fff4;
        border: 1px solid #9ae6b4;
        border-radius: 6px;
        padding: 1rem;
        margin: 0.75rem 0;
        color: #276749;
        border-left: 4px solid #38a169;
    }
    
    /* Clean button styling */
    .stButton > button {
        background: #4a90a4;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
        font-weight: 500;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(74, 144, 164, 0.2);
        width: 100%;
    }
    
    .stButton > button:hover {
        background: #3a7a8a;
        box-shadow: 0 4px 8px rgba(74, 144, 164, 0.3);
        transform: translateY(-1px);
    }
    
    /* Medical disclaimer */
    .medical-disclaimer {
        background: #fffbf0;
        border: 1px solid #f6e05e;
        border-radius: 6px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #ecc94b;
        color: #744210;
        font-size: 0.9rem;
    }
    
    /* Text areas and inputs */
    .stTextArea textarea {
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 0.75rem;
        font-size: 0.95rem;
        transition: border-color 0.2s ease;
        background: #ffffff;
    }
    
    .stTextArea textarea:focus {
        border-color: #4a90a4;
        box-shadow: 0 0 0 2px rgba(74, 144, 164, 0.1);
        outline: none;
    }
    
    /* File uploader */
    .stFileUploader {
        border: 1px dashed #cbd5e0;
        border-radius: 6px;
        padding: 1.5rem;
        background: #fafbfc;
    }
    
    /* Remove Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Medical formatting */
    .dosage-info {
        background: #f7fafc;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        font-family: 'Monaco', 'Menlo', monospace;
        font-size: 0.9rem;
    }
    
    .contraindication {
        background: #fff5f5;
        border: 1px solid #fed7d7;
        border-radius: 4px;
        padding: 0.75rem;
        margin: 0.5rem 0;
        color: #c53030;
        font-weight: 500;
    }
    
    /* Clean metrics */
    .medical-metric {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 1rem;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .metric-number {
        font-size: 1.8rem;
        font-weight: 700;
        color: #4a90a4;
        margin-bottom: 0.25rem;
    }
    
    .metric-desc {
        font-size: 0.85rem;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

# Enhanced API Keys
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")

if not TAVILY_API_KEY or not GOOGLE_API_KEY:
    st.error("🔑 Required API keys are missing. Please configure your credentials.")
    st.stop()

MAX_IMAGE_WIDTH = 280

# Enhanced medical-grade system prompt
ENHANCED_SYSTEM_PROMPT = """
You are a board-certified clinical pharmacist and drug information specialist with expertise in pharmaceutical analysis, drug safety, and clinical pharmacology.
Your role is to provide comprehensive, medically accurate drug analysis in a professional clinical format.

Clinical Expertise Areas:
- Pharmaceutical composition analysis and drug identification
- Clinical pharmacology and therapeutic applications
- Drug safety profiling and contraindication assessment
- Drug interaction analysis and clinical significance
- Dosing guidelines and administration protocols
- Patient safety and risk stratification

Always maintain the highest standards of medical accuracy and present information in a clear, professional clinical format.
"""

# Enhanced medical instructions
ENHANCED_INSTRUCTIONS = """
CLINICAL ANALYSIS PROTOCOL:

1. DRUG IDENTIFICATION & COMPOSITION
   - Perform precise pharmaceutical composition analysis from tablet image
   - Identify active pharmaceutical ingredients (APIs) with exact nomenclature
   - Include strength/concentration data when visible

2. COMPREHENSIVE DRUG INFORMATION RETRIEVAL
   - Search authoritative medical databases and sources
   - Verify information across multiple reliable sources
   - Prioritize peer-reviewed medical literature and official drug monographs

3. CLINICAL PRESENTATION FORMAT:
   
   **DRUG IDENTIFICATION**
   Composition: [Exact pharmaceutical composition with strengths]
   
   **BRAND NAMES & FORMULATIONS**
   Available as: [List major brand names and generic formulations]
   
   **THERAPEUTIC INDICATIONS**
   Primary Uses: [Evidence-based therapeutic applications]
   Mechanism of Action: [Brief pharmacological mechanism]
   
   **CLINICAL DOSING & ADMINISTRATION**
   Standard Dosing: [Typical adult dosing regimens]
   Administration: [Timing, food interactions, special instructions]
   Duration: [Typical treatment duration]
   
   **ADVERSE EFFECTS PROFILE**
   Common (>10%): [Most frequent side effects]
   Serious (<1%): [Rare but serious adverse effects]
   
   **CONTRAINDICATIONS & PRECAUTIONS**
   Absolute Contraindications: [When not to use]
   Precautions: [Special patient populations, monitoring requirements]
   
   **DRUG INTERACTIONS**
   Major Interactions: [Clinically significant interactions]
   Monitoring Required: [What to monitor when used with other drugs]
   
   **SPECIAL POPULATIONS**
   Pregnancy: [FDA category and specific guidance]
   Lactation: [Safety during breastfeeding]
   Pediatric: [Use in children if applicable]
   Geriatric: [Special considerations for elderly]
   Renal/Hepatic: [Dose adjustments needed]
   
   **SAFETY CONSIDERATIONS**
   Alcohol: [Specific alcohol interaction guidance]
   Driving: [Effects on psychomotor function]
   
   **COST ANALYSIS**
   Approximate Cost: [Current market pricing for common formulations]

4. CLINICAL ACCURACY REQUIREMENTS:
   - Use precise medical terminology
   - Include FDA-approved indications only
   - Cite evidence-based information
   - Provide specific rather than generic advice
   - Include relevant clinical pearls
   - Maintain professional medical format throughout

5. INFORMATION SOURCES:
   - Prioritize FDA drug labels and monographs
   - Use established medical databases (Drugs.com, WebMD, Mayo Clinic)
   - Reference clinical pharmacology resources
   - Verify pricing through pharmacy databases
"""

# Enhanced drug interaction analysis prompt
ENHANCED_INTERACTION_PROMPT = """
You are a clinical pharmacist specializing in drug interaction analysis and medication therapy management.
Conduct a comprehensive drug-drug interaction assessment with clinical risk stratification.

INTERACTION ANALYSIS PROTOCOL:

1. SYSTEMATIC INTERACTION SCREENING
   - Analyze each medication pair for potential interactions
   - Assess pharmacokinetic and pharmacodynamic interactions
   - Evaluate clinical significance and evidence quality

2. RISK STRATIFICATION FRAMEWORK:
   - CONTRAINDICATED: Never use together (Risk Level: X)
   - MAJOR: Significant risk, requires intervention (Risk Level: D)
   - MODERATE: Monitor closely, may need adjustment (Risk Level: C)
   - MINOR: Minimal clinical impact (Risk Level: B)
   - NO INTERACTION: Safe to use together (Risk Level: A)

3. CLINICAL PRESENTATION FORMAT:

   **INTERACTION SUMMARY**
   Overall Risk Level: [Highest risk level identified]
   
   **DETAILED INTERACTION ANALYSIS**
   [For each significant interaction:]
   
   Drug Pair: [Drug A] + [Drug B]
   Risk Level: [A/B/C/D/X]
   Mechanism: [How the interaction occurs]
   Clinical Effect: [What happens to the patient]
   Management: [Specific clinical recommendations]
   Monitoring: [What to monitor, how often]
   
   **CLINICAL RECOMMENDATIONS**
   Immediate Actions: [What to do now]
   Ongoing Management: [Long-term considerations]
   Alternative Options: [Safer alternatives if needed]
   Patient Counseling: [Key points to discuss with patient]
   
   **EVIDENCE QUALITY**
   [Rate the quality of interaction evidence: High/Moderate/Low]

4. CLINICAL DECISION SUPPORT:
   - Provide actionable clinical recommendations
   - Include specific monitoring parameters
   - Suggest alternative therapies when appropriate
   - Consider patient-specific factors when possible
"""

@st.cache_resource
def get_enhanced_agent():
    """Initialize enhanced medical AI agent."""
    try:
        return Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY),
            system_prompt=ENHANCED_SYSTEM_PROMPT,
            instructions=ENHANCED_INSTRUCTIONS,
            tools=[TavilyTools(api_key=TAVILY_API_KEY)],
            markdown=True,
        )
    except Exception as e:
        st.error(f"❌ Error initializing medical agent: {e}")
        return None

@st.cache_resource
def get_enhanced_interaction_agent():
    """Initialize enhanced drug interaction agent."""
    try:
        return Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY),
            system_prompt=ENHANCED_INTERACTION_PROMPT,
            tools=[TavilyTools(api_key=TAVILY_API_KEY)],
            markdown=True,
        )
    except Exception as e:
        st.error(f"❌ Error initializing interaction agent: {e}")
        return None

def resize_image_for_medical_display(image_file):
    """Resize image with medical documentation standards."""
    try:
        image_file.seek(0)
        img = Image.open(image_file)
        image_file.seek(0)
        
        # Optimize for medical documentation
        aspect_ratio = img.height / img.width
        new_height = int(MAX_IMAGE_WIDTH * aspect_ratio)
        img = img.resize((MAX_IMAGE_WIDTH, new_height), Image.Resampling.LANCZOS)
        
        # Enhance contrast for medical analysis
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)
        
        buf = BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
    except Exception as e:
        st.error(f"📷 Image processing error: {e}")
        return None

def perform_medical_analysis(image_path):
    """Perform comprehensive medical analysis of tablet."""
    agent = get_enhanced_agent()
    if agent is None:
        return None

    try:
        with st.spinner("🔬 Performing clinical pharmaceutical analysis..."):
            response = agent.run(
                """Perform a comprehensive clinical pharmaceutical analysis of this tablet image. 
                Provide detailed drug identification, therapeutic information, safety profile, 
                and clinical guidance in professional medical format. Include specific brand names, 
                precise dosing information, evidence-based uses, and comprehensive safety data.""",
                images=[image_path],
            )
            return response.content.strip()
    except Exception as e:
        st.error(f"🚨 Medical analysis failed: {e}")
        return None

def analyze_clinical_interactions(drug_composition, additional_medications):
    """Perform clinical drug interaction analysis."""
    if not additional_medications.strip():
        return None
    
    interaction_agent = get_enhanced_interaction_agent()
    if interaction_agent is None:
        return None

    try:
        with st.spinner("🔍 Conducting clinical interaction screening..."):
            query = f"""
            CLINICAL INTERACTION SCREENING REQUEST:
            
            PRIMARY MEDICATION: {drug_composition}
            CONCOMITANT MEDICATIONS: {additional_medications}
            
            Perform comprehensive drug-drug interaction analysis with clinical risk assessment.
            Provide evidence-based recommendations and monitoring guidelines.
            """
            response = interaction_agent.run(query)
            return response.content.strip()
    except Exception as e:
        st.error(f"🚨 Interaction analysis failed: {e}")
        return None

def save_medical_file(uploaded_file):
    """Save uploaded medical image file."""
    try:
        file_extension = os.path.splitext(uploaded_file.name)[1]
        with NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            return temp_file.name
    except Exception as e:
        st.error(f"💾 File handling error: {e}")
        return None

def create_medical_pdf(image_data, analysis_results, interaction_analysis=None, additional_meds=None):
    """Generate professional medical PDF report."""
    try:
        buffer = BytesIO()
        pdf = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        
        content = []
        styles = getSampleStyleSheet()
        
        # Professional medical styles
        title_style = ParagraphStyle(
            'MedicalTitle',
            parent=styles['Title'],
            fontSize=16,
            alignment=1,
            spaceAfter=20,
            textColor=colors.Color(0.17, 0.24, 0.31),
            fontName='Helvetica-Bold'
        )
        
        header_style = ParagraphStyle(
            'MedicalHeader',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.Color(0.17, 0.24, 0.31),
            spaceAfter=8,
            fontName='Helvetica-Bold'
        )
        
        body_style = ParagraphStyle(
            'MedicalBody',
            parent=styles['Normal'],
            fontSize=10,
            leading=12,
            textColor=colors.Color(0.29, 0.34, 0.41),
            fontName='Helvetica'
        )
        
        disclaimer_style = ParagraphStyle(
            'MedicalDisclaimer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.red,
            borderWidth=1,
            borderColor=colors.red,
            borderPadding=8,
            backColor=colors.Color(1, 0.98, 0.98),
            alignment=1,
            fontName='Helvetica-Bold'
        )
        
        # Header
        content.append(Paragraph("⚕️ MEDISCAN - CLINICAL PHARMACEUTICAL ANALYSIS REPORT", title_style))
        content.append(Spacer(1, 0.3*inch))
        
        # Medical disclaimer
        content.append(Paragraph(
            "MEDICAL DISCLAIMER: This analysis is for informational purposes only. "
            "Not intended to replace professional medical advice, diagnosis, or treatment. "
            "Always consult qualified healthcare professionals for medical decisions.",
            disclaimer_style
        ))
        content.append(Spacer(1, 0.2*inch))
        
        # Report metadata
        current_datetime = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        content.append(Paragraph(f"Report Generated: {current_datetime}", body_style))
        content.append(Spacer(1, 0.2*inch))
        
        # Add image
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
                content.append(Paragraph("ANALYZED SPECIMEN:", header_style))
                content.append(img_obj)
                content.append(Spacer(1, 0.2*inch))
            except Exception:
                pass
        
        # Analysis results
        content.append(Paragraph("CLINICAL ANALYSIS RESULTS:", header_style))
        
        if analysis_results:
            # Clean and format the medical analysis
            formatted_text = analysis_results.replace('**', '').replace('*', '')
            paragraphs = formatted_text.split('\n')
            
            for paragraph in paragraphs:
                if paragraph.strip():
                    clean_para = paragraph.strip().replace('<', '&lt;').replace('>', '&gt;')
                    content.append(Paragraph(clean_para, body_style))
                    content.append(Spacer(1, 0.1*inch))
        
        # Interaction analysis
        if interaction_analysis and additional_meds:
            content.append(Spacer(1, 0.2*inch))
            content.append(Paragraph("DRUG INTERACTION ANALYSIS:", header_style))
            content.append(Paragraph(f"Concomitant Medications: {additional_meds}", body_style))
            content.append(Spacer(1, 0.1*inch))
            
            formatted_interaction = interaction_analysis.replace('**', '').replace('*', '')
            interaction_paragraphs = formatted_interaction.split('\n')
            
            for paragraph in interaction_paragraphs:
                if paragraph.strip():
                    clean_para = paragraph.strip().replace('<', '&lt;').replace('>', '&gt;')
                    content.append(Paragraph(clean_para, body_style))
                    content.append(Spacer(1, 0.1*inch))
        
        # Footer
        content.append(Spacer(1, 0.4*inch))
        content.append(Paragraph(
            "This report was generated using advanced AI pharmaceutical analysis. "
            "Clinical correlation and professional medical judgment are essential.",
            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
        ))
        
        pdf.build(content)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"📄 PDF generation error: {e}")
        return None

def format_medical_section(title, content, icon=""):
    """Format medical information in professional clinical layout."""
    if not content or content.strip() == "":
        return
    
    st.markdown(f'<div class="med-result">', unsafe_allow_html=True)
    st.markdown(f'<div class="med-result-header">{icon} {title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="med-result-content">', unsafe_allow_html=True)
    
    # Special formatting for different medical sections
    if title == "Drug Identification" or title == "Composition":
        st.markdown(f'<div class="composition-display">{content}</div>', unsafe_allow_html=True)
    elif title == "Brand Names & Formulations":
        format_brand_names(content)
    elif title == "Contraindications & Precautions":
        st.markdown(f'<div class="contraindication">{content}</div>', unsafe_allow_html=True)
    elif title == "Clinical Dosing & Administration":
        st.markdown(f'<div class="dosage-info">{content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(content)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def format_brand_names(content):
    """Format brand names in clean medical style."""
    if not content:
        return
    
    # Parse brand names
    brands = []
    for delimiter in ['\n', ',', ';', '•', '-', '|']:
        if delimiter in content:
            brands = [name.strip() for name in content.split(delimiter) if name.strip()]
            break
    
    if not brands:
        brands = [content.strip()]
    
    # Display brands
    brand_html = ""
    for brand in brands:
        if brand:
            brand_html += f'<span class="brand-name">{brand}</span>'
    
    if brand_html:
        st.markdown(brand_html, unsafe_allow_html=True)

def format_safety_assessment(content, safety_category):
    """Format safety information with clinical risk levels."""
    if not content:
        return
    
    # Determine safety level
    content_lower = content.lower()
    
    if any(term in content_lower for term in ["safe", "no significant", "minimal risk", "compatible"]):
        css_class = "safety-level-safe"
        icon = "✅"
    elif any(term in content_lower for term in ["caution", "monitor", "consider", "may"]):
        css_class = "safety-level-caution"
        icon = "⚠️"
    elif any(term in content_lower for term in ["avoid", "contraindicated", "dangerous", "severe"]):
        css_class = "safety-level-warning"
        icon = "❌"
    else:
        css_class = "safety-level-safe"
        icon = "ℹ️"
    
    st.markdown(f'<div class="{css_class}">{icon} <strong>{safety_category}:</strong> {content}</div>', unsafe_allow_html=True)

def format_interaction_results(interaction_text):
    """Format drug interaction results with clinical severity indicators."""
    if not interaction_text:
        return
    
    # Determine interaction severity
    text_lower = interaction_text.lower()
    
    if any(term in text_lower for term in ["contraindicated", "never", "severe", "major"]):
        css_class = "interaction-high"
        severity = "HIGH RISK INTERACTION"
        icon = "🚨"
    elif any(term in text_lower for term in ["moderate", "significant", "monitor"]):
        css_class = "interaction-medium"
        severity = "MODERATE INTERACTION"
        icon = "⚠️"
    elif any(term in text_lower for term in ["minor", "low", "minimal"]):
        css_class = "interaction-low"
        severity = "LOW RISK INTERACTION"
        icon = "ℹ️"
    else:
        css_class = "interaction-low"
        severity = "INTERACTION ASSESSMENT"
        icon = "🔍"
    
    st.markdown(f'<div class="{css_class}"><strong>{icon} {severity}</strong></div>', unsafe_allow_html=True)

def main():
    # Session state initialization
    session_vars = [
        'analyze_clicked', 'analysis_results', 'original_image', 
        'drug_composition', 'interaction_analysis', 'additional_medications'
    ]
    
    for var in session_vars:
        if var not in st.session_state:
            st.session_state[var] = None if var != 'analyze_clicked' else False

    # Medical header
    st.markdown("""
    <div class="medical-header">
        <h1>⚕️ MediScan</h1>
        <div class="subtitle">Clinical Pharmaceutical Analysis & Drug Safety Platform</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Medical disclaimer
    st.markdown("""
    <div class="medical-disclaimer">
        <strong>⚠️ CLINICAL DISCLAIMER:</strong> This analysis is provided for educational and informational purposes only. 
        This tool does not replace professional medical consultation, diagnosis, or treatment recommendations. 
        Always consult with licensed healthcare professionals for medical advice and medication decisions.
    </div>
    """, unsafe_allow_html=True)
    
    # Main interface layout
    col1, col2 = st.columns([1, 1.2], gap="large")
    
    with col1:
        # Image upload section
        st.markdown('<div class="med-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📤 Pharmaceutical Image Upload</div>', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Upload tablet/capsule image for analysis",
            type=["jpg", "jpeg", "png", "webp"],
            help="Provide a clear, well-lit image of the tablet or its packaging for optimal analysis"
        )
        
        if uploaded_file:
            # Display image with medical documentation quality
            resized_image = resize_image_for_medical_display(uploaded_file)
            if resized_image:
                st.image(resized_image, caption="Pharmaceutical Specimen", width=MAX_IMAGE_WIDTH)
                
                # File information
                file_size = len(uploaded_file.getvalue()) / 1024
                st.info(f"📎 **{uploaded_file.name}** | Size: {file_size:.1f} KB")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Drug interaction screening section
        st.markdown('<div class="med-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🔍 Drug Interaction Screening</div>', unsafe_allow_html=True)
        
        additional_meds = st.text_area(
            "Current Medication Regimen:",
            placeholder="Enter all current medications with doses:\ne.g., Metformin 500mg BID, Lisinopril 10mg QD, Aspirin 81mg QD",
            help="Include prescription drugs, OTC medications, and supplements with exact dosages and frequencies",
            key="med_interaction_input",
            height=120
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Analysis button
        if uploaded_file:
            if st.button("🔬 Perform Clinical Analysis", use_container_width=True):
                st.session_state.analyze_clicked = True
                st.session_state.additional_medications = additional_meds
                
                temp_path = save_medical_file(uploaded_file)
                if temp_path:
                    try:
                        # Perform medical analysis
                        medical_analysis = perform_medical_analysis(temp_path)
                        
                        if medical_analysis:
                            st.session_state.analysis_results = medical_analysis
                            st.session_state.original_image = uploaded_file.getvalue()
                            
                            # Extract composition for interaction analysis
                            comp_patterns = [
                                r"(?:Composition|Drug Identification):\s*(.*?)(?=\n\n|\n[A-Z]|$)",
                                r"\*\*(?:Composition|Drug Identification)\*\*\s*(.*?)(?=\n\n|\*\*|$)"
                            ]
                            
                            for pattern in comp_patterns:
                                match = re.search(pattern, medical_analysis, re.DOTALL | re.IGNORECASE)
                                if match:
                                    st.session_state.drug_composition = match.group(1).strip()
                                    break
                            
                            # Perform interaction analysis
                            if additional_meds.strip():
                                interaction_result = analyze_clinical_interactions(
                                    st.session_state.drug_composition or "Primary medication",
                                    additional_meds
                                )
                                st.session_state.interaction_analysis = interaction_result
                            
                            st.success("✅ Clinical analysis completed successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Analysis failed. Please ensure image is clear and try again.")
                        
                    except Exception as e:
                        st.error(f"🚨 Clinical analysis error: {e}")
                    finally:
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
    
    with col2:
        st.markdown('<div class="section-title">📋 Clinical Analysis Results</div>', unsafe_allow_html=True)
        
        if st.session_state.analysis_results:
            # Parse medical analysis into sections
            medical_sections = [
                ("Drug Identification", "🧬"),
                ("Composition", "🔬"),
                ("Brand Names & Formulations", "💊"),
                ("Therapeutic Indications", "🎯"),
                ("Clinical Dosing & Administration", "📋"),
                ("Adverse Effects Profile", "⚠️"),
                ("Contraindications & Precautions", "🚫"),
                ("Drug Interactions", "🔄"),
                ("Special Populations", "👥"),
                ("Safety Considerations", "🛡️"),
                ("Cost Analysis", "💰")
            ]
            
            analysis_text = st.session_state.analysis_results
            
            # Display each medical section
            for section_name, icon in medical_sections:
                # Multiple pattern matching for flexible parsing
                patterns = [
                    rf"\*\*{re.escape(section_name)}\*\*(.*?)(?=\*\*[\w\s&]+\*\*|$)",
                    rf"{re.escape(section_name)}:\s*(.*?)(?=\n[A-Z][\w\s]+:|$)",
                    rf"\*{re.escape(section_name)}:\*(.*?)(?=\*[\w\s]+:\*|$)"
                ]
                
                content = None
                for pattern in patterns:
                    match = re.search(pattern, analysis_text, re.DOTALL | re.IGNORECASE)
                    if match:
                        content = match.group(1).strip()
                        break
                
                if content and len(content) > 5:  # Only show sections with meaningful content
                    format_medical_section(section_name, content, icon)
            
            # Drug interaction analysis display
            if st.session_state.interaction_analysis:
                st.markdown('<div class="med-result">', unsafe_allow_html=True)
                st.markdown('<div class="med-result-header">🔍 Clinical Interaction Assessment</div>', unsafe_allow_html=True)
                st.markdown('<div class="med-result-content">', unsafe_allow_html=True)
                
                if st.session_state.additional_medications:
                    st.markdown(f"**Concomitant Medications:** {st.session_state.additional_medications}")
                    st.markdown("---")
                
                # Display interaction severity
                format_interaction_results(st.session_state.interaction_analysis)
                
                # Display detailed analysis
                st.markdown(st.session_state.interaction_analysis)
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # PDF report generation
            if st.session_state.original_image:
                st.markdown('<div class="med-card">', unsafe_allow_html=True)
                st.markdown('<div class="section-title">📄 Medical Report</div>', unsafe_allow_html=True)
                
                pdf_data = create_medical_pdf(
                    st.session_state.original_image,
                    st.session_state.analysis_results,
                    st.session_state.interaction_analysis,
                    st.session_state.additional_medications
                )
                
                if pdf_data:
                    report_filename = f"clinical_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                    st.download_button(
                        label="📥 Download Clinical Report",
                        data=pdf_data,
                        file_name=report_filename,
                        mime="application/pdf",
                        help="Download comprehensive clinical analysis report",
                        use_container_width=True
                    )
                
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            # Instructions when no analysis available
            st.markdown("""
            <div class="med-result">
                <div class="med-result-header">📋 Clinical Analysis Protocol</div>
                <div class="med-result-content">
                    Upload a pharmaceutical image to begin comprehensive clinical analysis.
                    <br><br>
                    <strong>Analysis Includes:</strong>
                    <br>
                    🧬 Precise drug identification and composition<br>
                    💊 Available formulations and brand names<br>
                    🎯 Evidence-based therapeutic indications<br>
                    📋 Clinical dosing and administration guidelines<br>
                    ⚠️ Comprehensive adverse effects profile<br>
                    🚫 Contraindications and precautions<br>
                    🔄 Drug-drug interaction assessment<br>
                    👥 Special population considerations<br>
                    🛡️ Safety profile and monitoring requirements<br>
                    💰 Current market cost analysis
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Clinical guidelines section
    if st.session_state.analysis_results:
        st.markdown("---")
        st.markdown('<div class="section-title">🏥 Clinical Practice Guidelines</div>', unsafe_allow_html=True)
        
        guideline_col1, guideline_col2 = st.columns(2)
        
        with guideline_col1:
            st.markdown("""
            <div class="med-card">
                <div class="section-title">🍺 Alcohol Interaction Protocol</div>
                <div class="med-result-content">
                    • Review specific alcohol interaction data above<br>
                    • Consider hepatic metabolism pathways<br>
                    • Assess CNS depression risk<br>
                    • Evaluate patient alcohol use history<br>
                    • Provide clear patient counseling
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="med-card">
                <div class="section-title">🤱 Reproductive Health Considerations</div>
                <div class="med-result-content">
                    • Pregnancy category and trimester-specific risks<br>
                    • Lactation safety and milk transfer data<br>
                    • Contraceptive interactions if applicable<br>
                    • Teratogenic potential assessment<br>
                    • Alternative therapy options for pregnancy
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with guideline_col2:
            st.markdown("""
            <div class="med-card">
                <div class="section-title">🚗 Psychomotor Assessment</div>
                <div class="med-result-content">
                    • Evaluate sedation and cognitive effects<br>
                    • Assess reaction time impairment<br>
                    • Consider occupational safety implications<br>
                    • Review dose-dependent effects<br>
                    • Provide driving safety counseling
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="med-card">
                <div class="section-title">💊 Medication Management</div>
                <div class="med-result-content">
                    • Maintain comprehensive medication list<br>
                    • Include all OTC and herbal supplements<br>
                    • Regular medication reconciliation<br>
                    • Monitor for therapeutic duplications<br>
                    • Assess adherence and compliance
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Professional metrics (if analysis completed)
    if st.session_state.analysis_results:
        st.markdown("---")
        st.markdown('<div class="section-title">📊 Analysis Summary</div>', unsafe_allow_html=True)
        
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            st.markdown("""
            <div class="medical-metric">
                <div class="metric-number">✓</div>
                <div class="metric-desc">Drug Identified</div>
            </div>
            """, unsafe_allow_html=True)
        
        with metric_col2:
            st.markdown("""
            <div class="medical-metric">
                <div class="metric-number">✓</div>
                <div class="metric-desc">Safety Assessed</div>
            </div>
            """, unsafe_allow_html=True)
        
        with metric_col3:
            interaction_status = "✓" if st.session_state.interaction_analysis else "—"
            st.markdown(f"""
            <div class="medical-metric">
                <div class="metric-number">{interaction_status}</div>
                <div class="metric-desc">Interactions Checked</div>
            </div>
            """, unsafe_allow_html=True)
        
        with metric_col4:
            st.markdown("""
            <div class="medical-metric">
                <div class="metric-number">✓</div>
                <div class="metric-desc">Report Ready</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Professional footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem; color: #718096; font-size: 0.85rem; background: #f8fafc; border-radius: 6px; margin-top: 2rem;">
        <div style="margin-bottom: 0.5rem;">
            <strong>⚕️ MediScan Clinical Platform</strong>
        </div>
        <div>
            Advanced AI-Powered Pharmaceutical Analysis | Professional Medical Information System
        </div>
        <div style="margin-top: 0.5rem; font-size: 0.8rem;">
            <em>Enhancing clinical decision-making through intelligent drug analysis</em>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
