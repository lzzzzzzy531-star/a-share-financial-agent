import pandas as pd
import streamlit as st

from app.dashboard.renderers.common import (
    format_kpi,
)


# =========================================================
# Market DataFrame Builder
# =========================================================

def build_market_dataframe(
    price_series: list
) -> pd.DataFrame:
    """
    将市场价格序列转换为 Pandas DataFrame。
    """

    if not isinstance(
        price_series,
        list,
    ):
        return pd.DataFrame()

    if not price_series:
        return pd.DataFrame()

    df = pd.DataFrame(
        price_series
    )

    rename_mapping = {
        "date":
            "日期",

        "close":
            "收盘价",

        "ma20":
            "MA20",

        "ma60":
            "MA60",
    }

    df = df.rename(
        columns=rename_mapping
    )

    if "日期" in df.columns:

        df["日期"] = (
            pd.to_datetime(
                df["日期"],
                errors="coerce",
            )
        )

    return df


# =========================================================
# Market Dashboard Renderer
# =========================================================

def render_market_dashboard(
    market_data: dict
):
    """
    渲染 Market Dashboard。
    """

    if not isinstance(
        market_data,
        dict,
    ):
        st.info(
            "当前查询没有生成市场数据。"
        )
        return

    if market_data.get(
        "status"
    ) == "failed":
        st.subheader(
            "市场表现"
        )
        st.warning(
            market_data.get(
                "error"
            )
            or "市场数据构建失败。"
        )
        if market_data.get(
            "report"
        ):
            st.markdown(
                market_data.get(
                    "report"
                )
            )
        return

    data_date = (
        market_data.get(
            "data_date"
        )
    )

    trading_days = (
        market_data.get(
            "trading_days"
        )
    )

    price_adjustment = (
        market_data.get(
            "price_adjustment"
        )
    )

    st.subheader(
        "市场表现"
    )

    info_text = []

    if data_date:
        info_text.append(
            f"数据截止日期：{data_date}"
        )

    if trading_days:
        info_text.append(
            f"交易日数量：{trading_days}"
        )

    if price_adjustment:
        info_text.append(
            f"价格口径：{price_adjustment}"
        )

    if info_text:

        st.caption(
            " ｜ ".join(
                info_text
            )
        )

    # =========================================
    # KPI
    # =========================================

    kpis = (
        market_data.get(
            "kpis",
            {}
        )
    )

    row1 = st.columns(
        5
    )

    with row1[0]:

        st.metric(
            label="最新收盘价",
            value=format_kpi(
                kpis.get(
                    "latest_close"
                )
            ),
        )

    with row1[1]:

        st.metric(
            label="近20日收益率",
            value=format_kpi(
                kpis.get(
                    "return_20d"
                )
            ),
        )

    with row1[2]:

        st.metric(
            label="近60日收益率",
            value=format_kpi(
                kpis.get(
                    "return_60d"
                )
            ),
        )

    with row1[3]:

        st.metric(
            label="年化波动率",
            value=format_kpi(
                kpis.get(
                    "annualized_volatility"
                )
            ),
        )

    with row1[4]:

        st.metric(
            label="区间最大回撤",
            value=format_kpi(
                kpis.get(
                    "max_drawdown"
                )
            ),
        )

    # =========================================
    # Price Chart
    # =========================================

    st.markdown(
        "### 收盘价与移动均线"
    )

    price_series = (
        market_data.get(
            "price_series",
            []
        )
    )

    price_df = (
        build_market_dataframe(
            price_series
        )
    )

    if price_df.empty:

        st.info(
            "暂无价格时间序列数据。"
        )

    else:

        chart_columns = []

        for column in [
            "收盘价",
            "MA20",
            "MA60",
        ]:

            if column in (
                price_df.columns
            ):

                chart_columns.append(
                    column
                )

        st.line_chart(
            data=price_df,
            x="日期",
            y=chart_columns,
            x_label="日期",
            y_label="价格（元）",
            height=450,
        )

    # =========================================
    # Market Report
    # =========================================

    st.markdown(
        "### 市场分析报告"
    )

    market_report = (
        market_data.get(
            "report"
        )
    )

    if market_report:

        st.markdown(
            market_report
        )

    else:

        st.info(
            "暂无市场分析报告。"
        )
