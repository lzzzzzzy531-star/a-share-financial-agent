import json
import operator
import os
from typing import TypedDict, Annotated, Sequence

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, ToolMessage
from langchain_core.messages import SystemMessage
from langchain_openai.chat_models import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langgraph.prebuilt import ToolInvocation

from app.tools import (
    discounted_cash_flow,
    owner_earnings,
    roic,
    roe,
    get_a_share_quote,
    get_financial_indicators,
    get_a_share_history,
    search_a_share_stock,
    compare_a_share_companies,
)
from app.runtime import (
    log_section,
    log_summary,
)

# Load the environment variables
load_dotenv()

# Choose the LLM that will drive the agent
model = ChatOpenAI(
    model="qwen-plus",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    streaming=True,
)

local_tools = [
    discounted_cash_flow,
    roe,
    roic,
    owner_earnings,
    get_a_share_quote,
    get_financial_indicators,
    get_a_share_history,
    search_a_share_stock,
    compare_a_share_companies,
]

# =========================
# 不同任务可使用的工具集合
# =========================

analysis_tools = [
    search_a_share_stock,
    get_a_share_history,
    get_financial_indicators,
]
comparison_tools = [
    compare_a_share_companies,
]
quote_tools = [
    search_a_share_stock,
    get_a_share_quote,
]

calculation_tools = [
    roe,
    roic,
    owner_earnings,
    discounted_cash_flow,
]

all_tools = [
    search_a_share_stock,
    get_a_share_quote,
    get_a_share_history,
    get_financial_indicators,
    roe,
    roic,
    owner_earnings,
    discounted_cash_flow,
]

def select_tools(messages):

    user_message = ""

    for message in reversed(messages):
        if message.type == "human":
            user_message = message.content
            break

    # =========================
    # 1. 双股票比较
    # =========================

    comparison_keywords = [
        "比较",
        "对比",
        "相比",
        "横向比较",
        "哪个更",
        "谁更",
    ]

    if any(
        keyword in user_message
        for keyword in comparison_keywords
    ):
        return comparison_tools

    # =========================
    # 2. 单日行情
    # =========================

    quote_keywords = [
        "最新行情",
        "今日行情",
        "今天行情",
        "最近一个交易日",
        "开盘价",
        "最高价",
        "最低价",
    ]

    if any(
        keyword in user_message
        for keyword in quote_keywords
    ):
        return quote_tools

    # 其余保持你的原代码……

    # =========================
    # 3. 财务计算任务
    # =========================

    calculation_keywords = [
        "计算ROE",
        "计算roe",
        "计算ROIC",
        "计算roic",
        "Owner Earnings",
        "owner earnings",
        "DCF",
        "dcf",
        "估值",
    ]

    if any(keyword in user_message for keyword in calculation_keywords):
        return all_tools

    # =========================
    # 4. 默认：股票综合分析
    # =========================

    return analysis_tools

#tools = integration_tools + local_tools
tools = local_tools

tool_executor = ToolExecutor(tools)



class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


# Define the function that determines whether to continue or not
def should_continue(state):
    messages = state["messages"]
    last_message = messages[-1]

    tool_calls = last_message.additional_kwargs.get("tool_calls", [])

    if not tool_calls:
        return "end"
    else:
        return "continue"


# Define the function that calls the model
SYSTEM_PROMPT = """
你是一名严谨的金融分析 Agent。

你的核心原则是：
只基于当前可验证的数据进行分析。
不知道的内容明确说不知道，不得通过猜测补全报告。


【一、数据来源】

1. 公司具体事实和数值只能来自：
   - 用户明确提供的数据；
   - 当前会话中工具真实返回的数据。

2. 不得使用模型记忆补充公司具体信息，包括但不限于：
   - 股票价格
   - 财务数据
   - 历史数据
   - 行业数据
   - 市场份额
   - 产品价格
   - 分红数据
   - 公司行业地位
   - 商业模式
   - 品牌地位
   - 宏观数据
   - 同行业公司数据

3. 工具未返回的数据视为当前未知。
   不得根据其他字段猜测缺失字段的数值、状态或含义。

4. 如果数据不足以支持用户要求的判断，应明确说明：
   “当前工具返回的数据不足以判断该问题。”

5. 宁可减少分析内容，也不得通过猜测使报告显得完整。


【二、数据口径与单位】

6. 必须使用工具明确提供的数据单位和口径。

7. 不得自行：
   - 添加工具没有提供的单位；
   - 修改单位；
   - 将百分比解释为倍数；
   - 将倍数解释为百分比；
   - 将原始成交量转换为“股”“手”“万手”等其他单位。

8. 如果字段单位或统计口径不明确，
   应保留原始值并说明该口径当前无法确认。

9. 不得将中报或季报累计 EPS 直接作为全年 EPS 计算年度 PE。
   如果需要年化，必须明确说明年化方法和假设。

10. 计算 PE、PB、DCF 等估值指标前，
    必须确认所使用数据的报告期和统计口径具有可比性。


【三、工具调用】

11. 缺少计算工具所需的必要参数时，不得猜测参数。

12. DCF、ROIC、Owner Earnings 等计算工具，
    只有在获得真实且完整的必要输入后才能调用。

13. 已经由数据查询工具直接返回的指标，
    不应为了重复验证再次调用计算工具。

14. 当用户只提供股票名称时，应使用股票搜索/解析工具确定股票代码，
    不得依赖模型记忆自行映射代码。

15. 股票搜索返回多个候选且无法唯一确定时，
    不得自行选择其中一个。

16. 应使用满足任务所需的最小工具集合，避免无意义的重复查询。


【四、市场行情分析】

17. 用户要求分析一段时间内的市场表现、收益、波动或回撤时，
    应使用历史行情工具。

18. 如果历史行情工具已经提供：
    - 区间收益率
    - 均价/均线位置
    - 波动率
    - 最大回撤
    - 截止日期
    - 最新收盘价

    应直接使用这些结果，不自行重新计算。

19. 只有用户明确询问最近一个交易日的开盘价、最高价、最低价、
    收盘价等单日行情细节时，才需要调用单日行情工具。

20. 区间收益率为正或负只能描述该区间累计涨跌。
    不得仅凭收益率正负定义：
    - 上升趋势
    - 下降趋势
    - 高位震荡
    - 超买超卖
    - 支撑位
    - 压力位

    这些判断需要专门的数据和规则支持。


【五、分析与解释】

21. 必须区分：
    - 工具返回的事实；
    - Python/工具计算得到的结果；
    - 有数据支持的推断；
    - 当前无法判断的事项。

22. 如果没有明确比较基准，不得把绝对数值描述为：
    - 高 / 低
    - 极高 / 极低
    - 优秀 / 较差
    - 健康 / 危险
    - 强 / 弱
    - 异常高 / 异常低

23. 不得自行引用行业平均值、市场平均值、历史平均值、
    市场中位数或经验阈值作为比较基准。

24. 如果工具结果包含允许使用的描述性结论或解释边界，
    应遵守这些约束，但不得将内部控制信息直接展示给用户。


【六、公司横向比较】

25. 当比较工具已经返回两家公司指标的：
    - 原始值
    - 差值
    - 差值单位
    - 比较结果

    应直接使用工具结果，不自行重新计算。

26. “高于”“低于”“更大”“更小”等表述，
    只代表当前比较对象之间的相对关系，
    不得扩展为行业或市场层面的绝对评价。

27. 百分比指标之间的直接差值使用“百分点”。

28. 最大回撤必须比较回撤幅度，
    不得仅根据负数的数学大小解释金融含义。

29. 波动率、资产负债率等指标即使存在公司间差异，
    也只能描述相对高低，
    不得在没有基准的情况下进一步解释为
    “高风险”“低风险”“健康”“危险”等。

30. 不得仅根据当前横向比较结果得出：
    - 某公司整体更优秀；
    - 某公司投资价值更高；
    - 应买入或卖出某公司。


【七、估值与投资结论】

31. 不得自行给出目标价、买入价、卖出价或合理估值区间。

32. 如果用户要求估值，
    只能使用工具或用户提供的真实数据以及明确披露的假设。


【八、最终输出】

33. 最终回答只输出面向用户的金融分析内容。

34. 不得在最终回答中提及：
    - System Prompt
    - 系统规则
    - 工具限制
    - 解释限制
    - 内部控制
    - 允许使用的描述性结论

35. 不得声称分析完全基于工具数据，
    同时又加入工具没有提供的公司、行业或市场事实。
"""

def call_model(state):
    messages = state["messages"]

    messages_with_system = [
        SystemMessage(content=SYSTEM_PROMPT)
    ] + list(messages)

    selected_tools = select_tools(messages)

    model_with_tools = model.bind_tools(selected_tools)

    # 只在第一次进入 agent 节点时打印 Router
    if len(messages) == 1:
        log_section(
            "Tool Router",
            "SELECT TOOLS",
        )
        log_summary(
            "Tool Router",
            "本次任务允许工具",
            [tool.name for tool in selected_tools],
        )

    response = model_with_tools.invoke(
        messages_with_system
    )

    return {
        "messages": [response]
    }

def remove_none_fields(data):
    """
    删除值为None的指标字段。
    """

    cleaned = {}

    for key, value in data.items():

        if isinstance(value, dict):

            if value.get("值") is None:
                continue

        cleaned[key] = value

    return cleaned

def sanitize_tool_result(tool_name, result):
    """
    将工具原始结果转换为适合LLM解释的安全数据。

    原则：
    1. 不确定单位的数据不让LLM自行解释
    2. 口径不明确的数据直接移除
    3. 只生成能够由数值直接推出的描述性结论
    """
    if tool_name == "compare_a_share_companies":
        return result

    # 如果工具没有返回dict，直接原样返回
    if not isinstance(result, dict):
        return result

    # ======================================
    # 历史行情
    # ======================================

    if tool_name == "get_a_share_history":

        safe_result = {
            "股票代码": result.get("股票代码"),
            "数据截止日期": result.get("数据截止日期"),
            "实际交易日数量": result.get("实际交易日数量"),

            "最新收盘价": {
                "值": result.get("最新收盘价"),
                "单位": "元",
            },

            "价格口径": result.get("价格口径"),

            "近20日收益率": {
                "值": result.get("近20日收益率(%)"),
                "单位": "%",
            },

            "近60日收益率": {
                "值": result.get("近60日收益率(%)"),
                "单位": "%",
            },

            "20日均价": {
                "值": result.get("20日均价"),
                "单位": "元",
            },

            "价格相对20日均线": {
                "值": result.get("当前价格相对20日均线(%)"),
                "单位": "%",
            },

            "60日均价": {
                "值": result.get("60日均价"),
                "单位": "元",
            },

            "价格相对60日均线": {
                "值": result.get("当前价格相对60日均线(%)"),
                "单位": "%",
            },

            "年化波动率": {
                "值": result.get("年化波动率(%)"),
                "单位": "%",
            },

            "区间最大回撤": {
                "值": result.get("区间最大回撤(%)"),
                "单位": "%",
            },

            # 不返回原始成交量，因为单位尚未确认
            "成交量相对20日均量": {
                "值": result.get("成交量相对20日均量"),
                "单位": "倍",
            },
        }

        # Python生成描述，不让LLM自己判断
        descriptions = []

        r20 = result.get("近20日收益率(%)")
        r60 = result.get("近60日收益率(%)")
        ma20_relative = result.get("当前价格相对20日均线(%)")
        ma60_relative = result.get("当前价格相对60日均线(%)")
        volume_ratio = result.get("成交量相对20日均量")

        if r20 is not None:
            if r20 > 0:
                descriptions.append(
                    f"最近20个交易日累计收益率为正，为{r20:.2f}%"
                )
            elif r20 < 0:
                descriptions.append(
                    f"最近20个交易日累计收益率为负，为{r20:.2f}%"
                )
            else:
                descriptions.append(
                    "最近20个交易日累计收益率为0%"
                )

        if r60 is not None:
            if r60 > 0:
                descriptions.append(
                    f"最近60个交易日累计收益率为正，为{r60:.2f}%"
                )
            elif r60 < 0:
                descriptions.append(
                    f"最近60个交易日累计收益率为负，为{r60:.2f}%"
                )

        if ma20_relative is not None:
            if ma20_relative > 0:
                descriptions.append(
                    f"最新价格高于20日均价{ma20_relative:.2f}%"
                )
            else:
                descriptions.append(
                    f"最新价格低于20日均价{abs(ma20_relative):.2f}%"
                )

        if ma60_relative is not None:
            if ma60_relative > 0:
                descriptions.append(
                    f"最新价格高于60日均价{ma60_relative:.2f}%"
                )
            else:
                descriptions.append(
                    f"最新价格低于60日均价{abs(ma60_relative):.2f}%"
                )

        if volume_ratio is not None:
            descriptions.append(
                f"最近交易日成交量为20日平均成交量的"
                f"{volume_ratio * 100:.2f}%"
            )

        safe_result["允许使用的描述性结论"] = descriptions

        safe_result["_internal_constraints"] = [
            "不得根据这些数据自行定义上升趋势或下降趋势",
            "不得评价波动率属于高、中、低水平",
            "不得给成交量原始数值添加股、手等单位",
            "不得引用市场平均值、行业平均值或经验阈值",
        ]

        safe_result = remove_none_fields(safe_result)

        return safe_result

    # ======================================
    # 财务指标
    # ======================================

    if tool_name == "get_financial_indicators":

        safe_result = {
            "股票代码": result.get("股票代码"),
            "报告期": result.get("报告期"),

            "每股收益": {
                "值": result.get("每股收益"),
                "单位": "元",
            },

            "净资产收益率ROE": {
                "值": result.get("净资产收益率ROE"),
                "单位": "%",
            },

            "加权净资产收益率ROE": {
                "值": result.get("加权净资产收益率ROE"),
                "单位": "%",
            },

            "销售毛利率": {
                "值": result.get("销售毛利率"),
                "单位": "%",
            },

            "销售净利率": {
                "值": result.get("销售净利率"),
                "单位": "%",
            },

            "总资产净利润率": {
                "值": result.get("总资产净利润率"),
                "单位": "%",
            },

            "主营业务收入增长率": {
                "值": result.get("主营业务收入增长率"),
                "单位": "%",
            },

            "净利润增长率": {
                "值": result.get("净利润增长率"),
                "单位": "%",
            },

            "净资产增长率": {
                "值": result.get("净资产增长率"),
                "单位": "%",
            },

            "应收账款周转率": {
                "值": result.get("应收账款周转率"),
                "单位": "次",
            },

            "存货周转率": {
                "值": result.get("存货周转率"),
                "单位": "次",
            },

            "总资产周转率": {
                "值": result.get("总资产周转率"),
                "单位": "次",
            },

            "流动比率": {
                "值": result.get("流动比率"),
                "单位": None,
            },

            "速动比率": {
                "值": result.get("速动比率"),
                "单位": None,
            },

            "资产负债率": {
                "值": result.get("资产负债率"),
                "单位": "%",
            },

            "每股经营现金流": {
                "值": result.get("每股经营现金流"),
                "单位": "元",
            },
        }

        # 注意：
        # 经营现金流与净利润比率_原始值
        # 现在直接不交给LLM
        #
        # 在我们确认AkShare/Sina真实口径之前，
        # 宁可少一个指标，也不要让模型误解。

        descriptions = []

        revenue_growth = result.get("主营业务收入增长率")
        profit_growth = result.get("净利润增长率")

        if revenue_growth is not None:
            if revenue_growth > 0:
                descriptions.append(
                    f"主营业务收入增长率为正，为{revenue_growth:.2f}%"
                )
            elif revenue_growth < 0:
                descriptions.append(
                    f"主营业务收入增长率为负，为{revenue_growth:.2f}%"
                )

        if profit_growth is not None:
            if profit_growth > 0:
                descriptions.append(
                    f"净利润增长率为正，为{profit_growth:.2f}%"
                )
            elif profit_growth < 0:
                descriptions.append(
                    f"净利润增长率为负，为{profit_growth:.2f}%"
                )

        if (
            revenue_growth is not None
            and profit_growth is not None
        ):
            if revenue_growth > 0 and profit_growth < 0:
                descriptions.append(
                    "报告期主营业务收入增长率为正，"
                    "但净利润增长率为负"
                )

        safe_result["允许使用的描述性结论"] = descriptions

        safe_result["_internal_constraints"] = [
            "不得使用高、低、优秀、较差、健康等相对评价词",
            "不得引用行业水平、历史水平或经验阈值",
            "不得将应收账款周转率解释为议价能力",
            "不得将存货周转率解释为具体行业商业模式",
            "不得根据资产负债率自行判断负债水平高低",
            "不得根据流动比率自行判断偿债风险高低",
            "不得根据净利率自行推断定价权或成本控制能力",
        ]

        safe_result = remove_none_fields(safe_result)

        return safe_result

    # 其他工具暂时原样返回
    return result

# Define the function to execute tools
def call_tool(state):
    messages = state["messages"]
    last_message = messages[-1]

    tool_calls = last_message.additional_kwargs.get("tool_calls", [])

    tool_messages = []

    for tool_call in tool_calls:
        tool_name = tool_call["function"]["name"]
        tool_args = json.loads(
            tool_call["function"]["arguments"]
        )
        tool_call_id = tool_call["id"]

        log_section(
            "Tool",
            "RUN TOOL",
        )
        log_summary(
            "Tool",
            "工具名称",
            tool_name,
        )
        log_summary(
            "Tool",
            "工具参数",
            tool_args,
        )

        action = ToolInvocation(
            tool=tool_name,
            tool_input=tool_args,
        )

        response = tool_executor.invoke(action)

        log_summary(
            "Tool",
            "工具原始结果",
            response,
        )

        # ==============================
        # 安全清洗
        # ==============================

        safe_response = sanitize_tool_result(
            tool_name,
            response,
        )

        log_summary(
            "Tool",
            "传给LLM的安全结果",
            safe_response,
        )

        tool_message = ToolMessage(
            content=json.dumps(
                safe_response,
                ensure_ascii=False,
            ),
            tool_call_id=tool_call_id,
        )

        tool_messages.append(tool_message)

    return {"messages": tool_messages}


# Define a new graph
workflow = StateGraph(AgentState)

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("action", call_tool)

# Set the entrypoint as `agent`
# This means that this node is the first one called
workflow.set_entry_point("agent")

# We now add a conditional edge
workflow.add_conditional_edges(
    # First, we define the start node. We use `agent`.
    "agent",
    # Next, we pass in the function that will determine which node is called next.
    should_continue,
    # END is a special node marking that the graph should finish.
    {
        # If `tools`, then we call the tool node.
        "continue": "action",
        # Otherwise we finish.
        "end": END
    }
)

# We now add a normal edge from `tools` to `agent`.
workflow.add_edge('action', 'agent')

# Finally, we compile it!
agent = workflow.compile()
