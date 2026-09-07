def format_number(value):
    """
    只负责稳定地格式化数字，不改变数值含义。
    """

    if value is None:
        return "未知"

    if isinstance(value, float):
        return f"{value:,.2f}"

    return f"{value:,}"


def format_percent(decimal_value):
    """
    DCF 工具内部增长率使用：
    0.05 = 5%

    这里进行确定性的展示转换。
    """

    if decimal_value is None:
        return "未知"

    return f"{decimal_value * 100:.2f}%"


def format_dcf_report(
    data: dict,
) -> str:

    if not isinstance(data, dict):

        return (
            "DCF计算未返回有效的结构化结果。"
        )

    params = data.get(
        "输入参数",
        {},
    )

    free_cash_flow = params.get(
        "自由现金流"
    )

    growth_rate = params.get(
        "增长率"
    )

    discount_rate = params.get(
        "折现率"
    )

    terminal_growth_rate = params.get(
        "永续增长率"
    )

    num_years = params.get(
        "预测年数"
    )

    pv_sum = data.get(
        "预测期现金流现值合计"
    )

    terminal_value = data.get(
        "终值"
    )

    terminal_pv = data.get(
        "终值现值"
    )

    enterprise_value = data.get(
        "企业价值"
    )

    report = (
        "根据用户提供的参数进行DCF计算：\n\n"

        f"- 自由现金流："
        f"{format_number(free_cash_flow)} 元\n"

        f"- 增长率："
        f"{format_percent(growth_rate)}\n"

        f"- 折现率："
        f"{format_percent(discount_rate)}\n"

        f"- 永续增长率："
        f"{format_percent(terminal_growth_rate)}\n"

        f"- 预测年数："
        f"{num_years} 年\n\n"

        "计算结果：\n\n"

        f"- 预测期现金流现值合计："
        f"{format_number(pv_sum)} 元\n"

        f"- 终值："
        f"{format_number(terminal_value)} 元\n"

        f"- 终值现值："
        f"{format_number(terminal_pv)} 元\n"

        f"- 企业价值："
        f"{format_number(enterprise_value)} 元\n\n"

        "该计算结果依赖上述输入参数，"
        "不是股票目标价。"
    )

    return report