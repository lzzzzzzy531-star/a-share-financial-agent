import pandas as pd
import streamlit as st


from app.dashboard.renderers.common import (
    format_kpi,
)


# =========================================================
# Financial Dashboard Renderer
# =========================================================

# =========================================================
# Financial History DataFrame
# =========================================================

def build_financial_history_dataframe(
    history_series: list
) -> pd.DataFrame:
    """
    将 Dashboard Financial History
    转换为 Pandas DataFrame。
    """

    if not isinstance(
        history_series,
        list,
    ):
        return pd.DataFrame()

    if not history_series:
        return pd.DataFrame()

    df = pd.DataFrame(
        history_series
    )

    rename_mapping = {

        "period":
            "报告期",

        "eps":
            "每股收益",

        "roe":
            "ROE",

        "weighted_roe":
            "加权ROE",

        "gross_margin":
            "销售毛利率",

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

    df = df.rename(
        columns=rename_mapping
    )

    if "报告期" in df.columns:

        df["报告期"] = (
            pd.to_datetime(
                df["报告期"],
                errors="coerce",
            )
        )

    return df

def render_financial_dashboard(
    financial_data: dict
):
    """
    渲染 Financial Dashboard。
    """

    if not isinstance(
        financial_data,
        dict,
    ):
        st.info(
            "当前查询没有生成财务数据。"
        )
        return

    if financial_data.get(
        "status"
    ) == "failed":
        st.subheader(
            "财务指标"
        )
        st.warning(
            financial_data.get(
                "error"
            )
            or "财务数据构建失败。"
        )
        if financial_data.get(
            "report"
        ):
            st.markdown(
                financial_data.get(
                    "report"
                )
            )
        return

    report_period = (
        financial_data.get(
            "report_period"
        )
    )

    st.subheader(
        "财务指标"
    )

    if report_period:

        st.caption(
            f"报告期：{report_period}"
        )

    kpis = (
        financial_data.get(
            "kpis",
            {}
        )
    )

    # =========================================
    # 盈利能力
    # =========================================

    st.markdown(
        "#### 盈利能力"
    )

    row1 = st.columns(
        5
    )

    metrics = [
        (
            "每股收益 EPS",
            "eps",
        ),
        (
            "ROE",
            "roe",
        ),
        (
            "加权 ROE",
            "weighted_roe",
        ),
        (
            "销售净利率",
            "net_margin",
        ),
        (
            "总资产净利润率",
            "roa",
        ),
    ]

    for column, (
        label,
        key,
    ) in zip(
        row1,
        metrics,
    ):

        with column:

            st.metric(
                label=label,
                value=format_kpi(
                    kpis.get(
                        key
                    )
                ),
            )

    # =========================================
    # 成长能力
    # =========================================

    st.markdown(
        "#### 成长能力"
    )

    row2 = st.columns(
        3
    )

    metrics = [
        (
            "主营业务收入增长率",
            "revenue_growth",
        ),
        (
            "净利润增长率",
            "net_profit_growth",
        ),
        (
            "净资产增长率",
            "net_asset_growth",
        ),
    ]

    for column, (
        label,
        key,
    ) in zip(
        row2,
        metrics,
    ):

        with column:

            st.metric(
                label=label,
                value=format_kpi(
                    kpis.get(
                        key
                    )
                ),
            )

    # =========================================
    # 运营效率
    # =========================================

    st.markdown(
        "#### 运营效率"
    )

    row3 = st.columns(
        3
    )

    metrics = [
        (
            "应收账款周转率",
            "receivable_turnover",
        ),
        (
            "存货周转率",
            "inventory_turnover",
        ),
        (
            "总资产周转率",
            "asset_turnover",
        ),
    ]

    for column, (
        label,
        key,
    ) in zip(
        row3,
        metrics,
    ):

        with column:

            st.metric(
                label=label,
                value=format_kpi(
                    kpis.get(
                        key
                    )
                ),
            )

    # =========================================
    # 偿债能力与现金流
    # =========================================

    st.markdown(
        "#### 偿债能力与现金流"
    )

    row4 = st.columns(
        4
    )

    metrics = [
        (
            "流动比率",
            "current_ratio",
        ),
        (
            "速动比率",
            "quick_ratio",
        ),
        (
            "资产负债率",
            "debt_ratio",
        ),
        (
            "每股经营现金流",
            "operating_cash_flow_per_share",
        ),
    ]

    for column, (
        label,
        key,
    ) in zip(
        row4,
        metrics,
    ):

        with column:

            st.metric(
                label=label,
                value=format_kpi(
                    kpis.get(
                        key
                    )
                ),
            )

    # =========================================
    # Historical Financial Data
    # =========================================

    history_series = (
        financial_data.get(
            "history_series",
            []
        )
    )

    history_df = (
        build_financial_history_dataframe(
            history_series
        )
    )

    if not history_df.empty:

        st.markdown(
            "---"
        )

        st.markdown(
            "### 历史财务趋势"
        )

        # =====================================
        # Profitability
        # =====================================

        profitability_columns = [
            column
            for column in [
                "ROE",
                "加权ROE",
                "销售净利率",
                "总资产净利润率",
            ]
            if column in history_df.columns
        ]

        if profitability_columns:

            st.markdown(
                "#### 盈利能力趋势"
            )

            st.line_chart(
                data=history_df,
                x="报告期",
                y=profitability_columns,
                x_label="报告期",
                y_label="百分比（%）",
                height=420,
            )

        # =====================================
        # Growth
        # =====================================

        growth_columns = [
            column
            for column in [
                "主营业务收入增长率",
                "净利润增长率",
                "净资产增长率",
            ]
            if column in history_df.columns
        ]

        if growth_columns:

            st.markdown(
                "#### 成长能力趋势"
            )

            st.line_chart(
                data=history_df,
                x="报告期",
                y=growth_columns,
                x_label="报告期",
                y_label="增长率（%）",
                height=420,
            )

        # =====================================
        # Solvency
        # =====================================

        solvency_columns = [
            column
            for column in [
                "资产负债率",
            ]
            if column in history_df.columns
        ]

        if solvency_columns:

            st.markdown(
                "#### 资产负债率趋势"
            )

            st.line_chart(
                data=history_df,
                x="报告期",
                y=solvency_columns,
                x_label="报告期",
                y_label="百分比（%）",
                height=360,
            )

        # =====================================
        # Liquidity
        # =====================================

        liquidity_columns = [
            column
            for column in [
                "流动比率",
                "速动比率",
            ]
            if column in history_df.columns
        ]

        if liquidity_columns:

            st.markdown(
                "#### 流动性指标趋势"
            )

            st.line_chart(
                data=history_df,
                x="报告期",
                y=liquidity_columns,
                x_label="报告期",
                y_label="比率",
                height=360,
            )

    # =========================================
    # Financial Report
    # =========================================

    st.markdown(
        "### 财务分析报告"
    )

    financial_report = (
        financial_data.get(
            "report"
        )
    )

    if financial_report:

        st.markdown(
            financial_report
        )

    else:

        st.info(
            "暂无财务分析报告。"
        )
