"""Risk scoring for company-level audit results."""
from typing import List

from ..utils.datamodel import AuditAlert, CompanyAuditResult


SEVERITY_POINTS = {
    'high': 3,
    'medium': 2,
    'low': 1,
}


def _risk_level_from_score(score: int) -> str:
    """Map numeric risk score to risk level."""
    if score >= 8:
        return 'critical'
    if score >= 5:
        return 'high'
    if score >= 2:
        return 'medium'
    return 'low'


def calculate_risk_scores(company_results: List[CompanyAuditResult],
                          alerts: List[AuditAlert]) -> List[CompanyAuditResult]:
    """Calculate risk scores and levels for each company based on alerts."""
    company_map = {cr.company_name: cr for cr in company_results}

    for alert in alerts:
        points = SEVERITY_POINTS.get(alert.severity, 1)
        for company in alert.affected_companies:
            if company in company_map:
                company_map[company].risk_score += points

    for cr in company_results:
        cr.risk_level = _risk_level_from_score(cr.risk_score)

    return company_results
