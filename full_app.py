import streamlit as st
import pandas as pd
import re
from difflib import get_close_matches
import base64
from io import BytesIO
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="EthixGuard - Biosafety & Bioethics Compliance",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define the knowledge base for the chatbot
knowledge_base = {
    # Biosafety Questions
    "gmo": "GMOs (Genetically Modified Organisms) require special clearance from the GEAC (Genetic Engineering Approval Committee) in India. You need to obtain permission before any research, testing, or release.",
    "biosafety committee": "An Institutional Biosafety Committee (IBSC) is mandatory for institutions handling genetically engineered organisms. They oversee compliance with guidelines and report to RCGM.",
    "geac": "The Genetic Engineering Approval Committee (GEAC) is India's apex body for approval of activities involving large-scale use of hazardous microorganisms and recombinants in research and industrial production.",
    "rcgm": "The Review Committee on Genetic Manipulation (RCGM) under DBT reviews all ongoing research projects involving high-risk category and controlled field experiments.",
    "containment level": "Biosafety containment levels range from BSL-1 (minimal risk) to BSL-4 (dangerous pathogens). Each level requires specific safety equipment, practices, and facility design.",
    "biosafety guidelines": "The Government of India has published comprehensive biosafety guidelines through DBT. These cover rDNA research, large-scale operations, and environmental release of GMOs.",
    
    # Ethics Questions
    "informed consent": "Informed consent requires fully disclosing research procedures, risks, benefits, and alternatives to participants. Documentation must be maintained and approved by an ethics committee.",
    "animal ethics": "Animal ethics requires adherence to the 3Rs principle: Replacement, Reduction, and Refinement. CPCSEA approval is needed for animal experiments in India.",
    "food safety ethics": "Food safety ethics involves transparency about ingredients, additives, preservation methods, and potential allergens. All claims must be backed by scientific evidence.",
    "research ethics": "Research ethics includes honest reporting, proper attribution, data integrity, declaring conflicts of interest, and respecting intellectual property rights.",
    "institutional ethics committee": "An Institutional Ethics Committee (IEC) must review all research involving human subjects, ensuring protection of rights, safety, and well-being of participants.",
}

# Function to get response from knowledge base
def get_response(user_input):
    # Convert to lowercase and remove punctuation
    processed_input = re.sub(r'[^\w\s]', '', user_input.lower())
    
    # Check for direct matches first
    for key in knowledge_base:
        if key in processed_input:
            return knowledge_base[key]
    
    # If no direct match, look for close matches in keywords
    words = processed_input.split()
    for word in words:
        close_matches = get_close_matches(word, knowledge_base.keys(), n=1, cutoff=0.8)
        if close_matches:
            return knowledge_base[close_matches[0]]
    
    # Default response if no match found
    return "I don't have specific information on that topic. Please ask about biosafety guidelines, ethics requirements, or approval processes for more targeted assistance."

# Function to create downloadable report
def generate_report(biosafety_data, ethics_data):
    from datetime import datetime

    # Define BSL hierarchy for comparison
    bsl_hierarchy = {
        "Not determined yet": 0,
        "BSL-1": 1,
        "BSL-2": 2,
        "BSL-3": 3,
        "BSL-4": 4
    }

    # Minimum BSL requirements per research type (from your table, using the lower level for Animal Research)
    min_bsl = {
        "Clinical/Human Subjects": "BSL-2",
        "Animal Research": "BSL-1",  # Lower of ABSL-1 or ABSL-2
        "Food Production/Safety": "BSL-1",
        "Academic Research/Publication": "Not determined yet"
    }

    report = f"""
# EthixGuard Compliance Report
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Biosafety Compliance Summary

"""
    # Biosafety section
    passed = 0
    warnings = 0
    violations = 0

    for question, answer in biosafety_data.items():
        if answer == "Yes":
            status = "✅ Pass"
            passed += 1
        elif answer == "No":
            status = "❌ Violation"
            violations += 1
        else:
            status = "⚠️ Warning"
            warnings += 1
        report += f"- **{question}**: {answer} ({status})\n"

    report += f"""
### Summary
- Passes: {passed}
- Warnings: {warnings}
- Violations: {violations}

## Ethics Compliance Summary

"""

    # Ethics section
    passed = 0
    warnings = 0
    violations = 0

    # Determine required BSL for warning logic
    research_type = ethics_data.get("Research Type", "")
    required_bsl = min_bsl.get(research_type, "Not determined yet")
    user_bsl = ethics_data.get("Containment Level", "Not determined yet")

    # Always bullet the containment level and check if it meets the threshold
    user_bsl_val = bsl_hierarchy.get(user_bsl, 0)
    required_bsl_val = bsl_hierarchy.get(required_bsl, 0)
    if user_bsl_val < required_bsl_val:
        status = f"⚠️ Warning"
        warnings += 1
        report += f"- Containment Level: {user_bsl} ({status}) - Minimum required: {required_bsl}\n"
    else:
        status = f"✅ Pass"
        passed += 1
        report += f"- Containment Level: {user_bsl} ({status})\n"

    # Process all other ethics questions (excluding containment level, research type, notes)
    for question, answer in ethics_data.items():
        if question in ["Containment Level", "Research Type", "Additional Notes"]:
            continue
        if answer == "Yes" or answer == "No Conflicts Exist":
            status = "✅ Pass"
            passed += 1
        elif answer == "No":
            status = "❌ Violation"
            violations += 1
        else:
            status = "⚠️ Warning"
            warnings += 1
        report += f"- {question}: {answer} ({status})\n"

    report += f"""
### Summary
- Passes: {passed}
- Warnings: {warnings}
- Violations: {violations}

## Recommendations

"""
    # Recommendations
    if violations == 0 and warnings == 0:
        report += "### Congratulations! Your project is compliant with all biosafety and ethics guidelines.\n"
        

    elif violations > 0:
        report += "### Critical Action Items\n"
        report += "- Review all items marked as violations and take corrective action before proceeding.\n"
        if "No" in biosafety_data.values():
            report += "- Ensure all biosafety compliance requirements are met before proceeding\n"
        if "No" in ethics_data.values():
            report += "- Address ethical violations identified in this report\n"
    elif warnings > 0:
        report += "### Areas for Improvement\n"
        if user_bsl_val<required_bsl_val:
            report+=f"- {user_bsl} is below the recommended level {required_bsl} for {research_type}. Make sure to conduct experiments in suitable lab environments to ensure safety and compliance.\n" 
        report += "- Review warning items and consider addressing them\n"
        report += "- Consult with relevant committees for guidance\n"


    return report


# Function to create a download link for the report
def get_download_link(report, filename="EthixGuard_Report.txt"):
    """Generates a link to download the report as a text file"""
    b64 = base64.b64encode(report.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">Download Report</a>'
    return href

# Navigation
def main():
    # Sidebar for navigation
    st.sidebar.title("🛡️ EthixGuard")
    st.sidebar.subheader("Navigation")
    
    # Navigation options
    pages = {
        "Home": page_home,
        "Biosafety Compliance": page_biosafety,
        "Ethics Evaluation": page_ethics,
        "Generate Report": page_report,
        "Guidance Assistant": page_chatbot
    }
    
    # Navigation selection
    selection = st.sidebar.radio("Go to", list(pages.keys()))
    
    # Initialize session state for data storage
    if "biosafety_data" not in st.session_state:
        st.session_state.biosafety_data = {}
    if "ethics_data" not in st.session_state:
        st.session_state.ethics_data = {}
    if "chatbot_messages" not in st.session_state:
        st.session_state.chatbot_messages = []
    
    # Display the selected page
    pages[selection]()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.info(
        "EthixGuard: Bioethics & Biosafety Compliance Reviewer. "
        "Designed to help researchers and food producers ensure compliance with guidelines."
    )

# Home page
def page_home():
    st.title("🛡️ EthixGuard - Biosafety & Bioethics Compliance Reviewer")
    
    st.markdown("""
    Welcome to EthixGuard, your comprehensive biosafety and bioethics compliance tool. ☣️

    
    ### Purpose
    EthixGuard helps researchers and food producers ensure compliance with biosafety regulations 
    and ethical guidelines by providing structured checklists, evaluations, and reports.
    
    ### Features
    - **Biosafety Compliance Checker**: Based on Government of India Biosafety Guidelines
    - **Ethical Review Evaluator**: Covers clinical, animal, food safety, and research ethics
    - **Automated Report Generation**: Downloadable compliance summary with recommendations
    - **Guidance Assistant**: Get answers to your biosafety and ethics questions
    
    ### How to Use
    1. Navigate through the sidebar options
    2. Complete the Biosafety Compliance checklist
    3. Fill out the Ethics Evaluation form
    4. Generate and download your compliance report
    5. Use the Guidance Assistant for specific questions
    
    Get started by selecting "Biosafety Compliance" from the sidebar!
    """)
    
    # Display sample image - using a placeholder since we can't load external images
    st.image("biosafety.png", caption="Biosafety and ethics compliance are critical for research and production")

# Biosafety compliance page
def page_biosafety():
    st.title("Biosafety Compliance Checker")
    st.markdown("Complete the following checklist based on the Government of India Biosafety Guidelines.")
    
    with st.form("biosafety_form"):
        # GMO section
        st.subheader("GMO Handling")
        gmo_involved = st.radio("Does your research/process involve GMOs (Genetically Modified Organisms)?", 
                               ["Yes", "No", "Not Applicable"])
        
        ibsc_approval = st.radio("Has your Institutional Biosafety Committee (IBSC) approved the project?", 
                                ["Yes", "No", "Not Applicable"])
        
        
        
        containment_measures = st.radio("Have appropriate containment measures been implemented?", 
                                      ["Yes", "No", "Partially"])
        
        # Regulatory approval section
        st.subheader("Regulatory Approvals")
        rcgm_approval = st.radio("For high-risk category work, has RCGM approval been obtained?", 
                               ["Yes", "No", "Not Required"])
        
        geac_approval = st.radio("For environmental release or large-scale work, has GEAC approval been obtained?", 
                               ["Yes", "No", "Not Required"])
        
        # Training and documentation
        st.subheader("Training and Documentation")
        staff_training = st.radio("Have all staff received appropriate biosafety training?", 
                                ["Yes", "No", "Partially"])
        
        documentation = st.radio("Is all necessary biosafety documentation maintained?", 
                               ["Yes", "No", "Partially"])
        
        # Submit button
        submitted = st.form_submit_button("Save Biosafety Responses")
        
        if submitted:
            # Save responses to session state
            st.session_state.biosafety_data = {
                "GMO Involvement": gmo_involved,
                "IBSC Approval": ibsc_approval,
                "Containment Measures": containment_measures,
                "RCGM Approval": rcgm_approval,
                "GEAC Approval": geac_approval,
                "Staff Training": staff_training,
                "Documentation": documentation
            }
            st.success("Biosafety responses saved! Proceed to Ethics Evaluation or generate your report.")
    
    # Display current responses if they exist
    if st.session_state.biosafety_data:
        st.subheader("Your Biosafety Responses")
        
        # Create a DataFrame for display
        data = [[k, v] for k, v in st.session_state.biosafety_data.items()]
        df = pd.DataFrame(data, columns=["Question", "Response"])
        
        # Highlight responses based on compliance
        def highlight_responses(val):
            if val == "Yes":
                return "background-color: #c6efce; color: #006100"  # Green for pass
            elif val == "No":
                return "background-color: #ffc7ce; color: #9c0006"  # Red for violations
            elif val == "Partially" or val == "Not determined yet":
                return "background-color: #ffeb9c; color: #9c6500"  # Yellow for warnings
            return ""
        
        # Display styled DataFrame
        st.dataframe(df.style.map(highlight_responses, subset=["Response"]))

# Ethics evaluation page
def page_ethics():
    st.title("Ethics Evaluation")
    st.markdown("Complete the following ethics checklist applicable to your research or food production process.")

    # Research type selection with single selection (using selectbox instead of multiselect)
    research_type = st.selectbox(
        "Select the type of research applicable to your project:",
        ["Clinical/Human Subjects", "Animal Research", "Food Production/Safety", "Academic Research/Publication"]
    )

    # Initialize session state for storing ethics answers if not already present
    if "ethics_answers" not in st.session_state:
        st.session_state.ethics_answers = {}

    # Clinical ethics section - outside the form to appear immediately after selection
    if research_type == "Clinical/Human Subjects":
        # Containment section
        st.subheader("Biosafety Containment")
        st.session_state.ethics_answers["Containment Level"]=st.radio("What containment level is required for your work?", 
                                       ["BSL-1", "BSL-2", "BSL-3", "BSL-4", "Not determined yet"])
        st.subheader("Clinical Ethics")
        
        st.session_state.ethics_answers["Informed Consent"] = st.radio(
            "Has informed consent been obtained from all participants?",
            ["Yes", "No", "Partially", "Not Applicable"]
        )
        
        st.session_state.ethics_answers["Vulnerable Populations"] = st.radio(
            "Does the research involve vulnerable populations (children, pregnant women, etc.)?",
            ["Yes", "No"]
        )
        
        if st.session_state.ethics_answers["Vulnerable Populations"] == "Yes":
            st.session_state.ethics_answers["Special Protections"] = st.radio(
                "Have special protections been implemented for vulnerable populations?",
                ["Yes", "No", "Partially"]
            )
        else:
            st.session_state.ethics_answers["Special Protections"] = "Not Applicable"
        
        st.session_state.ethics_answers["Privacy Measures"] = st.radio(
            "Are adequate privacy and confidentiality measures in place?",
            ["Yes", "No", "Partially"]
        )

    # Animal ethics section
    elif research_type == "Animal Research":
        # Containment section
        st.subheader("Biosafety Containment")
        st.session_state.ethics_answers["Containment Level"]=st.radio("What containment level is required for your work?", 
                                       ["BSL-1", "BSL-2", "BSL-3", "BSL-4", "Not determined yet"])
        st.subheader("Animal Ethics")
        st.session_state.ethics_answers["CPCSEA Approval"] = st.radio(
            "Has CPCSEA approval been obtained for animal research?",
            ["Yes", "No", "Pending"]
        )
        
        st.session_state.ethics_answers["3Rs Principle"] = st.radio(
            "Does your protocol follow the 3Rs principle (Replacement, Reduction, Refinement)?",
            ["Yes", "No", "Partially"]
        )
        
        st.session_state.ethics_answers["Pain Management"] = st.radio(
            "Are adequate pain management protocols in place?",
            ["Yes", "No", "Partially", "Not Required"]
        )

    # Food safety ethics section
    elif research_type == "Food Production/Safety":
        # Containment section
        st.subheader("Biosafety Containment")
        st.session_state.ethics_answers["Containment Level"]=st.radio("What containment level is required for your work?", 
                                       ["BSL-1", "BSL-2", "BSL-3", "BSL-4", "Not determined yet"])
        st.subheader("Food Safety Ethics")
        st.session_state.ethics_answers["Ingredient Transparency"] = st.radio(
            "Is there full transparency regarding ingredients and additives?",
            ["Yes", "No", "Partially"]
        )
        
        st.session_state.ethics_answers["Safety Data Availability"] = st.radio(
            "Is all safety data publicly available?",
            ["Yes", "No", "Partially"]
        )
        
        st.session_state.ethics_answers["Environmental Impact Assessment"] = st.radio(
            "Has environmental impact been assessed?",
            ["Yes", "No", "Partially"]
        )

    # Research publication ethics section
    elif research_type == "Academic Research/Publication":
        # Containment section
        st.subheader("Biosafety Containment")
        st.session_state.ethics_answers["Containment Level"]=st.radio("What containment level is required for your work?", 
                                       ["BSL-1", "BSL-2", "BSL-3", "BSL-4", "Not determined yet"])
        st.subheader("Research Publication Ethics")
        st.session_state.ethics_answers["Data Integrity"] = st.radio(
            "Is there assurance of data integrity and availability?",
            ["Yes", "No", "Partially"]
        )
        
        st.session_state.ethics_answers["Conflict of Interest Declaration"] = st.radio(
            "Have all conflicts of interest been declared?",
            ["Yes", "No", "Partially", "No Conflicts Exist"]
        )
        
        st.session_state.ethics_answers["Proper Attribution"] = st.radio(
            "Is proper attribution and citation provided for all sources?",
            ["Yes", "No", "Partially"]
        )

    # Additional notes
    notes = st.text_area("Additional ethical considerations or notes:", "")

    # Save button (outside of form)
    if st.button("Save Ethics Responses"):
        # Save all answers to main session state
        st.session_state.ethics_data = {
            "Research Type": research_type,
            **st.session_state.ethics_answers,
            "Additional Notes": notes
        }
        st.success("Ethics responses saved! You can now generate your compliance report.")

    # Display current responses if they exist
    if "ethics_data" in st.session_state and st.session_state.ethics_data:
        st.subheader("Your Ethics Responses")
        
        # Filter out Not Applicable responses for cleaner display
        filtered_data = {k: v for k, v in st.session_state.ethics_data.items() 
                         if v != "Not Applicable" and k != "Additional Notes"}
        
        # Create a DataFrame for display
        data = [[k, v] for k, v in filtered_data.items()]
        df = pd.DataFrame(data, columns=["Question", "Response"])
        
        # Highlight responses based on compliance
        def highlight_responses(val):
            if val == "Yes" or val == "No Conflicts Exist":
                return "background-color: #c6efce; color: #006100"  # Green for pass
            elif val == "No":
                return "background-color: #ffc7ce; color: #9c0006"  # Red for violations
            elif val == "Partially" or val == "Pending":
                return "background-color: #ffeb9c; color: #9c6500"  # Yellow for warnings
            return ""
        
        # Display styled DataFrame
        st.dataframe(df.style.map(highlight_responses, subset=["Response"]))
        
        # Display additional notes if any
        if st.session_state.ethics_data["Additional Notes"]:
            st.subheader("Additional Notes")
            st.text_area("", st.session_state.ethics_data["Additional Notes"], disabled=True)

# Report generation page
def page_report():
    st.title("Generate Compliance Report")
    
    # Check if both biosafety and ethics data are available
    if not st.session_state.biosafety_data:
        st.warning("Please complete the Biosafety Compliance section before generating a report.")
    elif not st.session_state.ethics_data:
        st.warning("Please complete the Ethics Evaluation section before generating a report.")
    else:
        st.success("All required information has been collected. You can now generate your report.")
        
        if st.button("Generate Compliance Report"):
            # Generate the report
            report = generate_report(st.session_state.biosafety_data, st.session_state.ethics_data)
            
            # Display the report
            st.subheader("EthixGuard Compliance Report")
            st.markdown(report)
            
            # Provide download link
            st.markdown(get_download_link(report), unsafe_allow_html=True)
            
            # Add visualization of compliance status
            st.subheader("Compliance Visualization")
            
            # Count status for biosafety
            biosafety_pass = sum(1 for v in st.session_state.biosafety_data.values() if v == "Yes")
            biosafety_warn = sum(1 for v in st.session_state.biosafety_data.values() if v == "Partially" or v == "Not determined yet")
            biosafety_fail = sum(1 for v in st.session_state.biosafety_data.values() if v == "No")
            
            # Count status for ethics (excluding Not Applicable)
            ethics_pass = sum(1 for v in st.session_state.ethics_data.values() if v == "Yes" or v == "No Conflicts Exist")
            ethics_warn = sum(1 for v in st.session_state.ethics_data.values() if v == "Partially" or v == "Pending")
            ethics_fail = sum(1 for v in st.session_state.ethics_data.values() if v == "No")
            
            # Create two columns for biosafety and ethics metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Biosafety Compliance")
                
                # Create a DataFrame for the metrics
                biosafety_metrics = pd.DataFrame({
                    "Status": ["Pass", "Warning", "Violation"],
                    "Count": [biosafety_pass, biosafety_warn, biosafety_fail]
                })
                
                # Display metrics
                st.bar_chart(biosafety_metrics.set_index("Status"))
            
            with col2:
                st.subheader("Ethics Compliance")
                
                # Create a DataFrame for the metrics
                ethics_metrics = pd.DataFrame({
                    "Status": ["Pass", "Warning", "Violation"],
                    "Count": [ethics_pass, ethics_warn, ethics_fail]
                })
                
                # Display metrics
                st.bar_chart(ethics_metrics.set_index("Status"))

# Chatbot page
def page_chatbot():
    st.title("Guidance Assistant")
    st.markdown("""
    Ask questions about biosafety guidelines, ethics requirements, or compliance procedures.
    This assistant can provide guidance based on Government of India regulations and general 
    bioethics principles.
    """)
    
    # Initialize chat history if not already
    if "chatbot_messages" not in st.session_state:
        st.session_state.chatbot_messages = []
    
    # Display chat messages
    for message in st.session_state.chatbot_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Get user input
    if prompt := st.chat_input("Ask a question about biosafety or ethics"):
        # Add user message to chat history
        st.session_state.chatbot_messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get response
        response = get_response(prompt)
        
        # Display assistant response
        with st.chat_message("assistant"):
            st.write(response)
        
        # Add assistant response to chat history
        st.session_state.chatbot_messages.append({"role": "assistant", "content": response})

# Run the app
if __name__ == "__main__":
    main()
