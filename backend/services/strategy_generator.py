def generate_strategy_report(insights):

    report = []

    report.append("Business Performance Summary")

    for i in insights:
        report.append(f"- {i}")

    report.append("")
    report.append("Recommended Strategic Actions")

    report.append(
        "• Optimize marketing campaigns based on high ROI channels"
    )

    report.append(
        "• Improve customer retention and reduce churn risk"
    )

    report.append(
        "• Test new acquisition channels for growth"
    )

    report.append(
        "• Invest more in campaigns with strong conversion rates"
    )

    return report