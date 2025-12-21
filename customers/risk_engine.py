from datetime import date


def days_since(d):
    if not d:
        return 999
    return (date.today() - d).days


def calculate_churn_risk(customer):
    """
    Rule-based, explainable churn scoring.
    Returns: (score, level, reasons)
    """

    score = 0.0
    reasons = []

    # 1. Inactivity
    inactivity_days = days_since(customer.last_active_date)
    if inactivity_days > 30:
        score += 0.5
        reasons.append("Inactive for more than 30 days")
    elif inactivity_days > 14:
        score += 0.3
        reasons.append("Inactive for more than 14 days")

    # 2. Low feature usage
    if customer.feature_usage_score is not None:
        if customer.feature_usage_score < 20:
            score += 0.3
            reasons.append("Very low feature usage")
        elif customer.feature_usage_score < 40:
            score += 0.15
            reasons.append("Low feature usage")

    # 3. Free or low-paying plan
    if customer.monthly_spend is not None and customer.monthly_spend == 0:
        score += 0.2
        reasons.append("Free plan user")

    # 4. Very new user (early churn risk)
    if days_since(customer.signup_date) < 7:
        score += 0.1
        reasons.append("New user with early drop-off risk")

    # Cap score
    score = min(score, 1.0)

    # Risk level
    if score >= 0.7:
        level = "high"
    elif score >= 0.4:
        level = "medium"
    else:
        level = "low"

    return score, level, reasons
