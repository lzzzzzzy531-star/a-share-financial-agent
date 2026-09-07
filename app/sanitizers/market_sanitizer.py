from app.runtime import is_failure_result


def sanitize_market_history(
    result: dict
) -> dict:
    """
    将 get_a_share_history 的原始结果
    转换为安全的结构化市场数据。

    返回的数据既可用于：
    - Market Agent 的摘要分析
    - Structured State
    - Dashboard 图表

    其中价格序列会保留在结构化结果中，
    是否传给 LLM 由 Market Tool Node 决定。
    """

    if not isinstance(
        result,
        dict
    ):
        return result

    if is_failure_result(
        result
    ):
        return result

    # =========================
    # 1. 汇总市场指标
    # =========================

    safe_result = {
        "股票代码":
            result.get(
                "股票代码"
            ),

        "数据截止日期":
            result.get(
                "数据截止日期"
            ),

        "实际交易日数量":
            result.get(
                "实际交易日数量"
            ),

        "价格口径":
            result.get(
                "价格口径"
            ),

        "最新收盘价": {
            "值":
                result.get(
                    "最新收盘价"
                ),
            "单位":
                "元",
        },

        "近20日累计收益率": {
            "值":
                result.get(
                    "近20日收益率(%)"
                ),
            "单位":
                "%",
        },

        "近60日累计收益率": {
            "值":
                result.get(
                    "近60日收益率(%)"
                ),
            "单位":
                "%",
        },

        "20日均价": {
            "值":
                result.get(
                    "20日均价"
                ),
            "单位":
                "元",
        },

        "当前价格相对20日均价": {
            "值":
                result.get(
                    "当前价格相对20日均线(%)"
                ),
            "单位":
                "%",
        },

        "60日均价": {
            "值":
                result.get(
                    "60日均价"
                ),
            "单位":
                "元",
        },

        "当前价格相对60日均价": {
            "值":
                result.get(
                    "当前价格相对60日均线(%)"
                ),
            "单位":
                "%",
        },

        "年化波动率": {
            "值":
                result.get(
                    "年化波动率(%)"
                ),
            "单位":
                "%",
        },

        "区间最大回撤": {
            "值":
                result.get(
                    "区间最大回撤(%)"
                ),
            "单位":
                "%",
        },

        "成交量相对20日均量": {
            "值":
                result.get(
                    "成交量相对20日均量"
                ),
            "单位":
                "倍",
        },
    }

    # =========================
    # 2. 删除缺失的汇总指标
    # =========================

    safe_result = remove_none_fields(
        safe_result
    )

    # =========================
    # 3. 构造客观描述
    # =========================

    safe_result[
        "可直接使用的客观描述"
    ] = build_market_observations(
        safe_result
    )

    # =========================
    # 4. 清洗价格时间序列
    # =========================

    price_series = (
        result.get(
            "价格序列",
            []
        )
    )

    safe_price_series = (
        sanitize_price_series(
            price_series
        )
    )

    if safe_price_series:

        safe_result[
            "价格序列"
        ] = safe_price_series

    return safe_result


def sanitize_price_series(
    price_series: list
) -> list:
    """
    清洗价格时间序列。

    每个交易日只保留：
    - 日期
    - 收盘价
    - MA20
    - MA60

    不存在的均线字段直接省略，
    不使用0填充。
    """

    if not isinstance(
        price_series,
        list
    ):
        return []

    cleaned_series = []

    for item in price_series:

        if not isinstance(
            item,
            dict
        ):
            continue

        date = item.get(
            "日期"
        )

        close = item.get(
            "收盘价"
        )

        # 日期或收盘价缺失时，
        # 这一条无法用于价格图表
        if (
            date is None
            or close is None
        ):
            continue

        safe_item = {
            "日期":
                date,

            "收盘价": {
                "值":
                    close,
                "单位":
                    "元",
            },
        }

        # =========================
        # MA20
        # =========================

        ma20 = item.get(
            "MA20"
        )

        if ma20 is not None:

            safe_item[
                "MA20"
            ] = {
                "值":
                    ma20,
                "单位":
                    "元",
            }

        # =========================
        # MA60
        # =========================

        ma60 = item.get(
            "MA60"
        )

        if ma60 is not None:

            safe_item[
                "MA60"
            ] = {
                "值":
                    ma60,
                "单位":
                    "元",
            }

        cleaned_series.append(
            safe_item
        )

    return cleaned_series


def remove_none_fields(
    data: dict
) -> dict:
    """
    删除值为 None 的指标，
    避免模型把一个缺失字段
    错误扩展成其他字段也缺失。
    """

    cleaned = {}

    for key, value in (
        data.items()
    ):

        if isinstance(
            value,
            dict
        ):

            if (
                "值" in value
                and value["值"]
                is None
            ):
                continue

        elif value is None:
            continue

        cleaned[
            key
        ] = value

    return cleaned


def build_market_observations(
    safe_result: dict
) -> list[str]:

    observations = []

    # =========================
    # 20日收益
    # =========================

    item = safe_result.get(
        "近20日累计收益率"
    )

    if item:

        value = item["值"]

        if value > 0:

            observations.append(
                f"最近20个交易日累计收益率为"
                f"{value:.2f}%"
            )

        elif value < 0:

            observations.append(
                f"最近20个交易日累计收益率为"
                f"{value:.2f}%"
            )

        else:

            observations.append(
                "最近20个交易日累计收益率为0%"
            )

    # =========================
    # 60日收益
    # =========================

    item = safe_result.get(
        "近60日累计收益率"
    )

    if item:

        value = item["值"]

        observations.append(
            f"最近60个交易日累计收益率为"
            f"{value:.2f}%"
        )

    # =========================
    # MA20
    # =========================

    item = safe_result.get(
        "当前价格相对20日均价"
    )

    if item:

        value = item["值"]

        if value > 0:

            observations.append(
                f"当前价格高于20日均价"
                f"{abs(value):.2f}%"
            )

        elif value < 0:

            observations.append(
                f"当前价格低于20日均价"
                f"{abs(value):.2f}%"
            )

        else:

            observations.append(
                "当前价格与20日均价相同"
            )

    # =========================
    # MA60
    # =========================

    item = safe_result.get(
        "当前价格相对60日均价"
    )

    if item:

        value = item["值"]

        if value > 0:

            observations.append(
                f"当前价格高于60日均价"
                f"{abs(value):.2f}%"
            )

        elif value < 0:

            observations.append(
                f"当前价格低于60日均价"
                f"{abs(value):.2f}%"
            )

        else:

            observations.append(
                "当前价格与60日均价相同"
            )

    # =========================
    # 成交量
    # =========================

    item = safe_result.get(
        "成交量相对20日均量"
    )

    if item:

        value = item["值"]

        observations.append(
            f"最近交易日成交量为"
            f"20日平均成交量的"
            f"{value:.2f}倍"
        )

    return observations
