def recommend_action(customer, risk_level, reasons):
    """
    Simple rule-based recommendation engine.
    Easy to extend later or replace with AI.
    """

    if risk_level == "high":
        if customer.monthly_spend and customer.monthly_spend > 50:
            return "Offer personal outreach or onboarding call"
        if "Very low feature usage" in reasons:
            return "Send feature education email"
        return "Offer retention discount"

    if risk_level == "medium":
        if customer.monthly_spend == 0:
            return "Encourage upgrade with limited-time offer"
        return "Send engagement reminder"

    return "No action needed"
