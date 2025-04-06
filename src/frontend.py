import streamlit as st
from dotenv import load_dotenv
import os
import pymupdf
from streamlit_pdf_viewer import pdf_viewer

from agents.compliance_agent_optimised import ComplianceAgent
from agents.checklist_agent_optimised import ChecklistAgent
from scoring import calculate_compliance_score
from agents.risk_analysis_agent_optimised import RiskAnalysisAgent
from agents.rag_agent import RAGAgent
from agents.query_agent import QueryAgent
from agents.report_agent import generate_pdf_report
from agents.reference_agent import get_references

load_dotenv()


def get_company_profile() -> str:
    path = os.path.join(os.path.dirname(__file__), "company_profile.txt")
    if not os.path.exists(path):
        st.error(f"Company profile file not found: {path}")
        return ""
    with open(path, "r") as file:
        return file.read()


def extract_text_from_pdf(pdf_path: str) -> str:
    if not os.path.exists(pdf_path):
        st.error(f"PDF file not found: {pdf_path}")
        return ""
    try:
        with pymupdf.open(pdf_path) as doc:
            return "".join(page.get_text() for page in doc)
    except Exception as e:
        st.error(f"Error extracting text: {e}")
        return ""


def use_rag_agent(question: str, filename=None) -> str:
    query_agent = QueryAgent()
    context = "\n\n".join(
        query_agent.retrieve_relevant_data(
            user_query=question, namespace="test", filename=filename, top_k=3
        )
    )
    return (
        context
        if context == "No relevant data found"
        else RAGAgent().invoke(context, question)
    )


def init_session_state():
    defaults = {
        "pdf_text": "",
        "process_stage": "upload_file",
        "pdf_path": None,
        "company_profile": get_company_profile(),
        "compliance_dict": "",
        "checklist_agent_response": "",
        "risk_analysis_response": "",
        "report_pdf_path": "",
        "messages": [
            {
                "role": "assistant",
                "content": "I'm here to assist you with your RFP analysis.",
            }
        ],
        "filename": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def display_pdf_sidebar():
    with st.sidebar:
        pdf_viewer(st.session_state.pdf_path, width=800, height=600)


def display_compliance_results():
    score = calculate_compliance_score(st.session_state.compliance_dict)
    with st.container(border=True):
        st.subheader("Compliance Score")

        # st.write(f"Score Percentage: {score['score_percentage']}%")
        if score["score_percentage"] < 50:
            st.write("**Ineligible**")
        else:
            st.write("**Eligible**")
        st.write(
            f"Eligibility Satisfied: {score['criteria_matched']}/{score['total_criteria_evaluated']}"
        )

    for criteria in st.session_state.compliance_dict["compliance_criteria"]:
        icon = "✅" if criteria.get("matches") else "❌"
        if (
            "not found" in criteria["current"].lower()
            or "not available" in criteria["current"].lower()
        ):
            icon = "❓"
        with st.expander(criteria["criteria"], icon=icon):
            st.write(criteria["required"])
            st.write(criteria["importance"])
            st.write(f"Your Company Profile: {criteria['current']}")
            st.write("Eligible: Yes" if criteria.get("matches") else "Eligible: No")
            if not criteria.get("matches") and criteria.get("corrective_steps"):
                st.write(
                    "Corrective Steps: "
                    + " ".join(f"- {s}" for s in criteria["corrective_steps"])
                )


def main():
    init_session_state()
    st.set_page_config(
        page_title="RFP Analyser", page_icon=":guardsman:", layout="wide"
    )

    stage = st.session_state.process_stage

    if stage == "upload_file":
        with st.sidebar:
            st.title("Menu:")
            uploaded_file = st.file_uploader("Upload the RFP Document", type=["pdf"])
            if uploaded_file and st.button("Analyse RFP"):
                with st.spinner("Processing..."):
                    st.session_state.filename = uploaded_file.name
                    save_path = os.path.abspath(
                        os.path.join("temp_files", uploaded_file.name)
                    )
                    os.makedirs("temp_files", exist_ok=True)
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.read())
                    st.session_state.pdf_path = save_path
                    st.session_state.pdf_text = extract_text_from_pdf(save_path)
                    st.success("Your RFP Document is uploaded.")
                    st.session_state.process_stage = "compliance_check"
                    st.rerun()

        st.title("RFP Analyser")
        st.write("Upload the RFP document to get started.")

    elif stage == "compliance_check":
        display_pdf_sidebar()

        if st.session_state.compliance_dict:
            display_compliance_results()
        else:
            with st.spinner("Running compliance check..."):
                if not st.session_state.pdf_text:
                    st.error("No text extracted from the PDF.")
                    return
                if not st.session_state.company_profile:
                    st.error("No company profile found.")
                    return

                result = ComplianceAgent().invoke(
                    rfp_text=st.session_state.pdf_text,
                    company_profile=st.session_state.company_profile,
                    filename=st.session_state.filename,
                )
                if result.get("error"):
                    st.error(result["error"])
                    return

                st.session_state.compliance_dict = result
                display_compliance_results()

        if st.button("Generate Checklist"):
            st.session_state.process_stage = "generate_checklist"
            st.rerun()

    elif stage == "generate_checklist":
        display_pdf_sidebar()
        if st.session_state.checklist_agent_response:
            for item in st.session_state.checklist_agent_response["items"]:
                with st.expander(item["task"], icon="⏹️"):
                    st.write(item["priority"])
                    st.write(f"Deadline: {item['deadline']}")
        else:
            with st.spinner("Generating checklist..."):
                result = ChecklistAgent().invoke(
                    rfp_text=st.session_state.pdf_text,
                    filename=st.session_state.filename,
                )
                if result.get("error"):
                    st.error(result["error"])
                    return
                st.session_state.checklist_agent_response = result
                st.rerun()

        if st.button("Back to Compliance Check"):
            st.session_state.process_stage = "compliance_check"
            st.rerun()

        if st.button("Analyze Risks"):
            st.session_state.process_stage = "analyze_risks"
            st.rerun()

    elif stage == "analyze_risks":
        display_pdf_sidebar()
        response = st.session_state.risk_analysis_response

        if not response:
            with st.spinner("Analyzing risks..."):
                result = RiskAnalysisAgent().invoke(
                    rfp_text=st.session_state.pdf_text,
                    company_profile=st.session_state.company_profile,
                    filename=st.session_state.filename,
                )
                if result.get("error"):
                    st.error(result["error"])
                    return
                st.session_state.risk_analysis_response = result
                st.rerun()
        else:
            for risk in response["identified_risks"]:
                icon = {"High": "🛑", "Medium": "⚠️"}.get(risk["severity"], "ℹ️")
                with st.expander(risk["risk_description"], icon=icon):
                    st.write(f"Severity: {risk['severity']}")
                    st.write(f"Mitigation Strategy: {risk['mitigation_strategy']}")

        if st.button("Back to Checklist"):
            st.session_state.process_stage = "generate_checklist"
            st.rerun()

        if st.button("Chat with RFP Document"):
            st.session_state.process_stage = "chat_pdf"
            st.rerun()

        if st.button("Generate Report"):
            st.session_state.process_stage = "report_page"
            st.rerun()

    elif stage == "chat_pdf":
        display_pdf_sidebar()

        if st.button("Back to Risk Analysis"):
            st.session_state.process_stage = "analyze_risks"
            st.rerun()

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        if prompt := st.chat_input():
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = use_rag_agent(prompt, filename=st.session_state.filename)
                    st.write(response)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response}
                    )

    elif stage == "report_page":
        if not st.session_state.report_pdf_path:
            with st.spinner("Generating report..."):
                references = get_references(st.session_state.pdf_text[:1000])
                data = {
                    "eligibility": st.session_state.compliance_dict,
                    "checklist": st.session_state.checklist_agent_response,
                    "risk_analysis": st.session_state.risk_analysis_response,
                    "references": references,
                }
                report_agent = generate_pdf_report(data=data, filename="Report.pdf")
                st.session_state.report_pdf_path = os.path.abspath("Report.pdf")

        with st.sidebar:
            pdf_viewer(st.session_state.report_pdf_path, width=800, height=600)

        with open(st.session_state.report_pdf_path, "rb") as f:
            st.download_button(
                label="Download Report",
                data=f,
                file_name="Report.pdf",
                mime="application/pdf",
            )

        if st.button("Back to Chat"):
            st.session_state.process_stage = "chat_pdf"
            st.rerun()
        if st.button("Back to Risk Analysis"):
            st.session_state.process_stage = "analyze_risks"
            st.rerun()


if __name__ == "__main__":
    main()
