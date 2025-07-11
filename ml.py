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
    page_title="MediScan - Indian Drug Analyzer",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🏥"
)

# Custom CSS for better UI and visibility
st.markdown("""
<style>
    .main {
        background-color: #ffffff;
        padding: 20px;
    }
    
    .stApp {
        background-color: #ffffff;
    }
    
    .section-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 20px 0 10px 0;
        font-size: 20px;
        font-weight: bold;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .info-card {
        background-color: #f8f9fa;
        border: 2px solid #e9ecef;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .composition-card {
        background-color: #e8f5e8;
        border: 2px solid #28a745;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
    }
    
    .safety-card {
        background-color: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
    }
    
    .interaction-card {
        background-color: #f8d7da;
        border: 2px solid #dc3545;
        border-radius: 10px;
        padding: 20px;
        margin: 15px 0;
    }
    
    .tablet-names-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 15px;
        margin: 15px 0;
    }
    
    .tablet-name-item {
        background-color: #e3f2fd;
        border: 1px solid #2196f3;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
        font-weight: bold;
        color: #1976d2;
    }
    
    .side-effects-list {
        background-color: #ffebee;
        border: 1px solid #f44336;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .cost-info {
        background-color: #e8f5e8;
        border: 1px solid #4caf50;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        text-align: center;
        font-size: 18px;
        font-weight: bold;
        color: #2e7d32;
    }
    
    .usage-instructions {
        background-color: #e3f2fd;
        border: 1px solid #2196f3;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    .disclaimer-box {
        background-color: #ffebee;
        border: 2px solid #f44336;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
        text-align: center;
        font-weight: bold;
        color: #c62828;
    }
    
    .upload-section {
        background-color: #f5f5f5;
        border: 2px dashed #cccccc;
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        margin: 20px 0;
    }
    
    .analyze-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 15px 30px;
        border-radius: 10px;
        font-size: 18px;
        font-weight: bold;
        cursor: pointer;
        width: 100%;
        margin: 20px 0;
    }
    
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .text-content {
        color: #333333;
        line-height: 1.6;
        font-size: 16px;
    }
    
    .section-title {
        color: #2c3e50;
        font-size: 24px;
        font-weight: bold;
        margin: 20px 0 10px 0;
        border-bottom: 3px solid #3498db;
        padding-bottom: 10px;
    }
    
    .subsection-title {
        color: #34495e;
        font-size: 18px;
        font-weight: bold;
        margin: 15px 0 5px 0;
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
You are an expert pharmaceutical analyst specializing in the Indian drug market with comprehensive knowledge of drug safety, interactions, and Indian pharmaceutical brands.
Your role is to analyze a tablet's composition from an image, identify its ingredients, and provide detailed insights specifically relevant to the Indian market.

Focus on Indian pharmaceutical companies, pricing in Indian Rupees, and medications commonly available in India through pharmacies and online platforms.
"""

INSTRUCTIONS = """
- Extract the drug composition from the tablet image accurately.
- Provide comprehensive information specifically for the Indian market including:
  *Composition:* <exact active ingredients and their quantities>
  *Indian Brand Names:* <list of popular Indian brand names containing this composition - include companies like Cipla, Sun Pharma, Dr. Reddy's, Lupin, etc.>
  *Medical Uses:* <detailed therapeutic uses and indications>
  *Dosage Instructions:* <how to take, timing, with/without food, duration>
  *Side Effects:* <common and serious side effects to watch for>
  *Indian Market Price:* <approximate price range in Indian Rupees from Indian pharmacies>
  *Alcohol Safety:* <specific advice about alcohol consumption>
  *Pregnancy Safety:* <safety category and recommendations>
  *Breastfeeding Safety:* <safety for nursing mothers>
  *Driving Safety:* <effects on driving ability>
  *Storage Instructions:* <how to store the medication properly>
  *Precautions:* <important warnings and contraindications>
  
Ensure all information is accurate, up-to-date, and relevant to Indian patients and healthcare practices.
"""

DRUG_INTERACTION_PROMPT = """
You are a pharmaceutical expert specializing in drug interactions with focus on medications commonly used in India.
Analyze potential interactions between the identified drug and additional medications, considering Indian medical practices and commonly prescribed combinations.

Provide detailed interaction analysis including:
- Severity level: None, Minor, Moderate, Major, Severe
- Specific interaction mechanisms
- Clinical significance in Indian healthcare context
- Recommended actions for Indian patients
- Alternative suggestions from Indian pharmaceutical market
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
        with st.spinner("🔬 Analyzing tablet image and retrieving Indian market information..."):
            response = agent.run(
                "Extract the drug composition from this tablet image and provide comprehensive information relevant to the Indian pharmaceutical market including Indian brand names, pricing in INR, and safety information.",
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
        with st.spinner("🔍 Analyzing drug interactions for Indian market..."):
            query = f"""
            Analyze potential drug interactions between:
            Primary Drug: {drug_composition}
            Additional Medications: {additional_medications}
            
            Focus on Indian pharmaceutical market and provide detailed interaction analysis with severity levels and safety recommendations.
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

def display_tablet_names(tablet_names_text):
    """Display Indian brand names in a grid format."""
    if not tablet_names_text:
        return
    
    # Parse tablet names
    tablet_names = []
    for delimiter in ['\n', ',', ';', '•', '-']:
        if delimiter in tablet_names_text:
            names = tablet_names_text.split(delimiter)
            tablet_names = [name.strip() for name in names if name.strip()]
            break
    
    if not tablet_names:
        tablet_names = [tablet_names_text.strip()]
    
    # Display in grid format
    st.markdown('<div class="tablet-names-grid">', unsafe_allow_html=True)
    for name in tablet_names:
        if name:
            st.markdown(f'<div class="tablet-name-item">🏷️ {name}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def display_section_content(title, content, section_type="info"):
    """Display section content with appropriate styling."""
    if not content:
        return
    
    # Choose card style based on section type
    card_class = {
        "composition": "composition-card",
        "safety": "safety-card",
        "interaction": "interaction-card",
        "side-effects": "side-effects-list",
        "cost": "cost-info",
        "usage": "usage-instructions",
        "info": "info-card"
    }.get(section_type, "info-card")
    
    st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
    st.markdown(f'<div class="subsection-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="text-content">{content}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

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

    # Header
    st.markdown('<div class="section-header">🏥 MediScan - Indian Drug Analyzer</div>', unsafe_allow_html=True)
    
    # Medical disclaimer
    st.markdown("""
    <div class="disclaimer-box">
        ⚠️ <strong>MEDICAL DISCLAIMER</strong><br><br>
        This information is for educational purposes only and should not replace professional medical advice. 
        Always consult with a qualified healthcare provider before making any medical decisions or changes to your medication regimen.
        This tool provides information about medications commonly available in the Indian market.
    </div>
    """, unsafe_allow_html=True)
    
    # Upload Section
    st.markdown('<div class="section-title">📤 Upload Tablet Image</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Upload a clear image of the tablet or its packaging",
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload a high-quality image showing the tablet clearly"
        )
        
        if uploaded_file:
            resized_image = resize_image_for_display(uploaded_file)
            if resized_image:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.image(resized_image, caption="Uploaded Tablet Image", width=MAX_IMAGE_WIDTH)
                
                file_size = len(uploaded_file.getvalue()) / 1024
                st.success(f"✅ **{uploaded_file.name}** uploaded successfully • {file_size:.1f} KB")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Additional medications section
    st.markdown('<div class="section-title">💊 Additional Medications (Optional)</div>', unsafe_allow_html=True)
    
    additional_meds = st.text_area(
        "Enter other medications you are currently taking:",
        placeholder="e.g., Crocin 650mg twice daily, Metformin 500mg after meals, Telma 40mg once daily",
        help="Include Indian brand names, dosages, and frequency for interaction analysis",
        height=100
    )
    
    # Analyze button
    if uploaded_file:
        if st.button("🔬 Analyze Tablet & Get Complete Information", key="analyze_btn"):
            st.session_state.analyze_clicked = True
            st.session_state.additional_medications = additional_meds
            
            temp_path = save_uploaded_file(uploaded_file)
            if temp_path:
                try:
                    extracted_info = extract_composition_and_details(temp_path)
                    
                    if extracted_info:
                        st.session_state.analysis_results = extracted_info
                        st.session_state.original_image = uploaded_file.getvalue()
                        
                        # Extract drug composition
                        composition_match = re.search(r"\*Composition:\*(.*?)(?=\*[\w\s]+:\*|$)", extracted_info, re.DOTALL | re.IGNORECASE)
                        if composition_match:
                            st.session_state.drug_composition = composition_match.group(1).strip()
                        
                        # Analyze interactions if additional medications provided
                        if additional_meds.strip():
                            interaction_result = analyze_drug_interactions(
                                st.session_state.drug_composition or "Unknown composition",
                                additional_meds
                            )
                            st.session_state.interaction_analysis = interaction_result
                        
                        st.success("✅ Complete analysis finished successfully!")
                    else:
                        st.error("❌ Analysis failed. Please try with a clearer image.")
                        
                except Exception as e:
                    st.error(f"🚨 Analysis failed: {e}")
                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
    
    # Results Section
    if st.session_state.analysis_results:
        st.markdown('<div class="section-title">📊 Complete Drug Analysis Results</div>', unsafe_allow_html=True)
        
        analysis_text = st.session_state.analysis_results
        
        # Define sections with their display types
        sections_config = {
            "Composition": {"type": "composition", "icon": "🧬"},
            "Indian Brand Names": {"type": "brands", "icon": "🏷️"},
            "Medical Uses": {"type": "info", "icon": "💊"},
            "Dosage Instructions": {"type": "usage", "icon": "📋"},
            "Side Effects": {"type": "side-effects", "icon": "⚠️"},
            "Indian Market Price": {"type": "cost", "icon": "💰"},
            "Alcohol Safety": {"type": "safety", "icon": "🍺"},
            "Pregnancy Safety": {"type": "safety", "icon": "🤱"},
            "Breastfeeding Safety": {"type": "safety", "icon": "🍼"},
            "Driving Safety": {"type": "safety", "icon": "🚗"},
            "Storage Instructions": {"type": "info", "icon": "📦"},
            "Precautions": {"type": "safety", "icon": "🛡️"}
        }
        
        for section_name, config in sections_config.items():
            # Create pattern to match section
            pattern = rf"\*{re.escape(section_name)}:\*(.*?)(?=\*(?:{'|'.join(re.escape(s) for s in sections_config.keys())}):\*|$)"
            match = re.search(pattern, analysis_text, re.DOTALL | re.IGNORECASE)
            
            if match:
                content = match.group(1).strip()
                title = f"{config['icon']} {section_name}"
                
                if section_name == "Indian Brand Names":
                    st.markdown(f'<div class="subsection-title">{title}</div>', unsafe_allow_html=True)
                    display_tablet_names(content)
                elif section_name == "Indian Market Price":
                    st.markdown(f'<div class="cost-info">{title}<br>{content}</div>', unsafe_allow_html=True)
                else:
                    display_section_content(title, content, config["type"])
        
        # Drug Interaction Analysis
        if st.session_state.interaction_analysis:
            st.markdown('<div class="section-title">🔬 Drug Interaction Analysis</div>', unsafe_allow_html=True)
            
            st.markdown(f'<div class="info-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="subsection-title">📋 Additional Medications Analyzed</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="text-content">{st.session_state.additional_medications}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            interaction_text = st.session_state.interaction_analysis
            
            # Determine severity and display accordingly
            if "severe" in interaction_text.lower() or "major" in interaction_text.lower():
                st.error("🚨 **SEVERE/MAJOR INTERACTION DETECTED**")
                card_type = "interaction"
            elif "moderate" in interaction_text.lower():
                st.warning("⚠️ **MODERATE INTERACTION**")
                card_type = "safety"
            elif "minor" in interaction_text.lower():
                st.info("ℹ️ **MINOR INTERACTION**")
                card_type = "info"
            else:
                st.success("✅ **LOW INTERACTION RISK**")
                card_type = "composition"
            
            display_section_content("🔍 Interaction Analysis", interaction_text, card_type)
        
        # Important Reminders Section
        st.markdown('<div class="section-title">🛡️ Important Safety Reminders</div>', unsafe_allow_html=True)
        
        reminders = [
            {
                "title": "🩺 Consult Healthcare Provider",
                "content": "Always consult with a qualified doctor or pharmacist before starting, stopping, or changing any medication. This is especially important in India where many medications are available over-the-counter."
            },
            {
                "title": "🏥 Indian Healthcare Context",
                "content": "Medication availability and pricing may vary across different Indian cities and states. Always verify with local pharmacies for current prices and availability."
            },
            {
                "title": "💊 Medication Authenticity",
                "content": "Purchase medications only from licensed pharmacies or authorized online platforms. Verify the authenticity of medications, especially when buying online."
            },
            {
                "title": "🌡️ Storage in Indian Climate",
                "content": "Follow storage instructions carefully, especially considering India's tropical climate. Many medications require cool, dry storage away from direct sunlight."
            }
        ]
        
        for reminder in reminders:
            display_section_content(reminder["title"], reminder["content"], "info")
    
    else:
        st.markdown('<div class="section-title">📊 Analysis Results</div>', unsafe_allow_html=True)
        st.info("🔍 Upload a tablet image and click 'Analyze Tablet & Get Complete Information' to see detailed results here.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 14px; margin-top: 30px;">
        © 2025 MediScan - Indian Drug Analyzer | Powered by Gemini AI + Tavily<br>
        🇮🇳 Specialized for Indian Pharmaceutical Market
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
