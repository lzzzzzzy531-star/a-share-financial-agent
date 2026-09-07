import pandas as pd
import streamlit as st

from app.dashboard.renderers.common import (
    format_amount,
)


# =========================================================
# DCF DataFrame Builder
# =========================================================

def build_dcf_dataframe(
    forecast_series: list
) -> pd.DataFrame:
    """
    将 DCF 预测序列转换为 DataFrame。
    """

    if not isinstance(
        forecast_series,
        list,
    ):
        return pd.DataFrame()

    if not forecast_series:
        return pd.DataFrame()

    df = pd.DataFrame(
        forecast_series
    )

    rename_mapping = {
        "year":
            "年份",

        "projected_fcf":
            "预测自由现金流",

        "present_value":
            "折现后自由现金流",
    }

    return df.rename(
        columns=rename_mapping
    )


# =========================================================
# Valuation Dashboard Renderer
# =========================================================

def render_valuation_dashboard(
    valuation_data: dict
):
    """
    渲染 DCF Valuation Dashboard。
    """

    if not isinstance(
        valuation_data,
        dict,
    ):
        st.info(
            "当前查询没有生成估值数据。"
        )
        return

    if valuation_data.get(
        "status"
    ) == "failed":
        st.subheader(
            "DCF 估值"
        )
        st.warning(
            valuation_data.get(
                "error"
            )
            or "估值数据构建失败。"
        )
        if valuation_data.get(
            "report"
        ):
            st.markdown(
                valuation_data.get(
                    "report"
                )
            )
        return

    dcf_data = (
        valuation_data.get(
            "dcf"
        )
    )

    if not isinstance(
        dcf_data,
        dict,
    ):
        st.info(
            "当前没有可展示的 DCF 数据。"
        )
        return

    st.subheader(
        "DCF 估值"
    )

    # =========================================
    # Inputs
    # =========================================

    inputs = (
        dcf_data.get(
            "inputs",
            {}
        )
    )

    st.markdown(
        "#### DCF 假设参数"
    )

    input_columns = (
        st.columns(
            5
        )
    )

    free_cash_flow = (
        inputs.get(
            "free_cash_flow"
        )
    )

    growth_rate = (
        inputs.get(
            "growth_rate"
        )
    )

    discount_rate = (
        inputs.get(
            "discount_rate"
        )
    )

    terminal_growth_rate = (
        inputs.get(
            "terminal_growth_rate"
        )
    )

    forecast_years = (
        inputs.get(
            "forecast_years"
        )
    )

    with input_columns[0]:

        st.metric(
            label="自由现金流",
            value=format_amount(
                free_cash_flow
            ),
        )

    with input_columns[1]:

        st.metric(
            label="增长率",
            value=(
                f"{growth_rate * 100:.2f}%"
                if growth_rate is not None
                else "暂无数据"
            ),
        )

    with input_columns[2]:

        st.metric(
            label="折现率",
            value=(
                f"{discount_rate * 100:.2f}%"
                if discount_rate is not None
                else "暂无数据"
            ),
        )

    with input_columns[3]:

        st.metric(
            label="永续增长率",
            value=(
                f"{terminal_growth_rate * 100:.2f}%"
                if terminal_growth_rate is not None
                else "暂无数据"
            ),
        )

    with input_columns[4]:

        st.metric(
            label="预测年数",
            value=(
                f"{forecast_years} 年"
                if forecast_years is not None
                else "暂无数据"
            ),
        )

    # =========================================
    # Results
    # =========================================

    st.markdown(
        "#### 估值结果"
    )

    result_columns = (
        st.columns(
            4
        )
    )

    result_metrics = [
        (
            "预测期现金流现值",
            "forecast_pv",
        ),
        (
            "终值",
            "terminal_value",
        ),
        (
            "终值现值",
            "terminal_present_value",
        ),
        (
            "企业价值",
            "enterprise_value",
        ),
    ]

    for column, (
        label,
        key,
    ) in zip(
        result_columns,
        result_metrics,
    ):

        with column:

            st.metric(
                label=label,
                value=format_amount(
                    dcf_data.get(
                        key
                    )
                ),
            )

    # =========================================
    # Forecast Chart
    # =========================================

    st.markdown(
        "### 预测自由现金流与折现后现金流"
    )

    forecast_series = (
        dcf_data.get(
            "forecast_series",
            []
        )
    )

    dcf_df = (
        build_dcf_dataframe(
            forecast_series
        )
    )

    if dcf_df.empty:

        st.info(
            "暂无 DCF 预测现金流序列。"
        )

    else:

        chart_columns = [
            column
            for column in [
                "预测自由现金流",
                "折现后自由现金流",
            ]
            if column in dcf_df.columns
        ]

        st.line_chart(
            data=dcf_df,
            x="年份",
            y=chart_columns,
            x_label="预测年份",
            y_label="金额（元）",
            height=420,
        )

    # =========================================
    # Forecast Table
    # =========================================

    st.markdown(
        "### DCF 预测明细"
    )

    if not dcf_df.empty:

        display_df = (
            dcf_df.copy()
        )

        for column in [
            "预测自由现金流",
            "折现后自由现金流",
        ]:

            if column in (
                display_df.columns
            ):

                display_df[
                    column
                ] = (
                    display_df[
                        column
                    ]
                    .map(
                        format_amount
                    )
                )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )

    # =========================================
    # Valuation Report
    # =========================================

    st.markdown(
        "### DCF 估值说明"
    )

    valuation_report = (
        valuation_data.get(
            "report"
        )
    )

    if valuation_report:

        st.markdown(
            valuation_report
        )

    else:

        st.info(
            "暂无估值分析报告。"
        )
