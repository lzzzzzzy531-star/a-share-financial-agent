from typing import Any

from app.runtime import (
    build_failure_result,
    is_failure_result,
    log_exception,
)


# =========================================================
# 1. Helper Functions
# =========================================================

def get_metric_value(
    metric: Any
):
    """
    从 Agent 的标准指标结构中提取数值。

    例如：

    {
        "值": 1297.5,
        "单位": "元"
    }

    返回：

    1297.5
    """

    if isinstance(
        metric,
        dict,
    ):
        return metric.get(
            "值"
        )

    return metric


def get_metric_unit(
    metric: Any
):
    """
    从 Agent 的标准指标结构中提取单位。
    """

    if isinstance(
        metric,
        dict,
    ):
        return metric.get(
            "单位"
        )

    return None


def build_kpi(
    metric: Any
) -> dict | None:
    """
    将 Agent 内部指标转换为 Dashboard KPI 格式。

    输入：

    {
        "值": 1297.5,
        "单位": "元"
    }

    输出：

    {
        "value": 1297.5,
        "unit": "元"
    }
    """

    value = get_metric_value(
        metric
    )

    if value is None:
        return None

    return {
        "value":
            value,

        "unit":
            get_metric_unit(
                metric
            ),
    }


# =========================================================
# 2. Market Price Series Builder
# =========================================================

def build_market_price_series(
    market_data: dict
) -> list:
    """
    将 Market Agent 的价格序列转换为
    Dashboard / Chart 适合直接使用的扁平格式。

    Agent State：

    {
        "日期": "2026-09-02",
        "收盘价": {
            "值": 1297.5,
            "单位": "元"
        },
        "MA20": {
            "值": 1310.722,
            "单位": "元"
        },
        "MA60": {
            "值": 1268.11,
            "单位": "元"
        }
    }

    Dashboard：

    {
        "date": "2026-09-02",
        "close": 1297.5,
        "ma20": 1310.722,
        "ma60": 1268.11
    }
    """

    price_series = (
        market_data.get(
            "价格序列",
            []
        )
    )

    if not isinstance(
        price_series,
        list,
    ):
        return []

    dashboard_series = []

    for item in price_series:

        if not isinstance(
            item,
            dict,
        ):
            continue

        date = item.get(
            "日期"
        )

        close = get_metric_value(
            item.get(
                "收盘价"
            )
        )

        ma20 = get_metric_value(
            item.get(
                "MA20"
            )
        )

        ma60 = get_metric_value(
            item.get(
                "MA60"
            )
        )

        # 图表最基本需要：
        # 日期 + 收盘价
        if (
            date is None
            or close is None
        ):
            continue

        dashboard_series.append({
            "date":
                date,

            "close":
                close,

            "ma20":
                ma20,

            "ma60":
                ma60,
        })

    return dashboard_series


# =========================================================
# 3. Market Dashboard Builder
# =========================================================

def build_market_dashboard(
    market_data: dict | None,
    market_report: str | None,
) -> dict | None:
    """
    构建 Dashboard 的 Market 区域。
    """

    if not isinstance(
        market_data,
        dict,
    ):
        return None

    if is_failure_result(
        market_data
    ):
        return {
            "status": "failed",
            "error": market_data.get(
                "错误信息"
            ),
            "report": market_report,
        }

    # =========================================
    # KPI
    # =========================================

    kpis = {}

    kpi_mapping = {
        "latest_close":
            "最新收盘价",

        "return_20d":
            "近20日累计收益率",

        "return_60d":
            "近60日累计收益率",

        "ma20":
            "20日均价",

        "ma60":
            "60日均价",

        "price_vs_ma20":
            "当前价格相对20日均价",

        "price_vs_ma60":
            "当前价格相对60日均价",

        "annualized_volatility":
            "年化波动率",

        "max_drawdown":
            "区间最大回撤",

        "volume_ratio_20d":
            "成交量相对20日均量",
    }

    for (
        dashboard_key,
        source_key,
    ) in kpi_mapping.items():

        kpi = build_kpi(
            market_data.get(
                source_key
            )
        )

        if kpi is not None:

            kpis[
                dashboard_key
            ] = kpi

    # =========================================
    # Price Series
    # =========================================

    price_series = (
        build_market_price_series(
            market_data
        )
    )

    # =========================================
    # Market Dashboard
    # =========================================

    return {
        "data_date":
            market_data.get(
                "数据截止日期"
            ),

        "trading_days":
            market_data.get(
                "实际交易日数量"
            ),

        "price_adjustment":
            market_data.get(
                "价格口径"
            ),

        "kpis":
            kpis,

        "price_series":
            price_series,

        "report":
            market_report,
    }

# =========================================================
# Financial History Series Builder
# =========================================================

def build_financial_history_series(
    financial_data: dict
) -> list:
    """
    将 Financial Agent 的历史财务指标序列
    转换为 Dashboard 友好的扁平结构。

    Agent State:

    {
        "报告期": "2026-06-30",

        "净资产收益率ROE": {
            "值": 17.72,
            "单位": "%"
        }
    }

    Dashboard:

    {
        "period": "2026-06-30",
        "roe": 17.72
    }
    """

    if not isinstance(
        financial_data,
        dict,
    ):
        return []

    history_series = (
        financial_data.get(
            "财务历史序列",
            []
        )
    )

    if not isinstance(
        history_series,
        list,
    ):
        return []

    # =========================================
    # Agent Field -> Dashboard Field
    # =========================================

    field_mapping = {

        "每股收益":
            "eps",

        "净资产收益率ROE":
            "roe",

        "加权净资产收益率ROE":
            "weighted_roe",

        "销售毛利率":
            "gross_margin",

        "销售净利率":
            "net_margin",

        "总资产净利润率":
            "roa",

        "主营业务收入增长率":
            "revenue_growth",

        "净利润增长率":
            "net_profit_growth",

        "净资产增长率":
            "net_asset_growth",

        "应收账款周转率":
            "receivable_turnover",

        "存货周转率":
            "inventory_turnover",

        "总资产周转率":
            "asset_turnover",

        "流动比率":
            "current_ratio",

        "速动比率":
            "quick_ratio",

        "资产负债率":
            "debt_ratio",

        "每股经营现金流":
            "operating_cash_flow_per_share",
    }

    dashboard_series = []

    # =========================================
    # Flatten
    # =========================================

    for item in history_series:

        if not isinstance(
            item,
            dict,
        ):
            continue

        period = (
            item.get(
                "报告期"
            )
        )

        if period is None:
            continue

        dashboard_item = {
            "period":
                period
        }

        for (
            agent_field,
            dashboard_field,
        ) in field_mapping.items():

            metric = (
                item.get(
                    agent_field
                )
            )

            value = (
                get_metric_value(
                    metric
                )
            )

            if value is not None:

                dashboard_item[
                    dashboard_field
                ] = value

        dashboard_series.append(
            dashboard_item
        )

    return dashboard_series


# =========================================================
# 4. Financial Dashboard Builder
# =========================================================

def build_financial_dashboard(
    financial_data: dict | None,
    financial_report: str | None,
) -> dict | None:
    """
    构建 Dashboard 的 Financial 区域。

    当前阶段先转换已有财务 KPI。
    历史财务时间序列以后再加入。
    """

    if not isinstance(
        financial_data,
        dict,
    ):
        return None

    if is_failure_result(
        financial_data
    ):
        return {
            "status": "failed",
            "error": financial_data.get(
                "错误信息"
            ),
            "report": financial_report,
        }

    kpis = {}

    kpi_mapping = {
        "eps":
            "每股收益",

        "roe":
            "净资产收益率ROE",

        "weighted_roe":
            "加权净资产收益率ROE",

        "net_margin":
            "销售净利率",

        "roa":
            "总资产净利润率",

        "revenue_growth":
            "主营业务收入增长率",

        "net_profit_growth":
            "净利润增长率",

        "net_asset_growth":
            "净资产增长率",

        "receivable_turnover":
            "应收账款周转率",

        "inventory_turnover":
            "存货周转率",

        "asset_turnover":
            "总资产周转率",

        "current_ratio":
            "流动比率",

        "quick_ratio":
            "速动比率",

        "debt_ratio":
            "资产负债率",

        "operating_cash_flow_per_share":
            "每股经营现金流",
    }

    for (
        dashboard_key,
        source_key,
    ) in kpi_mapping.items():

        kpi = build_kpi(
            financial_data.get(
                source_key
            )
        )

        if kpi is not None:

            kpis[
                dashboard_key
            ] = kpi

    history_series = (
        build_financial_history_series(
            financial_data
        )
    )

    return {
    "report_period":
        financial_data.get(
            "报告期"
        ),

    "kpis":
        kpis,

    "history_series":
        history_series,

    "report":
        financial_report,
    }


# =========================================================
# 5. Valuation Dashboard Builder
# =========================================================

def build_valuation_dashboard(
    valuation_data: dict | None,
    valuation_report: str | None,
) -> dict | None:
    """
    构建 Dashboard 的 Valuation 区域。

    当前阶段主要支持 DCF。
    """

    if not isinstance(
        valuation_data,
        dict,
    ):
        return None

    if is_failure_result(
        valuation_data
    ):
        return {
            "status": "failed",
            "error": valuation_data.get(
                "错误信息"
            ),
            "report": valuation_report,
        }

    input_params = (
        valuation_data.get(
            "输入参数",
            {}
        )
    )

    projected_cash_flows = (
        valuation_data.get(
            "预测期现金流",
            []
        )
    )

    # =========================================
    # DCF Forecast Series
    # =========================================

    dcf_series = []

    if isinstance(
        projected_cash_flows,
        list,
    ):

        for item in projected_cash_flows:

            if not isinstance(
                item,
                dict,
            ):
                continue

            year = item.get(
                "年份"
            )

            projected_fcf = (
                item.get(
                    "预测自由现金流"
                )
            )

            present_value = (
                item.get(
                    "折现后自由现金流"
                )
            )

            if year is None:
                continue

            dcf_series.append({
                "year":
                    year,

                "projected_fcf":
                    projected_fcf,

                "present_value":
                    present_value,
            })

    # =========================================
    # Valuation Dashboard
    # =========================================

    return {
        "dcf": {
            "inputs": {
                "free_cash_flow":
                    input_params.get(
                        "自由现金流"
                    ),

                "growth_rate":
                    input_params.get(
                        "增长率"
                    ),

                "discount_rate":
                    input_params.get(
                        "折现率"
                    ),

                "terminal_growth_rate":
                    input_params.get(
                        "永续增长率"
                    ),

                "forecast_years":
                    input_params.get(
                        "预测年数"
                    ),
            },

            "forecast_series":
                dcf_series,

            "forecast_pv":
                valuation_data.get(
                    "预测期现金流现值合计"
                ),

            "terminal_value":
                valuation_data.get(
                    "终值"
                ),

            "terminal_present_value":
                valuation_data.get(
                    "终值现值"
                ),

            "enterprise_value":
                valuation_data.get(
                    "企业价值"
                ),
        },

        "report":
            valuation_report,
    }


# =========================================================
# 6. Main Dashboard Builder
# =========================================================

def build_dashboard_data(
    state: dict
) -> dict:
    """
    将整个 AnalysisState 转换为稳定的 Dashboard 数据。

    这里不调用：

    - LLM
    - AkShare
    - Agent
    - Tool

    只进行确定性的 Python 数据转换。
    """

    market_data = state.get(
        "market_data"
    )

    financial_data = state.get(
        "financial_data"
    )

    valuation_data = state.get(
        "valuation_data"
    )

    errors = []

    def safe_build_section(
        section_name: str,
        builder,
        **kwargs,
    ):
        try:

            return builder(
                **kwargs
            )

        except Exception as error:

            log_exception(
                "Dashboard Builder",
                error,
                section_name,
            )

            errors.append(
                build_failure_result(
                    source="Dashboard Builder",
                    stage=section_name,
                    message=(
                        f"{section_name} 构建失败。"
                    ),
                    retryable=False,
                )
            )

            return {
                "status": "failed",
                "error": (
                    f"{section_name} 构建失败。"
                ),
            }

    # =========================================
    # Meta
    # =========================================

    stock_code = None
    data_date = None

    if isinstance(
        market_data,
        dict,
    ):

        stock_code = (
            market_data.get(
                "股票代码"
            )
        )

        data_date = (
            market_data.get(
                "数据截止日期"
            )
        )

    if (
        stock_code is None
        and isinstance(
            financial_data,
            dict,
        )
    ):

        stock_code = (
            financial_data.get(
                "股票代码"
            )
        )

    dashboard_data = {
        "meta": {
            "stock_code":
                stock_code,

            "data_date":
                data_date,
        },

        "market":
            safe_build_section(
                "market",
                build_market_dashboard,
                market_data=market_data,
                market_report=state.get(
                    "market_report"
                ),
            ),

        "financial":
            safe_build_section(
                "financial",
                build_financial_dashboard,
                financial_data=financial_data,
                financial_report=state.get(
                    "financial_report"
                ),
            ),

        "valuation":
            safe_build_section(
                "valuation",
                build_valuation_dashboard,
                valuation_data=valuation_data,
                valuation_report=state.get(
                    "valuation_report"
                ),
            ),

        "synthesis": {
            "report":
                state.get(
                    "synthesis_report"
                ),
        },

        "final_report":
            state.get(
                "final_report"
            ),
    }

    if errors:

        dashboard_data[
            "errors"
        ] = errors

    return dashboard_data

# =========================================================
# 7. Local Smoke Test
# =========================================================

if __name__ == "__main__":
    from app.debug_helpers import log_dashboard_builder_smoke_result

    test_market_data = {
        "股票代码":
            "600519",

        "数据截止日期":
            "2026-09-02",

        "实际交易日数量":
            60,

        "价格口径":
            "前复权",

        "最新收盘价": {
            "值":
                1297.5,

            "单位":
                "元",
        },

        "近20日累计收益率": {
            "值":
                -0.6851,

            "单位":
                "%",
        },

        "近60日累计收益率": {
            "值":
                5.7492,

            "单位":
                "%",
        },

        "年化波动率": {
            "值":
                25.2486,

            "单位":
                "%",
        },

        "区间最大回撤": {
            "值":
                -7.4015,

            "单位":
                "%",
        },

        "价格序列": [
            {
                "日期":
                    "2026-09-01",

                "收盘价": {
                    "值":
                        1299.56,

                    "单位":
                        "元",
                },

                "MA20": {
                    "值":
                        1311.1695,

                    "单位":
                        "元",
                },

                "MA60": {
                    "值":
                        1266.9382,

                    "单位":
                        "元",
                },
            },

            {
                "日期":
                    "2026-09-02",

                "收盘价": {
                    "值":
                        1297.5,

                    "单位":
                        "元",
                },

                "MA20": {
                    "值":
                        1310.722,

                    "单位":
                        "元",
                },

                "MA60": {
                    "值":
                        1268.1138,

                    "单位":
                        "元",
                },
            },
        ],
    }

    test_state = {
        "market_data":
            test_market_data,

        "market_report":
            "这里是 Market Agent 测试报告。",

        "financial_data":
            None,

        "valuation_data":
            None,

        "synthesis_report":
            "这里是综合测试报告。",

        "final_report":
            "这里是最终测试报告。",
    }

    dashboard_data = (
        build_dashboard_data(
            test_state
        )
    )

    log_dashboard_builder_smoke_result(
        dashboard_data
    )
