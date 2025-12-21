import plotly.graph_objs as go


def risk_level_distribution(predictions):
    levels = {"low": 0, "medium": 0, "high": 0}
    for p in predictions:
        levels[p.risk_level] += 1

    fig = go.Figure(
        data=[
            go.Bar(
                x=list(levels.keys()),
                y=list(levels.values()),
                marker_color=["#28a745", "#ffc107", "#dc3545"],
            )
        ]
    )

    fig.update_layout(
        title="Churn Risk Distribution",
        xaxis_title="Risk Level",
        yaxis_title="Number of Customers",
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    return fig.to_html(full_html=False)


def revenue_at_risk_chart(predictions):
    labels = []
    values = []

    for p in predictions:
        if p.revenue_at_risk > 0:
            labels.append(str(p.customer.external_id))
            values.append(p.revenue_at_risk)

    if not values:
        return None

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
            )
        ]
    )

    fig.update_layout(
        title="Revenue at Risk by Customer",
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    return fig.to_html(full_html=False)


def trend_overview(predictions):
    trends = {"new": 0, "improving": 0, "stable": 0, "worsening": 0}

    for p in predictions:
        trends[p.risk_trend] += 1

    fig = go.Figure(
        data=[
            go.Bar(
                x=list(trends.keys()),
                y=list(trends.values()),
                marker_color="#17a2b8",
            )
        ]
    )

    fig.update_layout(
        title="Risk Trend Overview",
        xaxis_title="Trend",
        yaxis_title="Customers",
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    return fig.to_html(full_html=False)
