import streamlit as st

from app.multi_agent import (
    multi_agent,
)

from app.dashboard.renderers import (
    render_market_dashboard,
    render_financial_dashboard,
    render_valuation_dashboard,
    render_synthesis_dashboard,
    render_final_report,
)

from app.runtime import log_exception


# =========================================================
# 1. Page Config
# =========================================================

st.set_page_config(
    page_title="A股多智能体分析系统",
    page_icon="📊",
    layout="wide",
)


# =========================================================
# 2. Header Renderer
# =========================================================

def render_header(
    dashboard_data: dict
):
    """
    渲染 Dashboard 顶部基础信息。
    """

    meta = (
        dashboard_data.get(
            "meta",
            {}
        )
    )

    stock_code = (
        meta.get(
            "stock_code"
        )
    )

    data_date = (
        meta.get(
            "data_date"
        )
    )

    if not (
        stock_code
        or data_date
    ):
        return

    st.markdown(
        "---"
    )

    columns = (
        st.columns(
            2
        )
    )

    with columns[0]:

        st.write(
            "**股票代码：**",
            stock_code
            or "暂无"
        )

    with columns[1]:

        st.write(
            "**数据截止日期：**",
            data_date
            or "暂无"
        )


# =========================================================
# 3. Dashboard Renderer
# =========================================================

def render_dashboard(
    dashboard_data: dict
):
    """
    根据 Dashboard Schema
    渲染各个业务模块。
    """

    render_header(
        dashboard_data
    )

    market_data = (
        dashboard_data.get(
            "market"
        )
    )

    financial_data = (
        dashboard_data.get(
            "financial"
        )
    )

    valuation_data = (
        dashboard_data.get(
            "valuation"
        )
    )

    synthesis_data = (
        dashboard_data.get(
            "synthesis"
        )
    )

    final_report = (
        dashboard_data.get(
            "final_report"
        )
    )

    # =========================================
    # Market
    # =========================================

    if market_data is not None:

        st.markdown(
            "---"
        )

        render_market_dashboard(
            market_data
        )

    # =========================================
    # Financial
    # =========================================

    if financial_data is not None:

        st.markdown(
            "---"
        )

        render_financial_dashboard(
            financial_data
        )

    # =========================================
    # Valuation
    # =========================================

    if valuation_data is not None:

        st.markdown(
            "---"
        )

        render_valuation_dashboard(
            valuation_data
        )

    # =========================================
    # Synthesis
    # =========================================

    if synthesis_data is not None:

        st.markdown(
            "---"
        )

        render_synthesis_dashboard(
            synthesis_data
        )

    # =========================================
    # Final Report
    # =========================================

    if final_report:

        st.markdown(
            "---"
        )

        render_final_report(
            final_report
        )


# =========================================================
# 4. Main App
# =========================================================

def main():

    st.title(
        "📊 A股多智能体分析系统"
    )

    st.caption(
        "市场分析 · 财务分析 · 估值分析 · 综合报告"
    )

    # =========================================
    # User Input
    # =========================================

    user_query = (
        st.text_area(
            label="请输入分析问题",
            value=(
                "请综合分析贵州茅台的市场表现和最新财务指标，"
                "并以自由现金流1亿元、增长率5%、折现率10%、"
                "永续增长率2%、预测5年进行DCF估值。"
            ),
            height=120,
        )
    )

    analyze_button = (
        st.button(
            "开始分析",
            type="primary",
        )
    )

    # =========================================
    # Run Multi-Agent
    # =========================================

    if analyze_button:

        if not user_query.strip():

            st.warning(
                "请输入分析问题。"
            )

            return

        with st.spinner(
            "多智能体正在分析..."
        ):

            try:

                result = (
                    multi_agent.invoke({
                        "user_query":
                            user_query
                    })
                )

            except Exception as error:

                log_exception(
                    "Streamlit App",
                    error,
                    "多智能体分析失败",
                )

                st.error(
                    "多智能体分析失败，请稍后重试或查看后台日志。"
                )

                return

        st.session_state[
            "last_dashboard_result"
        ] = result

        dashboard_data = (
            result.get(
                "dashboard_data"
            )
        )

        if not isinstance(
            dashboard_data,
            dict,
        ):

            st.error(
                "未生成 dashboard_data。"
            )

            return

        render_dashboard(
            dashboard_data
        )

    elif (
        "last_dashboard_result"
        in st.session_state
    ):

        result = st.session_state[
            "last_dashboard_result"
        ]

        dashboard_data = (
            result.get(
                "dashboard_data"
            )
        )

        if isinstance(
            dashboard_data,
            dict,
        ):

            render_dashboard(
                dashboard_data
            )


# =========================================================
# 5. Entry Point
# =========================================================

if __name__ == "__main__":
    main()
