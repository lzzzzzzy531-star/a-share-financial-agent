# =========================================================
# Common Dashboard Helpers
# =========================================================


def format_kpi(
    kpi: dict | None,
    decimals: int = 2,
) -> str:
    """
    将 Dashboard KPI：

    {
        "value": 1297.5,
        "unit": "元"
    }

    格式化成：

    1297.50 元
    """

    if not isinstance(
        kpi,
        dict,
    ):
        return "暂无数据"

    value = kpi.get(
        "value"
    )

    unit = kpi.get(
        "unit"
    )

    if value is None:
        return "暂无数据"

    if isinstance(
        value,
        float,
    ):
        value_text = (
            f"{value:.{decimals}f}"
        )

    else:
        value_text = str(
            value
        )

    if unit:
        return (
            f"{value_text} {unit}"
        )

    return value_text


def format_amount(
    value,
    decimals: int = 2,
) -> str:
    """
    将金额格式化为更适合 Dashboard 展示的形式。

    例如：

    1446211889.98
    ->
    14.46 亿元
    """

    if value is None:
        return "暂无数据"

    try:
        value = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):
        return str(
            value
        )

    abs_value = abs(
        value
    )

    if abs_value >= 100000000:

        return (
            f"{value / 100000000:.{decimals}f} 亿元"
        )

    if abs_value >= 10000:

        return (
            f"{value / 10000:.{decimals}f} 万元"
        )

    return (
        f"{value:.{decimals}f} 元"
    )