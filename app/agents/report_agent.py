from app.state import AnalysisState


SECTION_NUMERALS = [
    "一",
    "二",
    "三",
    "四",
]


def append_report_section(
    sections: list[tuple[str, str]],
    title: str,
    content: str | None,
) -> None:
    if content:
        sections.append(
            (
                title,
                content.strip(),
            )
        )


def report_agent(
    state: AnalysisState,
) -> AnalysisState:

    sections: list[tuple[str, str]] = []

    market_report = state.get(
        "market_report"
    )

    append_report_section(
        sections,
        "市场表现",
        market_report,
    )

    financial_report = state.get(
        "financial_report"
    )

    append_report_section(
        sections,
        "财务指标",
        financial_report,
    )

    valuation_report = state.get(
        "valuation_report"
    )

    append_report_section(
        sections,
        "估值分析",
        valuation_report,
    )

    synthesis_report = state.get(
        "synthesis_report"
    )

    append_report_section(
        sections,
        "综合分析",
        synthesis_report,
    )

    if not sections:

        final_report = (
            "当前没有可用于生成报告的"
            "专业 Agent 分析结果。"
        )

    else:

        final_report = (
            "\n\n".join(
                (
                    f"{SECTION_NUMERALS[index]}、{title}\n\n"
                    f"{content}"
                )
                for index, (title, content)
                in enumerate(sections)
            )
        )

    return {
        **state,
        "final_report": final_report,
    }
