# 项目总结

## 项目定位

本项目是一个面向 A 股分析的多智能体系统。它把自然语言金融分析问题拆分为市场、财务、估值三个专业任务，再通过综合层、报告层和 Dashboard 层形成完整展示。

项目的核心价值不是让大模型直接给出投资判断，而是把数据获取、确定性计算、模型解释、结构化状态和前端展示拆开，让每一步都有明确边界。

## 已完成能力

- Supervisor 根据用户问题选择需要执行的专业 Agent。
- Market Agent 支持股票解析和近 60 个交易日行情分析。
- Financial Agent 支持最新财务指标获取，并补充最近 12 期历史财务序列。
- Financial Trend Engine 使用 Python 进行确定性同比趋势计算。
- Valuation Agent 支持基于用户输入参数的 DCF 确定性估值。
- Synthesis Agent 基于安全观察生成综合分析，并支持 Python fallback。
- Report Agent 汇总各模块报告，并支持动态章节编号。
- Dashboard Builder 输出稳定的 `dashboard_data` schema。
- Streamlit 前端展示市场、财务、估值、综合分析和最终报告。
- Runtime 层提供统一失败对象、TTL 内存缓存和摘要日志。

## 安全设计

- Structured State 保留完整业务数据，用于 Dashboard 和确定性计算。
- LLM Context 只接收经过 sanitizer 裁剪后的安全字段。
- Market 不把完整价格序列发送给 Qwen。
- Financial 不把完整财务历史发送给 Qwen。
- DCF 不由模型计算，必须通过 Python 工具确定性计算。
- Synthesis 不重新计算工具结果，只基于安全观察综合。
- Validator 发现不合规输出时触发 fallback 或放弃摘要。

## 稳定性设计

- 股票解析、行情历史、财务快照、财务历史使用 TTL 缓存。
- AkShare / 网络 / Qwen / Dashboard 构建异常均有兜底。
- 失败对象统一包含状态、来源、阶段、错误信息、是否可重试。
- Dashboard 支持局部失败，不让单个模块拖垮整页。
- 本地测试入口只输出摘要，避免打印完整长序列。

## 主要入口

- Dashboard：`app/dashboard/streamlit_app.py`
- 主多智能体图：`app/multi_agent.py`
- 数据工具：`app/tools.py`
- 运行时 helper：`app/runtime.py`
- 本地调试 helper：`app/debug_helpers.py`
- 演示手册：`docs/DEMO_GUIDE.md`
- 答辩讲稿：`docs/PRESENTATION_SCRIPT.md`

## 推荐演示问题

```text
请综合分析贵州茅台的市场表现和最新财务指标，并以自由现金流1亿元、增长率5%、折现率10%、永续增长率2%、预测5年进行DCF估值。
```

## 当前验收状态

- 语法检查通过。
- 财务趋势冒烟测试通过。
- Dashboard Builder 冒烟测试通过。
- 三 Agent 全链路通过。
- Streamlit 首页与健康检查通过。
- README、演示手册、答辩讲稿和首屏截图已补齐。

## 后续可扩展方向

- 增加更多 A 股样例和失败降级演示样例。
- 为核心 sanitizer / validator / builder 增加 pytest 自动化测试。
- 增加 Dashboard 截图或短录屏，形成完整演示包。
- 支持更多财务数据源或离线 mock 数据源，降低演示对网络的依赖。
- 将旧单 Agent 入口逐步迁移或标记为 legacy，避免与主多智能体链路混淆。
