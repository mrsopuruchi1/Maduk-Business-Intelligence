from modules.report import ReportGenerator


def generate_report(client_id, kpis, advice, currency):
    report = ReportGenerator()
    return report.generate(
        client_id=client_id,
        kpis=kpis,
        advice=advice,
        currency=currency
    )