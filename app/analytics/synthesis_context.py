from app.formatters.financial_trend_formatter import (
    build_financial_trend_safe_observations,
)


# =========================================================
# Helper
# =========================================================

def get_metric_value(
    metric,
):
    """
    从：
    {
        "值": ...,
        "单位": ...
    }

    中读取数值。
    """

    if isinstance(
        metric,
        dict,
    ):
        return metric.get(
            "值"
        )

    return metric


# =========================================================
# Market Context
# =========================================================

def build_market_synthesis_context(
    market_data: dict,
) -> dict | None:
    """
    为 Synthesis Agent 构造市场安全摘要。

    不发送：
    - 完整价格序列
    - 精确波动率评级
    - 高低估判断
    - 技术面买卖信号

    只生成确定性的数学关系。
    """

    if not isinstance(
        market_data,
        dict,
    ):
        return None

    observations = []

    # =========================================
    # 20日累计收益率
    # =========================================

    return_20d = get_metric_value(
        market_data.get(
            "近20日累计收益率"
        )
    )

    if isinstance(
        return_20d,
        (int, float),
    ):

        if return_20d > 0:
            observations.append(
                "近20日累计收益率为正。"
            )

        elif return_20d < 0:
            observations.append(
                "近20日累计收益率为负。"
            )

        else:
            observations.append(
                "近20日累计收益率为零。"
            )

    # =========================================
    # 60日累计收益率
    # =========================================

    return_60d = get_metric_value(
        market_data.get(
            "近60日累计收益率"
        )
    )

    if isinstance(
        return_60d,
        (int, float),
    ):

        if return_60d > 0:
            observations.append(
                "近60日累计收益率为正。"
            )

        elif return_60d < 0:
            observations.append(
                "近60日累计收益率为负。"
            )

        else:
            observations.append(
                "近60日累计收益率为零。"
            )

    # =========================================
    # 当前价格 vs MA20
    # =========================================

    price_vs_ma20 = get_metric_value(
        market_data.get(
            "当前价格相对20日均价"
        )
    )

    if isinstance(
        price_vs_ma20,
        (int, float),
    ):

        if price_vs_ma20 > 0:
            observations.append(
                "当前价格高于20日均价。"
            )

        elif price_vs_ma20 < 0:
            observations.append(
                "当前价格低于20日均价。"
            )

        else:
            observations.append(
                "当前价格等于20日均价。"
            )

    # =========================================
    # 当前价格 vs MA60
    # =========================================

    price_vs_ma60 = get_metric_value(
        market_data.get(
            "当前价格相对60日均价"
        )
    )

    if isinstance(
        price_vs_ma60,
        (int, float),
    ):

        if price_vs_ma60 > 0:
            observations.append(
                "当前价格高于60日均价。"
            )

        elif price_vs_ma60 < 0:
            observations.append(
                "当前价格低于60日均价。"
            )

        else:
            observations.append(
                "当前价格等于60日均价。"
            )

    if not observations:
        return None

    return {
        "模块":
            "市场",

        "安全观察":
            observations,
    }


# =========================================================
# Financial Context
# =========================================================

def build_financial_synthesis_context(
    financial_trend: dict,
) -> dict | None:
    """
    财务综合上下文直接复用
    Financial Trend Engine 的安全观察。

    不向 Synthesis Agent 发送12期历史原始序列。
    """

    if not isinstance(
        financial_trend,
        dict,
    ):
        return None

    if (
        financial_trend.get(
            "状态"
        )
        !=
        "成功"
    ):
        return None

    observations = (
        build_financial_trend_safe_observations(
            financial_trend
        )
    )

    if not observations:
        return None

    return {
        "模块":
            "财务",

        "安全观察":
            observations,
    }


# =========================================================
# Valuation Context
# =========================================================

def build_valuation_synthesis_context(
    valuation_data: dict,
) -> dict | None:
    """
    Synthesis 层不重新解释 DCF 数值。

    这里只告诉模型：
    已完成结构化 DCF 计算。

    精确企业价值等数据继续由
    Valuation Formatter 负责。
    """

    if not isinstance(
        valuation_data,
        dict,
    ):
        return None

    if not valuation_data:
        return None

    return {
        "模块":
            "估值",

        "安全观察": [
            (
                "已完成结构化DCF计算，"
                "估值结果依赖当前DCF输入与参数假设。"
            )
        ],
    }


# =========================================================
# Main Builder
# =========================================================

def build_synthesis_context(
    state: dict,
) -> dict:
    """
    AnalysisState
        ↓
    Safe Synthesis Context

    只有真正拥有结构化结果的模块
    才进入综合分析。
    """

    context = {}

    # =========================================
    # Market
    # =========================================

    market_context = (
        build_market_synthesis_context(
            state.get(
                "market_data"
            )
        )
    )

    if market_context:
        context[
            "market"
        ] = market_context

    # =========================================
    # Financial
    # =========================================

    financial_context = (
        build_financial_synthesis_context(
            state.get(
                "financial_trend"
            )
        )
    )

    if financial_context:
        context[
            "financial"
        ] = financial_context

    # =========================================
    # Valuation
    # =========================================

    valuation_context = (
        build_valuation_synthesis_context(
            state.get(
                "valuation_data"
            )
        )
    )

    if valuation_context:
        context[
            "valuation"
        ] = valuation_context

    return {
        "可用模块数量":
            len(
                context
            ),

        "模块":
            context,
    }