import os
import re

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
# Model
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
# System Prompt
# =========================================================

SYNTHESIS_SYSTEM_PROMPT = """
你是一个金融多智能体系统中的 Synthesis Agent。

你的任务是：

把 Market、Financial、Valuation 专业模块已经确认的
安全观察整合成简洁的跨维度总结。

你没有工具权限。

严格遵守以下规则：

1. 只能使用输入中的安全观察。

2. 不得使用模型记忆补充：
   - 公司经营情况
   - 行业信息
   - 产品信息
   - 管理层信息
   - 宏观经济
   - 市场地位
   - 历史事实

3. 不得重新计算任何指标。

4. 不得输出输入中没有出现的新数字。

5. 不得解释任何指标变化的原因。

6. 不得建立未经数据证明的因果关系。
   例如禁止：
   “因为盈利下降，所以股价下跌”。

7. 不得进行：
   - 买入建议
   - 卖出建议
   - 持有建议
   - 目标价判断
   - 高估或低估判断

8. 不得使用没有确定阈值支持的评价词：
   - 显著
   - 大幅
   - 明显
   - 小幅
   - 略有
   - 极高
   - 极低
   - 优秀
   - 较差
   - 健康
   - 危险
   - 强势
   - 弱势

9. 市场收益率为正或负，
   只能描述累计收益率方向，
   不得自动解释为长期趋势。

10. 当前价格高于或低于均线，
    只能描述价格与均线的数学关系，
    不得解释为支撑、压力、突破或买卖信号。

11. 财务指标上升或下降，
    只描述同比变化方向，
    不得自动解释为改善或恶化。

12. DCF结果只能说明：
    已完成基于当前输入与假设的估值计算。
    不得与市场价格比较并判断高估或低估，
    除非输入明确提供经过验证的比较结果。

13. 不得使用“环比”。

14. 输出中文。

15. 推荐结构：

市场维度：
...

财务维度：
...

估值维度：
...

综合观察：
...

如果某个模块不存在，则不要虚构该模块的结论。
"""


# =========================================================
# Output Validator
# =========================================================

BANNED_SYNTHESIS_TERMS = [
    "显著",
    "大幅",
    "明显",
    "小幅",
    "略有",
    "极高",
    "极低",
    "改善",
    "恶化",
    "强势",
    "弱势",
    "趋势",
    "健康",
    "危险",
    "高估",
    "低估",
    "买入",
    "卖出",
    "持有建议",
    "目标价",
    "支撑位",
    "压力位",
    "突破",
    "环比",
]


def extract_numeric_tokens(
    text: str,
) -> set[str]:
    """
    提取文本中的数字 token。

    例如：

    "近20日和60日"
        ↓
    {"20", "60"}
    """

    if not isinstance(
        text,
        str,
    ):
        return set()

    return set(
        re.findall(
            r"\d+(?:\.\d+)?",
            text,
        )
    )


def collect_allowed_numeric_tokens(
    synthesis_context: dict,
) -> set[str]:
    """
    从 Python 生成的安全 Context 中，
    提取允许 Qwen 使用的数字。

    Qwen 只能复述这些已经存在的数字，
    不得创造新数字。
    """

    if not isinstance(
        synthesis_context,
        dict,
    ):
        return set()

    modules = synthesis_context.get(
        "模块",
        {},
    )

    if not isinstance(
        modules,
        dict,
    ):
        return set()

    allowed_numbers = set()

    for module in modules.values():

        if not isinstance(
            module,
            dict,
        ):
            continue

        observations = module.get(
            "安全观察",
            [],
        )

        if not isinstance(
            observations,
            list,
        ):
            continue

        for observation in observations:

            allowed_numbers.update(
                extract_numeric_tokens(
                    str(
                        observation
                    )
                )
            )

    return allowed_numbers


def validate_synthesis_report(
    text: str,
    synthesis_context: dict,
) -> bool:
    """
    验证综合报告。

    原则：

    1. 禁止危险或越界表达。
    2. 允许复述 Context 已存在的数字。
    3. 禁止生成 Context 中不存在的新数字。
    """

    if not isinstance(
        text,
        str,
    ):
        return False

    if not text.strip():
        return False

    # =========================================
    # 禁止越界词
    # =========================================

    for term in (
        BANNED_SYNTHESIS_TERMS
    ):

        if term in text:
            return False

    # =========================================
    # Module Grounding Check
    # =========================================

    modules = (
        synthesis_context.get(
            "模块",
            {}
        )
    )

    if not isinstance(
        modules,
        dict,
    ):
        modules = {}

    module_title_mapping = {
        "market":
            "市场维度",

        "financial":
            "财务维度",

        "valuation":
            "估值维度",
    }

    for (
        module_key,
        module_title,
    ) in module_title_mapping.items():

        # Context 中不存在该模块，
        # Qwen 就不能输出该模块标题。
        if (
            module_key
            not in modules
            and
            module_title in text
        ):

            log_info(
                "Synthesis Validator",
                f"发现未经授权的模块: {module_title}",
            )

            return False

    # =========================================
    # Numeric Grounding Check
    # =========================================

    output_numbers = (
        extract_numeric_tokens(
            text
        )
    )

    allowed_numbers = (
        collect_allowed_numeric_tokens(
            synthesis_context
        )
    )

    new_numbers = (
        output_numbers
        -
        allowed_numbers
    )

    if new_numbers:

        log_info(
            "Synthesis Validator",
            f"发现未经授权的新数字: {sorted(new_numbers)}",
        )

        return False

    return True


# =========================================================
# Deterministic Fallback
# =========================================================

def build_synthesis_fallback(
    synthesis_context: dict,
) -> str:
    """
    如果 Qwen 输出未通过安全检查，
    用 Python 安全拼接观察结果。
    """

    modules = (
        synthesis_context.get(
            "模块",
            {}
        )
    )

    sections = []

    title_mapping = {
        "market":
            "市场维度",

        "financial":
            "财务维度",

        "valuation":
            "估值维度",
    }

    for key in [
        "market",
        "financial",
        "valuation",
    ]:

        module = modules.get(
            key
        )

        if not isinstance(
            module,
            dict,
        ):
            continue

        observations = (
            module.get(
                "安全观察",
                [],
            )
        )

        if not observations:
            continue

        title = (
            title_mapping.get(
                key,
                key,
            )
        )

        content = "".join(
            observations
        )

        sections.append(
            f"{title}：{content}"
        )

    return "\n\n".join(
        sections
    )


# =========================================================
# Synthesis Agent
# =========================================================

def generate_synthesis_report(
    synthesis_context: dict,
) -> str:
    """
    生成跨 Agent 综合分析。
    """

    if not isinstance(
        synthesis_context,
        dict,
    ):
        return ""

    module_count = (
        synthesis_context.get(
            "可用模块数量",
            0,
        )
    )

    # 单一专业模块没有必要做综合分析
    if module_count < 2:
        return ""

    messages = [

        SystemMessage(
            content=
                SYNTHESIS_SYSTEM_PROMPT
        ),

        HumanMessage(
            content=(
                "以下是各专业模块由 Python "
                "筛选后的安全观察。\n\n"
                f"{synthesis_context}\n\n"
                "请只基于这些信息进行跨维度综合。"
            )
        ),
    ]

    try:

        response = model.invoke(
            messages
        )

    except Exception as error:

        log_exception(
            "Synthesis Agent",
            error,
            "Qwen 调用失败",
        )

        return build_synthesis_fallback(
            synthesis_context
        )

    report = (
        response.content
        if response
        else ""
    )

    if validate_synthesis_report(
        report,
        synthesis_context,
    ):

        return report.strip()

    log_info(
        "Synthesis Agent",
        "Qwen 输出未通过安全校验，使用 Python fallback",
    )

    return build_synthesis_fallback(
        synthesis_context
    )
