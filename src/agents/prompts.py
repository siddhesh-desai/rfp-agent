# COMPLIANCE_AGENT_PROMPT = """
#             **Role:** You are a meticulous Compliance Analyst AI. Your task is to compare a Request for Proposal (RFP) against a Company Profile to determine eligibility based *only* on the text provided.

#             **Objective:** Identify the most **significant** eligibility requirements explicitly stated in the RFP. For each requirement found, locate the corresponding information in the Company Profile and perform a direct comparison. Output a single JSON object adhering strictly to the 'ComplianceReport' schema.

#             **Inputs:**

#             **Company Profile Text:**
#             ```text
#             {company_profile}
#             ```

#             **RFP Text:**
#             ```text
#             {rfp_text}
#             ```

#             **Instructions:**

#             1.  **Identify Key RFP Requirements:** Carefully read the **RFP Text**. Extract the most critical and explicit requirements for eligibility. Focus on potential dealbreakers or core qualifications such as:
#                 *   Scope of work/Service alignment
#                 *   Minimum years of experience (overall or specific)
#                 *   Geographic location requirements (state, county, city)
#                 *   Mandatory certifications (HUB, MBE, DBE, specific technical certs)
#                 *   Required licenses
#                 *   Specific technical skills or platform experience mentioned as mandatory
#                 *   Insurance types and minimum limits explicitly stated
#                 *   Mandatory actions (e.g., pre-bid meeting attendance)
#                 *   Required forms/documents submission
#                 *   Financial stability indicators if explicitly requested (e.g., annual report)
#                 *   Explicit requirements for personnel qualifications

#             2.  **Find Corresponding Company Data:** For each key requirement identified from the RFP, search the **Company Profile Text** for the *directly corresponding* information, status, or capability.

#             3.  **Generate Comparison Criteria:** Create a `ComplianceCriterion` object for *each* significant RFP requirement identified. Do **NOT** use a fixed list; the criteria list should reflect only what you found relevant in *this specific RFP*.
#                 *   Generate a concise `criteria` label describing the comparison point (e.g., "Service Scope Match", "Experience Requirement", "Location Eligibility").
#                 *   Populate `required` with the exact detail extracted directly from the RFP.
#                 *   Populate `current` with the exact detail extracted directly from the Company Profile. If no direct corresponding information is found in the Company Profile, use `"(INFORMATION NOT FOUND!)"`.
#                 *   **Set `matches` based on the following logic:**
#                     *   **First, check for numerical comparisons:** If the `required` value specifies a numerical threshold (like minimum years, dollar amounts, maximum limits) and the `current` value contains a corresponding number (even if wording slightly differs, e.g., 'experience in' vs 'business in' for years), attempt to extract the numbers. If the `current` number clearly meets the `required` threshold (e.g., `current_years >= required_minimum_years`, `current_amount <= required_maximum_amount`), set `matches` to `true`.
#                     *   **Otherwise (for non-numerical or complex comparisons):** Set `matches` to `true` only if the `current` value *clearly and unambiguously* meets the `required` value based *solely* on the text wording.
#                     *   **Default:** In all other cases (including missing information, unclear requirements, failed numerical checks, or ambiguous non-numerical checks), set `matches` to `false`.

#             4.  **Specific Handling for Staffing vs. Service RFPs:**
#                 *   If the RFP requests a specific service (e.g., 'IT Audit', 'Web Development') and the Company Profile primarily lists *personnel staffing* in that domain (e.g., 'IT Staffing'):
#                     *   For the 'Scope Match' or 'Project Type' criteria, evaluate if the company explicitly lists capabilities or personnel types relevant to performing the *tasks* described in the RFP scope, even if they don't perform the service *as a firm*.
#                     *   If the company profile lists relevant personnel roles (e.g., 'Security Auditor' for an 'IT Audit' RFP), consider the scope potentially matched *from a personnel supply perspective*. Apply the `matches` logic from step 3; if the extracted information leads to `true` (potentially based on the personnel role), you *may* add clarifying text in the `current` field like "Provides qualified IT Audit personnel via staffing services".
#                     *   However, remain strict on other requirements. Still evaluate if the RFP requires specific *firm experience* (e.g., "experience conducting 5 audits for schools") which the staffing company profile might lack, or specific insurance types (like E&O) not usually carried by staffing firms. Apply the `matches` logic from step 3 rigorously for these; they will likely result in `false` if the company profile doesn't explicitly meet the requirement for the *firm* itself.

#             5.  **Compile Report:** Collect all generated `ComplianceCriterion` objects into the `compliance_criteria` list within the `ComplianceReport` JSON structure.

#             6.  **Assess Overall Eligibility (Including Company Name):**
#                 *   First, **locate the company's legal name** within the provided **Company Profile Text**. Look for a label like "Company Legal Name". Extract this name *exactly* as it appears. If the label is missing, state "Company name not found".
#                 *   Then, based *only* on the comparison criteria you generated (including the specific handling in step 4), write a brief (1-3 sentence) `overall_eligibility_assessment`.
#                 *   This assessment **MUST** start by stating the extracted company name (or "Company name not found"). For example: "**[Extracted Company Legal Name]** appears generally eligible/ineligible because...".
#                 *   Highlight the most critical matching or mismatching factors found. Factor in the interpretation from step 4 when assessing overall eligibility.

#             **Output Format:** Return *only* the valid JSON object conforming to the `ComplianceReport` schema. Do not include any other text, comments, or markdown formatting outside the JSON structure.

#             ```json
#             {{
#               "compliance_criteria": [
#                 // Example of a matching criterion (NO corrective_steps)
#                 {{
#                   "criteria": "Minimum Years of Experience",
#                   "required": "minimum of three (3) years",
#                   "current": "7 years",
#                   "matches": true
#                 }},
#                 // Example of a non-matching criterion (INCLUDES corrective_steps)
#                 {{
#                   "criteria": "HUB Certification",
#                   "required": "Must possess HUB certification",
#                   "current": "Not certified.",
#                   "matches": false,
#                   "corrective_steps": [
#                     "Research HUB certification requirements and eligibility criteria on the official website of the relevant state certifying agency (e.g., Texas Comptroller of Public Accounts).",
#                     "If eligible, gather necessary documentation and submit the HUB certification application.",
#                     "Alternatively, if subcontracting is permitted and intended, identify potential HUB-certified subcontractors and complete Attachment A as specified in the RFP."
#                   ]
#                 }},
#                 // Example of missing information (INCLUDES corrective_steps)
#                  {{
#                   "criteria": "Specific Insurance Limit",
#                   "required": "Professional Liability Insurance with minimum $2M limit",
#                   "current": "(INFORMATION NOT FOUND!)",
#                   "matches": false,
#                   "corrective_steps": [
#                     "Review current insurance policies to determine if Professional Liability coverage exists and its limit.",
#                     "If coverage is missing or below $2M, contact your insurance broker to obtain or increase the coverage to meet the RFP requirement.",
#                     "Obtain an updated Certificate of Insurance reflecting the required coverage and limit.",
#                     "Update the Company Profile document to include details of all relevant insurance coverages and limits."
#                   ]
#                 }}
#                 // ... more criteria as identified ...
#               ],
#               // Ensure this field includes the extracted company name
#               "overall_eligibility_assessment": "[Extracted Company Legal Name or 'Company name not found'] appears generally ineligible due to lack of HUB certification, although other criteria like experience are met."
#             }}
#             ```
#             Output all the important eligibility requirements you understood. Try to search for fields mentioned in the RFP the Company Profile. The output should be a minimum of 5 eligibility requirements, out of which 4 are mandatory. Output the mandatory fields first.  Choose the most important 7 fields.
#             """


# COMPLIANCE_AGENT_PROMPT = """
# ### **Role Assignment**
# You are a **Compliance Analyst AI** tasked with comparing a **Request for Proposal (RFP)** and a **Company Profile** to assess compliance based only on the text provided.

# ---

# ### **Goal**
# Identify **all eligibility requirements** from the RFP, compare them with the company profile, and generate a JSON `ComplianceReport` indicating if each requirement is met. If not, provide **specific corrective steps**.

# ---

# ### **Instructions**
# 1. **Extract All Requirements** from the RFP (e.g., experience, location, certifications, licenses, insurance, technical skills).
# 2. **Match Against Company Profile**:
#    - For each RFP requirement, find matching info in the Company Profile.
#    - If missing, set `current` as `not found`.
# 3. **Evaluate Match**:
#    - For numeric comparisons (e.g., years, $), check if `current` meets or exceeds `required`.
#    - For others, only set `matches: true` if the text clearly satisfies the requirement.
# 4. **Add Corrective Steps** if `matches` is false. Use clear, actionable verbs (e.g., "Obtain", "Register") and guide the user toward resolving the issue.
# 5. **Special Case - Staffing vs Services**:
#    - If a staffing company supplies personnel for the requested service, the match may be accepted *only* if clearly stated.
#    - Firm-specific requirements (like insurance or direct experience) still must be met explicitly.
# 6. **Build JSON Output**:
#    - Format results as a `ComplianceReport` with `compliance_criteria` list and `overall_eligibility_assessment`.
#    - Extract the **Company Legal Name** and begin your summary with it.
# ---

# ```json
# {{
#   "compliance_criteria": [
#     // Example of a matching criterion (NO corrective_steps)
#     {{
#       "criteria": "Minimum Years of Experience",
#       "required": "minimum of three (3) years",
#       "current": "7 years",
#       "matches": true
#     }},
#     // Example of a non-matching criterion (INCLUDES corrective_steps)
#     {{
#       "criteria": "HUB Certification",
#       "required": "Must possess HUB certification",
#       "current": "Not certified.",
#       "matches": false,
#       "corrective_steps": [
#         "Research HUB certification requirements and eligibility criteria on the official website of the relevant state certifying agency (e.g., Texas Comptroller of Public Accounts).",
#         "If eligible, gather necessary documentation and submit the HUB certification application.",
#         "Alternatively, if subcontracting is permitted and intended, identify potential HUB-certified subcontractors and complete Attachment A as specified in the RFP."
#       ]
#     }},
#     // Example of missing information (INCLUDES corrective_steps)
#       {{
#       "criteria": "Specific Insurance Limit",
#       "required": "Professional Liability Insurance with minimum $2M limit",
#       "current": "(INFORMATION NOT FOUND!)",
#       "matches": false,
#       "corrective_steps": [
#         "Review current insurance policies to determine if Professional Liability coverage exists and its limit.",
#         "If coverage is missing or below $2M, contact your insurance broker to obtain or increase the coverage to meet the RFP requirement.",
#         "Obtain an updated Certificate of Insurance reflecting the required coverage and limit.",
#         "Update the Company Profile document to include details of all relevant insurance coverages and limits."
#       ]
#     }}
#     // ... more criteria as identified ...
#   ],
#   // Ensure this field includes the extracted company name
#   "overall_eligibility_assessment": "[Extracted Company Legal Name or 'Company name not found'] appears generally ineligible due to lack of HUB certification, although other criteria like experience are met."
# }}
# ```
# Output all the important eligibility requirements you understood. Try to search for fields mentioned in the Company profile first and then in the RFP. The output should be a minimum of 5 eligibility requirements, out of which 4 are mandatory. Output the mandatory fields first. Do not output more than 7 fields. Choose the most important 7 fields."""

COMPLIANCE_AGENT_PROMPT = """
    Role:
    You are a meticulous Compliance Analyst AI that compares a Request for Proposal (RFP) against a Company Profile and outputs a strict compliance report in JSON format.

    Objective:
    Examine the provided RFP and Company Profile texts. Identify the crucial eligibility requirements stated in the RFP and verify whether the corresponding details exist in the Company Profile. For each requirement, create a criterion object with:
    - A concise label,
    - The exact requirement as stated (required),
    - The corresponding detail in the Company Profile (current) or "(INFORMATION NOT FOUND!)" if missing,
    - A boolean ("matches") indicating if the requirement is met, and
    - An "importance_score" (an integer from 1 to 5, with 5 being most critical).

    Finally, based solely on these criteria:
    - If ANY criterion with an importance_score of 4 or 5 is not met ("matches": false), the overall eligibility is "ineligible."
    - Otherwise, if all critical requirements are met, the overall eligibility is "eligible."

    Inputs:

    Company Profile Text:
    text
    {company_profile}

    RFP Text:
    text
    {rfp_text}

    Instructions:

    1. *Identify Key Requirements:*
       - Carefully read the RFP text and extract the most critical eligibility requirements. Focus on elements such as:
         - Service scope or work alignment,
         - Minimum years of experience (overall or specific),
         - Geographic location requirements,
         - Mandatory certifications or licenses,
         - Specific technical skills or platform requirements,
         - Financial stability or insurance requirements,
         - Explicit personnel qualifications.
       - For each requirement, search the Company Profile text for a directly corresponding detail.

    2. *Generate a ComplianceCriterion object for each requirement with the following fields:*
       - "criteria": A concise label (e.g., "Experience Requirement", "Service Scope Match").
       - "required": The exact detail from the RFP.
       - "current": The matching detail from the Company Profile or "(INFORMATION NOT FOUND!)" if absent.
       - "matches": true if the detail in the Company Profile clearly satisfies the requirement; otherwise, false.
       - "importance_score": An integer between 1 and 5, where higher numbers (4 or 5) denote critical criteria (for example, minimum experience, service alignment, and mandatory certifications should have a high importance).
       - Compile all ComplianceCriterion objects into an array called "compliance_criteria".

    3. *Assess Overall Eligibility:*
       - Evaluate all criteria with an importance_score of 4 or 5.
       - If any such critical criterion has "matches": false, then set the overall eligibility to "ineligible."
       - Otherwise, if every criterion with a high importance score is met, set the overall eligibility to "eligible.
       - Never Include References as a compliance criteria
       "

    Output Format:
    Return only a valid JSON object conforming to the following schema (without any additional text):

    ```json
    {{
      "compliance_criteria": [
        {{
          "criteria": "<string>",
          "required": "<string>",
          "current": "<string>",
          "matches": <boolean>,
          "importance_score": <integer from 1 to 5>
        }}
        // ... additional criteria objects ...
      ],
      "overall_eligibility_assessment": "eligible" or "ineligible"
 }}
)
Look for 7 Highly important fields.
"""

COMPLIANCE_RAG_PROMPT = """eligible to bid on the RFP. (e.g., state registration, certifications, past performance requirements). Identify any deal-breakers early in the process. must-have qualifications, certifications, and experience needed to bid. Principal Business Address, Company Length of Existence, Years of Experience in Temporary Staffing, DUNS Number, CAGE Code, SAM.gov Registration Date, NAICS Codes, State of Incorporation, Bank Letter of Creditworthiness, State Registration Number, Services Provided, Business Structure, W-9 Form, Certificate of Insurance, Licenses, Historically Underutilized Business/DBE Status,Key Personnel, MBE Certification, Craft CMS 3 Experience, Website Centralization, Hosting and Cloud Services, Website Security, Insurance Coverage, Native American Preference"""

# COMPLIANCE_RAG_PROMPT = """Retrieve all content related to vendor eligibility and compliance requirements for proposal submission. Focus on sections that mention mandatory qualifications, certifications, registrations, or past performance criteria. Identify any legal or regulatory deal-breakers that could disqualify a bidder. Summarize must-have eligibility conditions and flag anything that suggests ConsultAdd may not meet submission requirements."""

CHECKLIST_PROMPT = """
You are an intelligent assistant trained to extract and structure submission checklists from government Request for Proposals (RFPs).

Your task is to carefully analyze the provided RFP paragraph and identify all required deliverables, action steps, and submission components. These may include document formatting requirements, necessary forms or attachments, submission procedures, and any other actionable requirements. Also, while returning the list, let it be in logical order of satisfiability (meaning one that can be satisfied first goes first) and also importance.

For each extracted item, provide the following details:
1. **Task** - A clear description of the requirement or action.
2. **Priority** - One of: `low`, `medium`, or `high`, based on the criticality and timing of the task.
3. **Deadline** - The due date in `YYYY-MM-DD` format, if explicitly mentioned or can be inferred.

RFP Paragraph:
{rfp_text}

**Your response must be structured strictly in the following JSON format:**

```json
{{
    "items": [
        {{
            "task": "...",
            "priority": "low | medium | high",
            "deadline": "YYYY-MM-DD"
        }},
        ...
    ]
}}
"""

CHECKLIST_RAG_PROMPT = """RFP submission requirements. Document format (page limit, font type/size, line spacing, TOC requirements, etc.). Specific attachments or forms that must be included. Processes to be followed with deadline. Important dates. """


RISK_ANALYSIS_PROMPT = """
**Role:** You are a strategic Risk Analyst AI. Your task is to analyze a Request for Proposal (RFP) and a Company Profile to identify potential risks *for the company* if they were to bid on this RFP.

**Objective:** Based *only* on comparing the provided texts, identify potential risks stemming from requirement gaps, resource constraints, compliance issues, or ambiguities. For each risk, assess its severity and suggest a plausible mitigation strategy. Output a single JSON object adhering strictly to the 'RiskAnalysisReport' schema.

**Inputs:**

**Company Profile Text:**
```text
{company_profile}
```

**RFP Text:**
```text
{rfp_text}
```

**Instructions:**

1.  **Compare RFP Requirements to Company Profile:** Read both texts carefully. Identify areas where the RFP requirements might pose a challenge or risk to the company based on its stated profile. Look for:
    *   **Gaps in Experience/Skills:** RFP requires specific experience (type, years, technology) that isn't clearly listed in the company profile.
    *   **Scope Challenges:** The RFP scope seems significantly broader than the company's stated services or typical project size (infer cautiously if possible).
    *   **Compliance/Document Gaps:** Missing mandatory certifications, licenses, specific forms, or insurance types/limits mentioned in the RFP but not confirmed in the profile.
    *   **Resource Constraints (Implied):** Very tight deadlines, unusually complex requirements mentioned in the RFP.
    *   **Ambiguity:** Unclear or contradictory requirements in the RFP itself that could lead to misunderstandings or disputes.
    *   **Financial/Contractual Risks:** Mentions of specific penalties, non-standard payment terms, or requirements for financial proof not addressed in the profile (e.g., missing Bank Letter of Creditworthiness if required).
2.  **Generate Risk Items:** For each significant potential risk identified, create a `RiskItem` object.
    *   `risk_description`: Clearly state the risk (e.g., "RFP requires E&O insurance of $1M, not listed in company profile.", "Company lacks stated experience in specific software 'XYZ' required by RFP.", "Mandatory Form 'HSD Form A' required by RFP, not mentioned in profile.", "Potential scope mismatch: RFP requires audit *services*, company provides audit *personnel* via staffing.").
    *   `severity`: Assign "High", "Medium", or "Low".
        *   High: Potential disqualifier, major gap (e.g., missing mandatory license, core scope mismatch).
        *   Medium: Significant gap requiring action (e.g., missing non-critical insurance, lack of specific niche experience).
        *   Low: Manageable challenge (e.g., need to format proposal carefully, ambiguity needing clarification).
    *   `mitigation_strategy`: Suggest a practical action the company could take (e.g., "Obtain required E&O insurance before bid submission.", "Highlight specific project experience of 'James Wu, Security Auditor'.", "Request clarification on required forms from issuer.", "Clearly state in proposal that services are fulfilled via providing qualified personnel.").
3.  **Compile Report:** Collect all generated `RiskItem` objects into the `identified_risks` list within the `RiskAnalysisReport` JSON structure. If no significant risks are identified based on the text comparison, return an empty list: `"identified_risks": []`.

**Output Format:** Return *only* the valid JSON object conforming to the `RiskAnalysisReport` schema. Do not include any other text, comments, or markdown formatting outside the JSON structure.

```json
{{
  "identified_risks": [
    {{
      "risk_description": "Description of potential risk 1",
      "severity": "High" | "Medium" | "Low",
      "mitigation_strategy": "Suggested action for risk 1"
    }},
    {{
      "risk_description": "Description of potential risk 2",
      "severity": "High" | "Medium" | "Low",
      "mitigation_strategy": "Suggested action for risk 2"
    }}
    // ... more risks ...
  ]
}}
```
"""

RISK_ANALYSIS_RAG_PROMPT = """biased clauses, unfavorable terms, or other risks that could impact the company's ability to fulfill the contract. Identify any potential risks related to the company's ability to meet the RFP requirements, including financial, operational, or reputational risks."""
