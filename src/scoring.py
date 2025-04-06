import json
import os
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def calculate_compliance_score(compliance_data: dict) -> dict:
    """
    Calculates the compliance score based on the 'matches' field.

    Args:
        compliance_data (dict): The dictionary loaded from compliance_results.json.

    Returns:
        dict: A dictionary containing the score details or an error message.
    """
    if "error" in compliance_data:
        logger.error(
            f"Input compliance data contains an error: {compliance_data['error']}"
        )
        return {
            "error": f"Input compliance data indicates an error: {compliance_data['error']}",
            "score_percentage": 0,
        }

    criteria_list = compliance_data.get("compliance_criteria")
    assessment = compliance_data.get(
        "overall_eligibility_assessment", "Assessment not found."
    )

    if not criteria_list:
        # Handle cases where criteria might be missing or empty, even if no top-level error
        logger.warning(
            "Compliance data is missing the 'compliance_criteria' list or it is empty."
        )
        # Check if assessment hints at eligibility despite missing criteria (unlikely but possible)
        if "eligible" in assessment.lower() and "ineligible" not in assessment.lower():
            # Assign a default score or handle as needed if eligible despite no criteria
            logger.warning(
                "Assessment suggests eligibility but no criteria found. Assigning placeholder score."
            )
            return {
                "company_name_from_assessment": (
                    assessment.split(" appears")[0]
                    if " appears" in assessment
                    else "Unknown Company"
                ),
                "overall_eligibility_assessment": assessment,
                "total_criteria_evaluated": 0,
                "criteria_matched": 0,
                "score_percentage": 0,  # Or maybe 100 if assessment is positive? Decide your logic.
                "notes": "Eligible assessment but no criteria details found.",
            }
        else:
            return {
                "company_name_from_assessment": (
                    assessment.split(" appears")[0]
                    if " appears" in assessment
                    else "Unknown Company"
                ),
                "overall_eligibility_assessment": assessment,
                "total_criteria_evaluated": 0,
                "criteria_matched": 0,
                "score_percentage": 0,
                "notes": "No compliance criteria found to calculate score.",
            }

    total_criteria = len(criteria_list)
    matched_criteria = 0
    for item in criteria_list:
        # Check if 'matches' key exists and is True
        if item.get("matches") is True:
            matched_criteria += 1

    score_percentage = 0
    if total_criteria > 0:
        score_percentage = round((matched_criteria / total_criteria) * 100, 2)
    else:
        logger.warning("No criteria found in the list, score is 0.")

    # Attempt to extract company name from assessment for inclusion
    company_name = "Unknown Company"
    if " appears" in assessment:
        company_name = assessment.split(" appears")[0].strip()

    logger.info(
        f"Score calculated: {matched_criteria}/{total_criteria} criteria matched ({score_percentage}%)"
    )

    return {
        "company_name_from_assessment": company_name,
        "overall_eligibility_assessment": assessment,
        "total_criteria_evaluated": total_criteria,
        "criteria_matched": matched_criteria,
        "score_percentage": score_percentage,
    }
