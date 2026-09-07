import streamlit as st


# =========================================================
# Report Renderers
# =========================================================

def render_synthesis_dashboard(
    synthesis_data: dict,
):
    """
    渲染 Synthesis Agent 的跨维度综合分析。
    """

    if not isinstance(
        synthesis_data,
        dict,
    ):
        st.info(
            "当前查询没有生成综合分析。"
        )
        return

    report = synthesis_data.get(
        "report"
    )

    if not report:
        st.info(
            "当前查询没有生成综合分析。"
        )
        return

    st.subheader(
        "综合分析"
    )

    st.markdown(
        report
    )


def render_final_report(
    final_report: str | None,
):
    """
    渲染最终汇总报告。
    """

    if not final_report:
        st.info(
            "当前查询没有生成最终报告。"
        )
        return

    st.subheader(
        "最终汇总报告"
    )

    st.markdown(
        final_report
    )
