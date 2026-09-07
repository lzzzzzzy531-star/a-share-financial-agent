from app.state import AnalysisState
from app.runtime import (
    log_section,
    log_summary,
)


# =========================================================
# 1. Keyword Groups
# =========================================================

MARKET_KEYWORDS = [
    "市场",
    "行情",
    "走势",
    "股价",
    "价格",
    "涨跌",
    "收益率",
    "波动率",
    "回撤",
    "均线",
    "成交量",
    "交易日",
    "技术面",
]


FINANCIAL_KEYWORDS = [
    "财务",
    "财报",
    "基本面",
    "roe",
    "ROE",
    "净资产收益率",
    "利润率",
    "净利润",
    "收入",
    "营收",
    "资产负债率",

    # 不再使用过于宽泛的“现金流”
    "经营现金流",
    "每股经营现金流",

    "每股收益",
    "EPS",
]


VALUATION_KEYWORDS = [
    "估值",
    "DCF",
    "dcf",
    "折现现金流",
    "自由现金流",
    "折现率",
    "永续增长率",
    "企业价值",
    "内在价值",
]


# =========================================================
# 2. Helper
# =========================================================

def contains_any(
    text: str,
    keywords: list,
) -> bool:

    return any(
        keyword in text
        for keyword in keywords
    )


# =========================================================
# 3. Supervisor Router
# =========================================================

def select_agents(
    user_query: str,
) -> list[str]:

    query = str(
        user_query
    ).strip()

    selected_agents = []

    # =====================================================
    # 1. Strong Valuation Intent
    # =====================================================
    #
    # DCF 属于非常明确的估值任务。
    #
    # 如果用户只是给：
    #
    # 自由现金流
    # 增长率
    # 折现率
    # 永续增长率
    #
    # 并明确要求 DCF，
    # 不需要 Financial Agent。
    # =====================================================

    strong_valuation_keywords = [
        "DCF",
        "dcf",
        "折现现金流",
        "做DCF",
        "DCF估值",
    ]

    strong_valuation = contains_any(
        query,
        strong_valuation_keywords,
    )

    # =====================================================
    # 2. Market
    # =====================================================

    if contains_any(
        query,
        MARKET_KEYWORDS,
    ):

        selected_agents.append(
            "market"
        )

    # =====================================================
    # 3. Financial
    # =====================================================

    if contains_any(
        query,
        FINANCIAL_KEYWORDS,
    ):

        selected_agents.append(
            "financial"
        )

    # =====================================================
    # 4. Valuation
    # =====================================================

    if contains_any(
        query,
        VALUATION_KEYWORDS,
    ):

        selected_agents.append(
            "valuation"
        )

    # =====================================================
    # 5. DCF Special Rule
    # =====================================================
    #
    # 如果是明确 DCF 请求，
    # 但 Financial 只是被相关词间接触发，
    # 默认只运行 Valuation。
    #
    # 除非用户明确要求同时做财务分析。
    # =====================================================

    explicit_financial_request = contains_any(
        query,
        [
            "财务分析",
            "财务指标",
            "分析财务",
            "财报分析",
            "基本面分析",
        ],
    )

    if (
        strong_valuation
        and not explicit_financial_request
    ):

        selected_agents = [
            agent
            for agent in selected_agents
            if agent != "financial"
        ]

        if "valuation" not in selected_agents:

            selected_agents.append(
                "valuation"
            )

    # =====================================================
    # 6. Default
    # =====================================================

    if not selected_agents:

        selected_agents = [
            "market",
            "financial",
        ]

    return selected_agents

def supervisor_node(
    state: AnalysisState,
):

    user_query = state.get(
        "user_query",
        "",
    )

    requested_agents = (
        select_agents(
            user_query
        )
    )

    log_section(
        "Supervisor",
        "ROUTE",
    )

    log_summary(
        "Supervisor",
        "用户问题",
        user_query,
    )

    log_summary(
        "Supervisor",
        "选择 Agent",
        requested_agents,
    )

    return {
        "requested_agents":
            requested_agents
    }


# =========================================================
# 5. Test
# =========================================================

if __name__ == "__main__":
    from app.runtime import log_summary

    test_queries = [

        # Market
        "分析贵州茅台最近60日行情",

        # Financial
        "分析贵州茅台最新财务指标",

        # Valuation
        (
            "自由现金流=100000000元，"
            "增长率=5%，"
            "折现率=10%，"
            "永续增长率=2%，"
            "预测5年，请做DCF估值。"
        ),

        # Market + Financial
        (
            "综合分析贵州茅台的"
            "市场表现和财务指标"
        ),

        # Financial + Valuation
        (
            "请分析贵州茅台的财务指标，"
            "并进行DCF估值"
        ),

        # Three agents
        (
            "请分析贵州茅台的市场表现、"
            "财务指标和DCF估值"
        ),

        # Default
        "贵州茅台怎么样",
    ]

    for query in test_queries:

        log_summary(
            "Supervisor Smoke",
            "问题",
            query,
        )

        log_summary(
            "Supervisor Smoke",
            "路由",
            select_agents(query),
        )
