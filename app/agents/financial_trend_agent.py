import os
import re

from app.formatters.financial_trend_formatter import (
    build_financial_trend_safe_observations,
)

from dotenv import load_dotenv

from langchain_openai import (
    ChatOpenAI,
)

from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
)

from app.runtime import (
    log_exception,
    log_info,
)


load_dotenv()


# =========================================================
# Qwen Model
# =========================================================

model = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv(
        "DASHSCOPE_API_KEY"
    ),
    base_url=(
        "https://dashscope.aliyuncs.com/"
        "compatible-mode/v1"
    ),
    streaming=False,
)


# =========================================================
# Financial Trend System Prompt
# =========================================================

FINANCIAL_TREND_SYSTEM_PROMPT = """
你是 Financial Trend Analyst。

你会收到 Python 已经生成的“安全财务趋势观察”。

你的任务仅仅是把这些观察整理成一段简洁中文总结。

严格规则：

1. 不得进行任何数学计算。

2. 不得添加输入中不存在的事实。

3. 不得解释任何指标变化原因。

4. 不得加入：
   - 行业信息
   - 公司经营原因
   - 宏观因素
   - 市场地位
   - 投资建议
   - 估值判断

5. 不得使用以下程度或评价词：
   - 大幅
   - 显著
   - 明显
   - 小幅
   - 略有
   - 较强
   - 较弱
   - 优秀
   - 较差
   - 健康
   - 危险

6. 不得把资产负债率变化解释为
   “杠杆改善”“偿债能力增强”等。

7. 不得把流动比率或速动比率变化解释为
   “偿债能力增强或减弱”。

8. 不得使用“环比”。

9. 不得输出任何新的数字。

10. 只允许使用：
    - 上升
    - 下降
    - 持平
    - 由正值变为负值
    - 由负值变为正值
    这些确定性方向描述。

11. 输出中文。

12. 只输出一段简短总结，不要重复详细指标列表。

"""


# =========================================================
# Build LLM Context
# =========================================================

def build_financial_trend_llm_context(
    financial_trend: dict,
) -> dict:
    """
    Qwen 只接收 Python 生成的
    安全方向观察，不接收详细财务数值。
    """

    observations = (
        build_financial_trend_safe_observations(
            financial_trend
        )
    )

    return {
        "安全趋势观察":
            observations
    }


# =========================================================
# Generate Trend Report
# =========================================================

BANNED_TREND_TERMS = [
    "大幅",
    "显著",
    "明显",
    "小幅",
    "略有",
    "较强",
    "较弱",
    "改善",
    "恶化",
    "增强",
    "减弱",
    "健康",
    "危险",
    "高估",
    "低估",
    "买入",
    "卖出",
    "环比",
    "杠杆水平",
]


def validate_financial_trend_summary(
    text: str,
) -> bool:
    """
    检查 Qwen 趋势摘要是否越界。
    """

    if not isinstance(
        text,
        str,
    ):
        return False

    if not text.strip():
        return False

    # Qwen 摘要不允许重新输出数值
    if re.search(
        r"\d",
        text,
    ):
        return False

    for term in BANNED_TREND_TERMS:

        if term in text:
            return False

    if re.search(
        r"(偿债能力|流动性).*(上升|下降|增强|减弱)",
        text,
    ):
        return False

    return True

def generate_financial_trend_report(
    financial_trend: dict,
) -> str:
    """
    Qwen 只生成非数值的趋势总结。
    """

    if not isinstance(
        financial_trend,
        dict,
    ):
        return ""

    if (
        financial_trend.get(
            "状态"
        )
        !=
        "成功"
    ):

        return ""

    llm_context = (
        build_financial_trend_llm_context(
            financial_trend
        )
    )

    messages = [

        SystemMessage(
            content=
                FINANCIAL_TREND_SYSTEM_PROMPT
        ),

        HumanMessage(
            content=(
                "以下内容均由 Python "
                "确定性分析生成：\n\n"
                f"{llm_context}\n\n"
                "请仅整理为一段简短总结。"
            )
        ),
    ]

    try:

        response = model.invoke(
            messages
        )

    except Exception as error:

        log_exception(
            "Financial Trend Qwen",
            error,
            "Qwen 调用失败",
        )

        return ""

    summary = (
        response.content
        if response
        else ""
    )

    if not validate_financial_trend_summary(
        summary
    ):

        log_info(
            "Financial Trend Qwen",
            "输出未通过安全校验，已放弃该摘要",
        )

        return ""

    return summary.strip()
