from typing import TypedDict, List


class AnalysisState(
    TypedDict,
    total=False,
):
    user_query: str

    requested_agents: List[str]

    stock_info: dict

    market_data: dict
    market_report: str

    financial_data: dict
    financial_trend: dict
    financial_trend_report: str
    financial_report: str

    valuation_data: dict
    valuation_report: str

    synthesis_context: dict
    synthesis_report: str

    final_report: str
    dashboard_data: dict