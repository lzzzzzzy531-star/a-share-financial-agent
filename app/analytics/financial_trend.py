from datetime import datetime
from typing import Any


# =========================================================
# Financial Trend Engine
# =========================================================
#
# 职责：
#
# 1. 读取 Sanitizer 输出的历史财务序列
# 2. 找到最新报告期
# 3. 找到去年相同报告期
# 4. 进行确定性同比计算
#
# 注意：
#
# 不比较相邻报告期：
#
# 2026-03-31
#      ↓
# 2026-06-30
#
# 因为部分财务指标可能是累计报告期口径。
#
# 正确比较：
#
# 2025-06-30
#      ↓
# 2026-06-30
#
# =========================================================


# =========================================================
# 1. Trend Metric Configuration
# =========================================================

TREND_METRICS = {

    # -----------------------------------------
    # 盈利能力
    # -----------------------------------------

    "每股收益": {
        "category": "profitability",
        "change_type": "absolute",
    },

    "净资产收益率ROE": {
        "category": "profitability",
        "change_type": "percentage_point",
    },

    "加权净资产收益率ROE": {
        "category": "profitability",
        "change_type": "percentage_point",
    },

    "销售净利率": {
        "category": "profitability",
        "change_type": "percentage_point",
    },

    "总资产净利润率": {
        "category": "profitability",
        "change_type": "percentage_point",
    },

    # -----------------------------------------
    # 成长能力
    # -----------------------------------------

    "主营业务收入增长率": {
        "category": "growth",
        "change_type": "percentage_point",
    },

    "净利润增长率": {
        "category": "growth",
        "change_type": "percentage_point",
    },

    "净资产增长率": {
        "category": "growth",
        "change_type": "percentage_point",
    },

    # -----------------------------------------
    # 偿债 / 流动性
    # -----------------------------------------

    "资产负债率": {
        "category": "solvency",
        "change_type": "percentage_point",
    },

    "流动比率": {
        "category": "liquidity",
        "change_type": "absolute",
    },

    "速动比率": {
        "category": "liquidity",
        "change_type": "absolute",
    },

    # -----------------------------------------
    # 现金流
    # -----------------------------------------

    "每股经营现金流": {
        "category": "cash_flow",
        "change_type": "absolute",
    },
}


# =========================================================
# 2. Metric Helpers
# =========================================================

def get_metric_value(
    metric: Any,
):
    """
    从 Sanitizer 的指标结构中读取数值。

    支持：

    {
        "值": 17.72,
        "单位": "%"
    }

    也兼容直接数值。
    """

    if isinstance(
        metric,
        dict,
    ):
        return metric.get(
            "值"
        )

    if isinstance(
        metric,
        (
            int,
            float,
        ),
    ):
        return metric

    return None


def get_metric_unit(
    metric: Any,
):
    """
    获取指标单位。
    """

    if isinstance(
        metric,
        dict,
    ):
        return metric.get(
            "单位"
        )

    return None


# =========================================================
# 3. Period Helpers
# =========================================================

def parse_report_period(
    period: str,
):
    """
    将报告期转换为 datetime。

    例如：

    2026-06-30
    """

    if not isinstance(
        period,
        str,
    ):
        return None

    try:

        return datetime.strptime(
            period,
            "%Y-%m-%d",
        )

    except ValueError:

        return None


def get_previous_year_period(
    period: str,
):
    """
    根据当前报告期生成去年同期日期。

    例如：

    2026-06-30
        ↓
    2025-06-30
    """

    parsed_period = (
        parse_report_period(
            period
        )
    )

    if parsed_period is None:
        return None

    try:

        previous_period = (
            parsed_period.replace(
                year=
                    parsed_period.year
                    - 1
            )
        )

    except ValueError:

        return None

    return previous_period.strftime(
        "%Y-%m-%d"
    )


# =========================================================
# 4. Find Latest Period
# =========================================================

def find_latest_financial_period(
    history_series: list,
):
    """
    找到历史财务序列中的最新报告期。
    """

    if not isinstance(
        history_series,
        list,
    ):
        return None

    valid_items = []

    for item in history_series:

        if not isinstance(
            item,
            dict,
        ):
            continue

        period = item.get(
            "报告期"
        )

        parsed_period = (
            parse_report_period(
                period
            )
        )

        if parsed_period is None:
            continue

        valid_items.append(
            (
                parsed_period,
                item,
            )
        )

    if not valid_items:
        return None

    valid_items.sort(
        key=lambda x: x[0]
    )

    return valid_items[-1][1]


# =========================================================
# 5. Find Same Period Last Year
# =========================================================

def find_yoy_reference_period(
    history_series: list,
    latest_period: str,
):
    """
    找到去年相同报告期的数据。

    例如：

    latest_period
        2026-06-30

    reference_period
        2025-06-30
    """

    target_period = (
        get_previous_year_period(
            latest_period
        )
    )

    if target_period is None:
        return None

    for item in history_series:

        if not isinstance(
            item,
            dict,
        ):
            continue

        if (
            item.get(
                "报告期"
            )
            ==
            target_period
        ):

            return item

    return None


# =========================================================
# 6. Change Unit
# =========================================================

def resolve_change_unit(
    change_type: str,
    original_unit: str | None,
):
    """
    根据指标类型确定变化量的单位。
    """

    if (
        change_type
        ==
        "percentage_point"
    ):
        return "个百分点"

    return original_unit


# =========================================================
# 7. Direction
# =========================================================

def resolve_direction(
    change_value: float,
):
    """
    只描述数学方向。

    不进行：
    - 好坏评价
    - 投资评价
    - 基本面评价
    """

    if change_value > 0:
        return "上升"

    if change_value < 0:
        return "下降"

    return "持平"


# =========================================================
# 8. Compare Single Metric
# =========================================================

def compare_financial_metric(
    metric_name: str,
    latest_item: dict,
    reference_item: dict,
):
    """
    对单个财务指标进行同报告期同比计算。

    只进行确定性的数值比较：
    - 最新值
    - 去年同期值
    - 差值
    - 数学方向

    不进行好坏评价或原因推断。
    """

    # =========================================
    # 1. 获取指标配置
    # =========================================

    config = (
        TREND_METRICS.get(
            metric_name
        )
    )

    if config is None:
        return None

    # =========================================
    # 2. 获取原始指标对象
    # =========================================

    latest_metric = (
        latest_item.get(
            metric_name
        )
    )

    reference_metric = (
        reference_item.get(
            metric_name
        )
    )

    # =========================================
    # 3. 提取指标数值
    # =========================================

    latest_raw_value = (
        get_metric_value(
            latest_metric
        )
    )

    reference_raw_value = (
        get_metric_value(
            reference_metric
        )
    )

    if (
        latest_raw_value is None
        or
        reference_raw_value is None
    ):
        return None

    # =========================================
    # 4. 转换为 float
    # =========================================

    try:

        latest_value = round(
            float(
                latest_raw_value
            ),
            4,
        )

        reference_value = round(
            float(
                reference_raw_value
            ),
            4,
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    # =========================================
    # 5. 计算变化值
    # =========================================

    change_value = round(
        latest_value
        -
        reference_value,
        4,
    )

    # =========================================
    # 6. 获取原指标单位
    # =========================================

    latest_unit = (
        get_metric_unit(
            latest_metric
        )
    )

    reference_unit = (
        get_metric_unit(
            reference_metric
        )
    )

    original_unit = (
        latest_unit
        or
        reference_unit
    )

    # =========================================
    # 7. 确定变化量单位
    # =========================================

    change_unit = (
        resolve_change_unit(
            config[
                "change_type"
            ],
            original_unit,
        )
    )

    # =========================================
    # 8. 返回结构化趋势结果
    # =========================================

    return {

        "指标":
            metric_name,

        "类别":
            config[
                "category"
            ],

        "最新值": {
            "值":
                latest_value,

            "单位":
                original_unit,
        },

        "去年同期值": {
            "值":
                reference_value,

            "单位":
                original_unit,
        },

        "同比变化": {
            "值":
                change_value,

            "单位":
                change_unit,
        },

        "方向":
            resolve_direction(
                change_value
            ),

        "比较方式":
            "同报告期同比",
    }


# =========================================================
# 9. Build Financial Trend Analysis
# =========================================================

def build_financial_trend_analysis(
    financial_data: dict,
) -> dict:
    """
    Financial Trend Engine 主入口。

    输入：

    financial_data

    其中需要：

    {
        "股票代码": ...,
        "财务历史序列": [...]
    }

    输出：

    {
        "股票代码": ...,
        "最新报告期": ...,
        "去年同期报告期": ...,
        "比较方式": "同报告期同比",
        "指标趋势": {...}
    }
    """

    if not isinstance(
        financial_data,
        dict,
    ):

        return {
            "状态":
                "数据不足",

            "原因":
                "financial_data 不是字典结构",
        }

    history_series = (
        financial_data.get(
            "财务历史序列",
            []
        )
    )

    if not isinstance(
        history_series,
        list,
    ) or not history_series:

        return {
            "股票代码":
                financial_data.get(
                    "股票代码"
                ),

            "状态":
                "数据不足",

            "原因":
                "缺少财务历史序列",
        }

    # =========================================
    # 最新报告期
    # =========================================

    latest_item = (
        find_latest_financial_period(
            history_series
        )
    )

    if latest_item is None:

        return {
            "股票代码":
                financial_data.get(
                    "股票代码"
                ),

            "状态":
                "数据不足",

            "原因":
                "无法识别最新报告期",
        }

    latest_period = (
        latest_item.get(
            "报告期"
        )
    )

    # =========================================
    # 去年同期
    # =========================================

    reference_item = (
        find_yoy_reference_period(
            history_series,
            latest_period,
        )
    )

    if reference_item is None:

        return {
            "股票代码":
                financial_data.get(
                    "股票代码"
                ),

            "最新报告期":
                latest_period,

            "状态":
                "数据不足",

            "原因":
                "历史序列中缺少去年同期报告期",
        }

    reference_period = (
        reference_item.get(
            "报告期"
        )
    )

    # =========================================
    # 指标同比
    # =========================================

    metric_trends = {}

    for metric_name in TREND_METRICS:

        comparison = (
            compare_financial_metric(
                metric_name,
                latest_item,
                reference_item,
            )
        )

        if comparison is not None:

            metric_trends[
                metric_name
            ] = comparison

    return {

        "股票代码":
            financial_data.get(
                "股票代码"
            ),

        "状态":
            "成功",

        "比较方式":
            "同报告期同比",

        "最新报告期":
            latest_period,

        "去年同期报告期":
            reference_period,

        "指标趋势":
            metric_trends,

        "解释限制": [
            (
                "同比变化仅描述同报告期指标的"
                "数值变化。"
            ),
            (
                "方向仅表示数学上的上升、下降"
                "或持平，不代表好坏评价。"
            ),
            (
                "不得将报告期累计指标解释为"
                "单季度环比变化。"
            ),
        ],
    }