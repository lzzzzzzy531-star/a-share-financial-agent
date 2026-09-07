from app.runtime import is_failure_result


def remove_none_fields(data: dict) -> dict:
    cleaned = {}

    for key, value in data.items():

        if isinstance(value, dict):
            if "值" in value and value["值"] is None:
                continue

        elif value is None:
            continue

        cleaned[key] = value

    return cleaned


def build_financial_observations(safe_result: dict) -> list[str]:
    observations = []

    revenue_growth = safe_result.get(
        "主营业务收入增长率"
    )

    profit_growth = safe_result.get(
        "净利润增长率"
    )

    if revenue_growth:
        value = revenue_growth["值"]

        if value is not None:
            observations.append(
                f"主营业务收入增长率为{value:.2f}%"
            )

    if profit_growth:
        value = profit_growth["值"]

        if value is not None:
            observations.append(
                f"净利润增长率为{value:.2f}%"
            )

    if revenue_growth and profit_growth:

        revenue_value = revenue_growth["值"]
        profit_value = profit_growth["值"]

        if (
            revenue_value is not None
            and profit_value is not None
            and revenue_value > 0
            and profit_value < 0
        ):
            observations.append(
                "主营业务收入增长率为正，"
                "净利润增长率为负"
            )

        elif (
            revenue_value is not None
            and profit_value is not None
            and revenue_value < 0
            and profit_value > 0
        ):
            observations.append(
                "主营业务收入增长率为负，"
                "净利润增长率为正"
            )

    return observations


def sanitize_financial_indicators(
    result: dict,
) -> dict:
    """
    将 get_financial_indicators 的原始结果转换为
    可以安全提供给 Financial Agent 的结构化数据。
    """

    if not isinstance(result, dict):
        return result

    if is_failure_result(
        result
    ):
        return result

    safe_result = {
        "股票代码": result.get(
            "股票代码"
        ),

        "报告期": result.get(
            "报告期"
        ),

        "每股收益": {
            "值": result.get(
                "每股收益"
            ),
            "单位": "元/股",
        },

        "净资产收益率ROE": {
            "值": result.get(
                "净资产收益率ROE"
            ),
            "单位": "%",
        },

        "加权净资产收益率ROE": {
            "值": result.get(
                "加权净资产收益率ROE"
            ),
            "单位": "%",
        },

        "销售毛利率": {
            "值": result.get(
                "销售毛利率"
            ),
            "单位": "%",
        },

        "销售净利率": {
            "值": result.get(
                "销售净利率"
            ),
            "单位": "%",
        },

        "总资产净利润率": {
            "值": result.get(
                "总资产净利润率"
            ),
            "单位": "%",
        },

        "主营业务收入增长率": {
            "值": result.get(
                "主营业务收入增长率"
            ),
            "单位": "%",
        },

        "净利润增长率": {
            "值": result.get(
                "净利润增长率"
            ),
            "单位": "%",
        },

        "净资产增长率": {
            "值": result.get(
                "净资产增长率"
            ),
            "单位": "%",
        },

        "应收账款周转率": {
            "值": result.get(
                "应收账款周转率"
            ),
            "单位": "次",
        },

        "存货周转率": {
            "值": result.get(
                "存货周转率"
            ),
            "单位": "次",
        },

        "总资产周转率": {
            "值": result.get(
                "总资产周转率"
            ),
            "单位": "次",
        },

        "流动比率": {
            "值": result.get(
                "流动比率"
            ),
            "单位":"无量纲",
        },

        "速动比率": {
            "值": result.get(
                "速动比率"
            ),
            "单位":"无量纲",
        },

        "资产负债率": {
            "值": result.get(
                "资产负债率"
            ),
            "单位": "%",
        },

        "每股经营现金流": {
            "值": result.get(
                "每股经营现金流"
            ),
            "单位": "元/股",
        },
    }

    safe_result = remove_none_fields(
        safe_result
    )

    safe_result[
        "可直接使用的客观描述"
    ] = build_financial_observations(
        safe_result
    )

    return safe_result

# =========================================================
# Financial History Sanitizer
# =========================================================

def sanitize_financial_history_item(
    item: dict
) -> dict:
    """
    清洗单个报告期的历史财务指标。

    原始 Tool 数据：

    {
        "报告期": "2026-06-30",
        "净资产收益率ROE": 17.72,
        "存货周转率": 0.1544,
        ...
    }

    转换为：

    {
        "报告期": "2026-06-30",
        "净资产收益率ROE": {
            "值": 17.72,
            "单位": "%"
        },
        ...
    }
    """

    if not isinstance(
        item,
        dict,
    ):
        return {}

    safe_item = {}

    # =========================================
    # 报告期
    # =========================================

    report_period = (
        item.get(
            "报告期"
        )
    )

    if report_period is not None:

        safe_item[
            "报告期"
        ] = report_period

    # =========================================
    # 指标单位映射
    # =========================================

    unit_mapping = {

        # -------------------------------------
        # 盈利能力
        # -------------------------------------

        "每股收益":
            "元/股",

        "净资产收益率ROE":
            "%",

        "加权净资产收益率ROE":
            "%",

        "销售毛利率":
            "%",

        "销售净利率":
            "%",

        "总资产净利润率":
            "%",

        # -------------------------------------
        # 成长能力
        # -------------------------------------

        "主营业务收入增长率":
            "%",

        "净利润增长率":
            "%",

        "净资产增长率":
            "%",

        # -------------------------------------
        # 运营效率
        # -------------------------------------

        "应收账款周转率":
            "次",

        "存货周转率":
            "次",

        "总资产周转率":
            "次",

        # -------------------------------------
        # 偿债能力
        # -------------------------------------

        "流动比率":
            "无量纲",

        "速动比率":
            "无量纲",

        "资产负债率":
            "%",

        # -------------------------------------
        # 现金流
        # -------------------------------------

        "每股经营现金流":
            "元/股",
    }

    # =========================================
    # 构造安全指标
    # =========================================

    for (
        metric_name,
        unit,
    ) in unit_mapping.items():

        value = (
            item.get(
                metric_name
            )
        )

        if value is None:
            continue

        safe_item[
            metric_name
        ] = {
            "值":
                value,

            "单位":
                unit,
        }

    return safe_item


def sanitize_financial_history(
    result: dict
) -> dict:
    """
    清洗 get_financial_history 工具的完整结果。
    """

    if not isinstance(
        result,
        dict,
    ):
        return result

    if is_failure_result(
        result
    ):
        return result

    safe_result = {}

    # =========================================
    # 股票代码
    # =========================================

    stock_code = (
        result.get(
            "股票代码"
        )
    )

    if stock_code is not None:

        safe_result[
            "股票代码"
        ] = stock_code

    # =========================================
    # 历史序列
    # =========================================

    history_series = (
        result.get(
            "财务历史序列",
            []
        )
    )

    safe_history_series = []

    if isinstance(
        history_series,
        list,
    ):

        for item in history_series:

            safe_item = (
                sanitize_financial_history_item(
                    item
                )
            )

            if safe_item:

                safe_history_series.append(
                    safe_item
                )

    safe_result[
        "实际报告期数量"
    ] = len(
        safe_history_series
    )

    safe_result[
        "财务历史序列"
    ] = safe_history_series

    return safe_result
