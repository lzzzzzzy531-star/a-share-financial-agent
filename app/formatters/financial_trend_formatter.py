from typing import Any


CATEGORY_NAMES = {
    "profitability": "盈利能力",
    "growth": "成长能力",
    "solvency": "偿债能力",
    "liquidity": "流动性",
    "cash_flow": "现金流",
}


def format_number(
    value: Any,
) -> str:
    """
    将数值格式化为最多4位小数，
    去掉不必要的尾随0。
    """

    if value is None:
        return "-"

    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)

    text = f"{number:.4f}"

    text = text.rstrip("0").rstrip(".")

    return text


def format_metric(
    metric: dict | None,
) -> str:
    """
    格式化：
    {
        "值": 17.72,
        "单位": "%"
    }
    """

    if not isinstance(metric, dict):
        return "-"

    value = metric.get("值")
    unit = metric.get("单位")

    value_text = format_number(value)

    if not unit or unit == "无量纲":
        return value_text

    return f"{value_text}{unit}"


def format_financial_trend_line(
    metric_name: str,
    trend: dict,
) -> str:
    """
    对单个指标生成确定性的同比描述。
    """

    latest = format_metric(
        trend.get("最新值")
    )

    previous = format_metric(
        trend.get("去年同期值")
    )

    change = format_metric(
        trend.get("同比变化")
    )

    direction = trend.get(
        "方向",
        "",
    )

    return (
        f"{metric_name}："
        f"最新值 {latest}，"
        f"去年同期 {previous}，"
        f"同比{direction} {change}。"
    )


def build_financial_trend_safe_observations(
    financial_trend: dict,
) -> list[str]:
    """
    生成允许交给 Qwen 的安全观察。

    只描述确定性方向关系，
    不发送详细数值。
    """

    if not isinstance(financial_trend, dict):
        return []

    trends = financial_trend.get(
        "指标趋势",
        {},
    )

    if not isinstance(trends, dict):
        return []

    categories = {}

    for metric_name, trend in trends.items():

        if not isinstance(trend, dict):
            continue

        category = trend.get("类别")
        direction = trend.get("方向")

        if category not in categories:
            categories[category] = {
                "上升": [],
                "下降": [],
                "持平": [],
            }

        if direction in categories[category]:
            categories[category][direction].append(
                metric_name
            )

    observations = []

    for category, directions in categories.items():

        category_name = CATEGORY_NAMES.get(
            category,
            category,
        )

        parts = []

        for direction in [
            "上升",
            "下降",
            "持平",
        ]:

            metrics = directions.get(
                direction,
                [],
            )

            if metrics:

                names = "、".join(metrics)

                parts.append(
                    f"{names}{direction}"
                )

        if parts:

            observations.append(
                f"{category_name}："
                +
                "；".join(parts)
                +
                "。"
            )

    # =========================================
    # 确定性的正负值跨越
    # =========================================

    net_profit_trend = trends.get(
        "净利润增长率"
    )

    if isinstance(
        net_profit_trend,
        dict,
    ):

        latest = (
            net_profit_trend
            .get(
                "最新值",
                {},
            )
            .get("值")
        )

        previous = (
            net_profit_trend
            .get(
                "去年同期值",
                {},
            )
            .get("值")
        )

        if (
            isinstance(latest, (int, float))
            and
            isinstance(previous, (int, float))
        ):

            if previous > 0 and latest < 0:

                observations.append(
                    "净利润增长率由正值变为负值。"
                )

            elif previous < 0 and latest > 0:

                observations.append(
                    "净利润增长率由负值变为正值。"
                )

    return observations


def format_financial_trend_report(
    financial_trend: dict,
) -> str:
    """
    完全由 Python 生成精确趋势报告。
    """

    if not isinstance(
        financial_trend,
        dict,
    ):
        return ""

    if financial_trend.get("状态") != "成功":

        return (
            "当前历史财务数据不足，"
            "无法生成同报告期同比趋势分析。"
        )

    latest_period = financial_trend.get(
        "最新报告期"
    )

    previous_period = financial_trend.get(
        "去年同期报告期"
    )

    trends = financial_trend.get(
        "指标趋势",
        {},
    )

    category_metrics = {}

    for metric_name, trend in trends.items():

        if not isinstance(trend, dict):
            continue

        category = trend.get(
            "类别",
            "other",
        )

        category_metrics.setdefault(
            category,
            []
        )

        category_metrics[
            category
        ].append(
            (
                metric_name,
                trend,
            )
        )

    sections = []

    for category in [
        "profitability",
        "growth",
        "solvency",
        "liquidity",
        "cash_flow",
    ]:

        metrics = category_metrics.get(
            category,
            [],
        )

        if not metrics:
            continue

        category_name = CATEGORY_NAMES.get(
            category,
            category,
        )

        lines = [
            format_financial_trend_line(
                metric_name,
                trend,
            )
            for metric_name, trend in metrics
        ]

        section = (
            f"### {category_name}\n\n"
            +
            "\n".join(
                f"- {line}"
                for line in lines
            )
        )

        sections.append(section)

    header = (
        f"比较区间：{latest_period} "
        f"vs {previous_period}（同报告期同比）"
    )

    return (
        header
        +
        "\n\n"
        +
        "\n\n".join(sections)
    )