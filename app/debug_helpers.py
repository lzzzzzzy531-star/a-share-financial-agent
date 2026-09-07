from typing import Any

from app.runtime import (
    log_section,
    log_summary,
    summarize_for_log,
)


def log_series_edges(
    component: str,
    label: str,
    series: list,
    edge_count: int = 2,
) -> None:
    log_summary(
        component,
        f"{label}长度",
        len(series),
    )

    if not series:
        return

    log_summary(
        component,
        f"{label}前{edge_count}条",
        series[:edge_count],
    )

    log_summary(
        component,
        f"{label}后{edge_count}条",
        series[-edge_count:],
    )


def log_market_agent_smoke_result(
    result: dict[str, Any],
) -> None:
    log_section(
        "Market Smoke",
        "REPORT",
    )
    log_summary(
        "Market Smoke",
        "最终回答",
        result["messages"][-1].content,
    )

    market_data = result.get("market_data") or {}
    log_section(
        "Market Smoke",
        "DATA",
    )
    log_summary(
        "Market Smoke",
        "market_data 已生成",
        bool(market_data),
    )
    log_series_edges(
        "Market Smoke",
        "价格序列",
        market_data.get("价格序列", []),
    )


def log_financial_agent_smoke_result(
    result: dict[str, Any],
) -> None:
    financial_data = result.get("financial_data") or {}
    history_series = financial_data.get("财务历史序列", [])

    log_section(
        "Financial Smoke",
        "DATA",
    )
    log_summary(
        "Financial Smoke",
        "financial_data 已生成",
        bool(financial_data),
    )
    log_summary(
        "Financial Smoke",
        "股票代码",
        financial_data.get("股票代码"),
    )
    log_summary(
        "Financial Smoke",
        "最新报告期",
        financial_data.get("报告期"),
    )
    log_series_edges(
        "Financial Smoke",
        "财务历史序列",
        history_series,
        edge_count=1,
    )


def log_valuation_agent_smoke_result(
    result: dict[str, Any],
) -> None:
    log_section(
        "Valuation Smoke",
        "REPORT",
    )
    log_summary(
        "Valuation Smoke",
        "最终回答",
        result["messages"][-1].content,
    )
    log_summary(
        "Valuation Smoke",
        "valuation_data",
        result.get("valuation_data"),
    )


def log_dashboard_builder_smoke_result(
    dashboard_data: dict[str, Any],
) -> None:
    market = dashboard_data.get("market") or {}

    log_section(
        "Dashboard Builder Smoke",
        "SUMMARY",
    )
    log_summary(
        "Dashboard Builder Smoke",
        "dashboard_data",
        dashboard_data,
    )
    log_series_edges(
        "Dashboard Builder Smoke",
        "price_series",
        market.get("price_series", []),
        edge_count=1,
    )
    log_summary(
        "Dashboard Builder Smoke",
        "latest_close KPI",
        market.get("kpis", {}).get("latest_close"),
    )


def log_financial_history_smoke_result(
    result: dict[str, Any],
    safe_result: dict[str, Any],
) -> None:
    log_section(
        "Financial History Smoke",
        "RAW",
    )
    log_summary(
        "Financial History Smoke",
        "股票代码",
        result.get("股票代码"),
    )
    log_summary(
        "Financial History Smoke",
        "实际报告期数量",
        result.get("实际报告期数量"),
    )
    log_series_edges(
        "Financial History Smoke",
        "财务历史序列",
        result.get("财务历史序列", []),
    )

    log_section(
        "Financial History Smoke",
        "SANITIZED",
    )
    log_summary(
        "Financial History Smoke",
        "安全结果",
        summarize_for_log(safe_result),
    )
    log_series_edges(
        "Financial History Smoke",
        "安全历史序列",
        safe_result.get("财务历史序列", []),
        edge_count=1,
    )


def log_multi_agent_smoke_result(
    result: dict[str, Any],
) -> None:
    financial_data = result.get("financial_data") or {}
    financial_trend = result.get("financial_trend") or {}
    dashboard_data = result.get("dashboard_data") or {}
    financial_dashboard = dashboard_data.get("financial") or {}
    market_dashboard = dashboard_data.get("market") or {}
    valuation_dashboard = dashboard_data.get("valuation") or {}
    synthesis_dashboard = dashboard_data.get("synthesis") or {}

    log_section(
        "Multi Agent Smoke",
        "FINAL STATE",
    )
    log_summary(
        "Multi Agent Smoke",
        "FINAL STATE KEYS",
        list(result.keys()),
    )
    log_summary(
        "Multi Agent Smoke",
        "财务历史序列长度",
        len(financial_data.get("财务历史序列", [])),
    )
    log_summary(
        "Multi Agent Smoke",
        "Financial Trend 状态",
        financial_trend.get("状态"),
    )
    log_summary(
        "Multi Agent Smoke",
        "Dashboard history_series 长度",
        len(financial_dashboard.get("history_series", [])),
    )
    log_summary(
        "Multi Agent Smoke",
        "Market price_series 长度",
        len(market_dashboard.get("price_series", [])),
    )
    log_summary(
        "Multi Agent Smoke",
        "DCF forecast_series 长度",
        len(
            valuation_dashboard
            .get("dcf", {})
            .get("forecast_series", [])
        ),
    )
    log_summary(
        "Multi Agent Smoke",
        "Synthesis Dashboard Report 是否存在",
        bool(synthesis_dashboard.get("report")),
    )
    log_summary(
        "Multi Agent Smoke",
        "Final Report 是否存在",
        bool(dashboard_data.get("final_report")),
    )

    metric_trends = financial_trend.get("指标趋势", {})
    log_section(
        "Multi Agent Smoke",
        "FINANCIAL TREND",
    )
    log_summary(
        "Multi Agent Smoke",
        "趋势摘要",
        {
            "最新报告期": financial_trend.get("最新报告期"),
            "去年同期报告期": financial_trend.get("去年同期报告期"),
            "指标数量": len(metric_trends),
        },
    )

    log_section(
        "Multi Agent Smoke",
        "SYNTHESIS",
    )
    log_summary(
        "Multi Agent Smoke",
        "可用模块数量",
        (result.get("synthesis_context") or {}).get("可用模块数量"),
    )
    log_summary(
        "Multi Agent Smoke",
        "综合模块",
        list(
            (result.get("synthesis_context") or {})
            .get("模块", {})
            .keys()
        ),
    )
    log_summary(
        "Multi Agent Smoke",
        "综合报告存在",
        bool(result.get("synthesis_report")),
    )


def log_financial_trend_engine_smoke_result(
    result: dict[str, Any],
) -> None:
    metric_trends = result.get("指标趋势", {})

    log_section(
        "Financial Trend Smoke",
        "ENGINE",
    )
    log_summary(
        "Financial Trend Smoke",
        "状态",
        result.get("状态"),
    )
    log_summary(
        "Financial Trend Smoke",
        "最新报告期",
        result.get("最新报告期"),
    )
    log_summary(
        "Financial Trend Smoke",
        "去年同期报告期",
        result.get("去年同期报告期"),
    )
    log_summary(
        "Financial Trend Smoke",
        "指标数量",
        len(metric_trends),
    )
    log_summary(
        "Financial Trend Smoke",
        "指标趋势",
        metric_trends,
    )
