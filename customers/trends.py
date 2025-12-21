from datetime import date


def analyze_trend(previous, current):
    """
    Compare previous and current risk score.
    """

    if previous is None:
        return "new", False

    diff = current - previous

    if diff > 0.1:
        return "worsening", True
    elif diff < -0.1:
        return "improving", False
    else:
        return "stable", False


def calculate_days_in_risk(first_seen_date):
    if not first_seen_date:
        return 0
    return (date.today() - first_seen_date.date()).days
