from app.formatters.valuation_formatter import (
    format_dcf_report,
)

from langchain_core.messages import (
    HumanMessage,
)

from langgraph.graph import (
    StateGraph,
    END,
)

from app.state import (
    AnalysisState,
)

from app.agents.supervisor import (
    supervisor_node,
)

from app.agents.market_agent import (
    market_agent,
)

from app.agents.financial_agent import (
    financial_agent,
)

from app.agents.valuation_agent import (
    valuation_agent,
)

from app.agents.report_agent import (
    report_agent,
)

from app.dashboard.builder import (
    build_dashboard_data,
)

from app.tools import get_financial_history

from app.sanitizers.financial_sanitizer import (
    sanitize_financial_history,
)

from app.analytics.financial_trend import (
    build_financial_trend_analysis,
)

from app.analytics.synthesis_context import (
    build_synthesis_context,
)

from app.agents.synthesis_agent import (
    generate_synthesis_report,
)

from app.agents.financial_trend_agent import (
    generate_financial_trend_report,
)

from app.formatters.financial_trend_formatter import (
    format_financial_trend_report,
)

from app.runtime import (
    build_failure_result,
    is_failure_result,
    log_exception,
    log_info,
    log_section,
    log_summary,
)

# =========================================================
# 1. Helper
# =========================================================

def agent_is_requested(
    state: AnalysisState,
    agent_name: str,
) -> bool:

    requested_agents = state.get(
        "requested_agents",
        [],
    )

    return (
        agent_name
        in requested_agents
    )


# =========================================================
# 2. Market Node
# =========================================================

def market_node(
    state: AnalysisState,
):

    # ---------------------------------
    # Skip
    # ---------------------------------

    if not agent_is_requested(
        state,
        "market",
    ):

        log_info(
            "Market Agent",
            "SKIPPED",
        )

        return {}

    # ---------------------------------
    # Run
    # ---------------------------------

    log_section(
        "Market Agent",
        "RUN",
    )

    user_query = state["user_query"]

    market_task = (
        "你当前只负责原始用户问题中的"
        "市场行情与市场表现分析部分。\n"
        "忽略财务分析、DCF估值以及其他不属于"
        "Market Agent 职责的任务。\n\n"
        "原始用户问题：\n"
        f"{user_query}"
    )

    try:

        result = market_agent.invoke({
            "messages": [
                HumanMessage(
                    content=market_task
                )
            ]
        })

    except Exception as error:

        log_exception(
            "Market Node",
            error,
            "Market Agent 执行失败",
        )

        return {
            "market_report": (
                "Market Agent 执行失败，"
                "本次未生成市场分析。"
            )
        }


    market_report = (
        result["messages"][-1].content
    )


    market_data = result.get(
        "market_data"
    )


    log_info(
        "Market Agent",
        "完成",
    )


    output = {
        "market_report":
            market_report
    }


    if market_data:

        output[
            "market_data"
        ] = market_data


    return output

# =========================================================
# Financial Dashboard History Loader
# =========================================================

def ensure_financial_history(
    financial_data: dict
) -> dict:
    """
    确保 Financial Dashboard 拥有历史财务序列。

    Financial Agent 如果已经调用过
    get_financial_history，则直接复用。

    如果没有调用，则由 Python 编排层
    确定性补充最近12期历史财务数据。
    """

    if not isinstance(
        financial_data,
        dict,
    ):
        return financial_data

    # =========================================
    # 已经存在历史数据 → 不重复调用
    # =========================================

    existing_history = (
        financial_data.get(
            "财务历史序列"
        )
    )

    if isinstance(
        existing_history,
        list,
    ) and existing_history:
        log_info(
            "Financial History",
            "已存在，跳过重复加载",
        )

        return financial_data

    # =========================================
    # 获取股票代码
    # =========================================

    stock_code = (
        financial_data.get(
            "股票代码"
        )
    )

    if not stock_code:

        log_info(
            "Financial History",
            "缺少股票代码",
        )

        return financial_data

    log_section(
        "Financial History",
        "LOAD DASHBOARD HISTORY",
    )

    log_summary(
        "Financial History",
        "股票代码",
        stock_code,
    )

    # =========================================
    # Deterministic Tool Call
    # =========================================

    try:

        history_result = (
            get_financial_history.invoke(
                {
                    "stock_code":
                        stock_code,

                    "periods":
                        12,
                }
            )
        )

    except Exception as error:

        log_exception(
            "Financial History",
            error,
            "历史财务加载失败",
        )

        return financial_data

    if is_failure_result(
        history_result
    ):
        log_summary(
            "Financial History",
            "加载失败",
            history_result.get("错误信息"),
        )

        return financial_data

    try:

        safe_history = (
            sanitize_financial_history(
                history_result
            )
        )

    except Exception as error:

        log_exception(
            "Financial History",
            error,
            "历史财务清洗失败",
        )

        return financial_data

    if is_failure_result(
        safe_history
    ):
        return financial_data

    history_series = (
        safe_history.get(
            "财务历史序列",
            []
        )
    )

    # =========================================
    # Merge
    # =========================================

    merged_data = dict(
        financial_data
    )

    merged_data[
        "财务历史序列"
    ] = history_series

    merged_data[
        "历史报告期数量"
    ] = len(
        history_series
    )

    log_summary(
        "Financial History",
        "历史报告期数量",
        len(history_series),
    )

    return merged_data


# =========================================================
# 3. Financial Node
# =========================================================

def financial_node(
    state: AnalysisState,
):

    # ---------------------------------
    # Skip
    # ---------------------------------

    if not agent_is_requested(
        state,
        "financial",
    ):

        log_info(
            "Financial Agent",
            "SKIPPED",
        )

        return {}

    # ---------------------------------
    # Run
    # ---------------------------------

    log_section(
        "Financial Agent",
        "RUN",
    )

    user_query = state[
        "user_query"
    ]

    financial_task = (
    "你当前只负责原始用户问题中的"
    "财务指标与基本面数据分析部分。\n"
    "忽略市场行情、技术指标、DCF估值"
    "以及其他不属于 Financial Agent "
    "职责的任务。\n\n"
    "如果原始问题明确要求分析财务指标，"
    "必须根据工具获取真实财务数据，"
    "不得仅凭模型知识直接回答。\n\n"
    "原始用户问题：\n"
    f"{user_query}"
)

    try:

        result = financial_agent.invoke({
            "messages": [
                HumanMessage(
                    content=financial_task
                )
            ]
        })

    except Exception as error:

        log_exception(
            "Financial Node",
            error,
            "Financial Agent 执行失败",
        )

        return {
            "financial_report": (
                "Financial Agent 执行失败，"
                "本次未生成财务分析。"
            )
        }


    financial_report = (
        result["messages"][-1].content
    )


    financial_data = (
        result.get(
            "financial_data"
        )
    )

    log_summary(
        "Financial Node",
        "financial_data 是否存在",
        financial_data is not None,
    )

    if isinstance(
        financial_data,
        dict,
    ):

        log_summary(
            "Financial Node",
            "financial_data keys",
            list(financial_data.keys()),
        )

        log_info(
            "Financial Node",
            "调用 ensure_financial_history",
        )
    # =========================================
    # Ensure Dashboard History Data
    # =========================================
    if financial_data:

        financial_data = (
            ensure_financial_history(
                financial_data
            )
        )

        log_summary(
            "Financial Node",
            "补充历史数据后 keys",
            list(financial_data.keys()),
        )

        log_summary(
            "Financial Node",
            "历史序列长度",
            len(financial_data.get("财务历史序列", [])),
        )

    # =========================================
    # Financial Trend Engine
    # =========================================

    financial_trend = None

    if financial_data:

        try:

            financial_trend = (
                build_financial_trend_analysis(
                    financial_data
                )
            )

        except Exception as error:

            log_exception(
                "Financial Trend",
                error,
                "确定性趋势计算失败",
            )

            financial_trend = build_failure_result(
                source="Financial Trend Engine",
                stage="build_financial_trend_analysis",
                message="确定性财务趋势计算失败。",
                retryable=False,
            )

        log_section(
            "Financial Trend",
            "ENGINE",
        )

        log_summary(
            "Financial Trend",
            "状态",
            financial_trend.get("状态"),
        )

        log_summary(
            "Financial Trend",
            "最新报告期",
            financial_trend.get("最新报告期"),
        )

        log_summary(
            "Financial Trend",
            "去年同期报告期",
            financial_trend.get("去年同期报告期"),
        )

        log_summary(
            "Financial Trend",
            "趋势指标数量",
            len(financial_trend.get("指标趋势", {})),
        )

    # =========================================
    # Financial Trend + Qwen
    # =========================================

    financial_trend_report = None

    if (
        isinstance(
            financial_trend,
                dict,
            )
            and
            financial_trend.get(
                "状态"
            )
            ==
            "成功"
        ):

            log_section(
                "Financial Trend Qwen",
                "RUN",
            )

            try:

                financial_trend_report = (
                    generate_financial_trend_report(
                        financial_trend
                    )
                )

            except Exception as error:

                log_exception(
                    "Financial Trend Qwen",
                    error,
                    "趋势摘要生成失败",
                )

                financial_trend_report = None

            log_info(
                "Financial Trend Qwen",
                "完成",
            )


    # =========================================
    # Merge Financial Reports
    # =========================================

    if (
        isinstance(
            financial_trend,
            dict,
        )
        and
        financial_trend.get(
            "状态"
        )
        ==
        "成功"
    ):

        deterministic_trend_report = (
            format_financial_trend_report(
                financial_trend
            )
        )

        financial_report = (
            financial_report.strip()
            +
            "\n\n"
            +
            "## 同比财务趋势\n\n"
            +
            deterministic_trend_report.strip()
        )

        if financial_trend_report:

            financial_report += (
                "\n\n"
                +
                "### 趋势总结\n\n"
                +
                financial_trend_report.strip()
            )

    # =========================================
    # Financial Node Output
    # =========================================

    output = {
        "financial_report":
            financial_report,
    }

    if financial_data:

        output[
            "financial_data"
        ] = financial_data

    if financial_trend:

        output[
            "financial_trend"
        ] = financial_trend

    if financial_trend_report:

        output[
            "financial_trend_report"
        ] = financial_trend_report

    log_info(
        "Financial Agent",
        "完成",
    )

    return output


# =========================================================
# 4. Valuation Node
# =========================================================

def valuation_node(
    state: AnalysisState,
):

    # ---------------------------------
    # Skip
    # ---------------------------------

    if not agent_is_requested(
        state,
        "valuation",
    ):

        log_info(
            "Valuation Agent",
            "SKIPPED",
        )

        return {}

    # ---------------------------------
    # Run
    # ---------------------------------

    log_section(
        "Valuation Agent",
        "RUN",
    )

    user_query = state[
        "user_query"
    ]

    valuation_task = (
    "你当前只负责原始用户问题中的"
    "估值与DCF计算部分。\n"
    "忽略市场行情、财务指标分析以及"
    "其他不属于 Valuation Agent "
    "职责的任务。\n\n"
    "原始用户问题：\n"
    f"{user_query}"
)

    try:

        result = valuation_agent.invoke({
            "messages": [
                HumanMessage(
                    content=valuation_task
                )
            ]
        })

    except Exception as error:

        log_exception(
            "Valuation Node",
            error,
            "Valuation Agent 执行失败",
        )

        return {
            "valuation_report": (
                "Valuation Agent 执行失败，"
                "本次未生成估值分析。"
            )
        }


# =========================================================
# 优先读取结构化 DCF 数据
# =========================================================

    valuation_data = result.get(
        "valuation_data"
    )


# =========================================================
# 如果成功得到 valuation_data
#
# 不再使用 Valuation LLM 的最终解释，
# 直接由 Python Formatter 生成报告。
# =========================================================

    if (
        valuation_data
        and not is_failure_result(
            valuation_data
        )
    ):

        valuation_report = (
            format_dcf_report(
                valuation_data
            )
        )


# =========================================================
# 如果没有调用 DCF Tool
#
# 比如：
# “请给贵州茅台做DCF估值”
#
# 但用户没有提供自由现金流。
#
# 此时 Valuation Agent 的文字回答仍然有用，
# 因为它需要告诉用户缺少什么数据。
# =========================================================

    else:

        valuation_report = (
            result["messages"][-1].content
        )


    log_info(
        "Valuation Agent",
        "完成",
    )


    output = {
        "valuation_report":
            valuation_report
    }


    if valuation_data:

        output[
            "valuation_data"
        ] = valuation_data


    return output


    # =========================================================
    # Synthesis Node
    # =========================================================

def synthesis_node(
    state: AnalysisState,
):

    log_section(
        "Synthesis Agent",
        "RUN",
    )

    # =========================================
    # Build Safe Context
    # =========================================

    try:

        synthesis_context = (
            build_synthesis_context(
                state
            )
        )

    except Exception as error:

        log_exception(
            "Synthesis Node",
            error,
            "安全综合上下文构建失败",
        )

        synthesis_context = {
            "可用模块数量": 0,
            "模块": {},
            "状态": "失败",
            "错误信息": "安全综合上下文构建失败。",
        }

    module_count = (
        synthesis_context.get(
            "可用模块数量",
            0,
        )
    )

    log_summary(
        "Synthesis Agent",
        "可用综合模块数量",
        module_count,
    )

    log_summary(
        "Synthesis Agent",
        "综合模块",
        list(synthesis_context.get("模块", {}).keys()),
    )

    # =========================================
    # 少于两个模块，不需要综合
    # =========================================

    if module_count < 2:

        log_info(
            "Synthesis Agent",
            "SKIPPED",
        )

        return {
            "synthesis_context":
                synthesis_context
        }

    # =========================================
    # Qwen Synthesis
    # =========================================

    try:

        synthesis_report = (
            generate_synthesis_report(
                synthesis_context
            )
        )

    except Exception as error:

        log_exception(
            "Synthesis Node",
            error,
            "综合报告生成失败",
        )

        synthesis_report = ""

    log_info(
        "Synthesis Agent",
        "完成",
    )

    output = {
        "synthesis_context":
            synthesis_context,
    }

    if synthesis_report:

        output[
            "synthesis_report"
        ] = synthesis_report

    return output

# =========================================================
# 5. Report Node
# =========================================================

def report_node(
    state: AnalysisState,
):

    log_section(
        "Report Agent",
        "RUN",
    )

    try:

        result = report_agent(
            state
        )

    except Exception as error:

        log_exception(
            "Report Node",
            error,
            "最终报告构建失败",
        )

        return {
            "final_report": (
                "最终报告构建失败，"
                "请查看各模块的结构化结果。"
            )
        }

    final_report = result.get(
        "final_report",
        "",
    )

    log_info(
        "Report Agent",
        "完成",
    )

    return {
        "final_report":
            final_report
    }

# =========================================================
# Dashboard Node
# =========================================================

def dashboard_node(
    state: AnalysisState
):

    log_section(
        "Dashboard",
        "BUILD DATA",
    )

    try:

        dashboard_data = (
            build_dashboard_data(
                state
            )
        )

    except Exception as error:

        log_exception(
            "Dashboard Node",
            error,
            "Dashboard 构建失败",
        )

        dashboard_data = {
            "meta": {},
            "market": None,
            "financial": None,
            "valuation": None,
            "synthesis": None,
            "final_report": state.get(
                "final_report"
            ),
            "errors": [
                build_failure_result(
                    source="Dashboard Builder",
                    stage="build_dashboard_data",
                    message="Dashboard 构建失败。",
                    retryable=False,
                )
            ],
        }

    financial_dashboard = (
        dashboard_data.get(
            "financial"
        )
    )

    market_dashboard = (
        dashboard_data.get(
            "market"
        )
    )

    valuation_dashboard = (
        dashboard_data.get(
            "valuation"
        )
    )

    synthesis_dashboard = (
        dashboard_data.get(
            "synthesis"
        )
    )

    final_report = (
        dashboard_data.get(
            "final_report"
        )
    )

    log_summary(
        "Dashboard",
        "Market Dashboard 是否存在",
        isinstance(market_dashboard, dict),
    )

    if isinstance(
        financial_dashboard,
        dict,
    ):

        log_summary(
            "Dashboard",
            "Financial Dashboard keys",
            list(financial_dashboard.keys()),
        )

        log_summary(
            "Dashboard",
            "Financial history_series 长度",
            len(financial_dashboard.get("history_series", [])),
        )

    log_summary(
        "Dashboard",
        "Valuation Dashboard 是否存在",
        isinstance(valuation_dashboard, dict),
    )

    log_summary(
        "Dashboard",
        "Synthesis Dashboard 是否存在",
        isinstance(synthesis_dashboard, dict)
        and bool(synthesis_dashboard.get("report")),
    )

    log_summary(
        "Dashboard",
        "Final Report 是否存在",
        bool(final_report),
    )

    return {
        "dashboard_data":
            dashboard_data
    }


# =========================================================
# 6. Build Main Graph
# =========================================================

workflow = StateGraph(
    AnalysisState
)


# =========================================================
# 7. Nodes
# =========================================================

workflow.add_node(
    "supervisor",
    supervisor_node,
)

workflow.add_node(
    "market",
    market_node,
)

workflow.add_node(
    "financial",
    financial_node,
)

workflow.add_node(
    "valuation",
    valuation_node,
)

workflow.add_node(
    "synthesis",
    synthesis_node,
)

workflow.add_node(
    "report",
    report_node,
)

workflow.add_node(
    "dashboard",
    dashboard_node,
)

# =========================================================
# 8. Entry Point
# =========================================================

workflow.set_entry_point(
    "supervisor"
)


# =========================================================
# 9. Edges
# =========================================================

workflow.add_edge(
    "supervisor",
    "market",
)

workflow.add_edge(
    "market",
    "financial",
)

workflow.add_edge(
    "financial",
    "valuation",
)

workflow.add_edge(
    "valuation",
    "synthesis",
)

workflow.add_edge(
    "synthesis",
    "report",
)

workflow.add_edge(
    "report",
    "dashboard",
)

workflow.add_edge(
    "dashboard",
    END,
)


# =========================================================
# 10. Compile
# =========================================================

multi_agent = workflow.compile()


# =========================================================
# Local Test
# =========================================================

if __name__ == "__main__":
    from app.debug_helpers import log_multi_agent_smoke_result

    result = multi_agent.invoke(
        {
            "user_query": (
                "请综合分析贵州茅台的市场表现和最新财务指标，"
                "并以自由现金流1亿元、增长率5%、折现率10%、"
                "永续增长率2%、预测5年进行DCF估值。"
            )
        }
    )

    log_multi_agent_smoke_result(
        result
    )
