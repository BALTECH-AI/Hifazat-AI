
from typing import Literal


RiskLevel = Literal[
    "low",
    "moderate",
    "high",
    "critical",
]


def calculate_risk(
    likelihood: int,
    impact: int,
) -> tuple[int, RiskLevel]:
    """
    Calculate an ordinal MVP risk score and its corresponding level.

    Both likelihood and impact must be integers from 1 to 5.
    """

    if type(likelihood) is not int or not 1 <= likelihood <= 5:
        raise ValueError("likelihood must be an integer between 1 and 5.")

    if type(impact) is not int or not 1 <= impact <= 5:
        raise ValueError("impact must be an integer between 1 and 5.")

    risk_score = likelihood * impact

    if risk_score <= 4:
        risk_level: RiskLevel = "low"
    elif risk_score <= 9:
        risk_level = "moderate"
    elif risk_score <= 16:
        risk_level = "high"
    else:
        risk_level = "critical"

    return risk_score, risk_level
