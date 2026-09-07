# 发布前检查清单

## 文件清单

- [x] `README.md` 已更新为当前 A 股多智能体系统说明。
- [x] `.env.example` 已更新为 `DASHSCOPE_API_KEY`。
- [x] `Dockerfile` 已改为 Streamlit Dashboard 入口。
- [x] `pyproject.toml` 已显式声明 `langchain`。
- [x] `poetry.lock` 已刷新。
- [x] `docs/DEMO_GUIDE.md` 已新增。
- [x] `docs/PRESENTATION_SCRIPT.md` 已新增。
- [x] `docs/PROJECT_SUMMARY.md` 已新增。
- [x] `docs/assets/dashboard-home.png` 已新增。

## 验证命令

```bash
poetry check
poetry run python -m compileall app
poetry run python -m app.test_financial_trend
poetry run python -m app.dashboard.builder
poetry run python -m app.multi_agent
poetry run streamlit run app/dashboard/streamlit_app.py --server.port 8502
```

## 已验证结果

- [x] Poetry 配置检查通过。
- [x] Python 语法检查通过。
- [x] 财务趋势核心冒烟测试通过。
- [x] Dashboard Builder 冒烟测试通过。
- [x] 三 Agent 全链路通过。
- [x] Streamlit 首页返回 `200`。
- [x] Streamlit `/healthz` 返回 `ok`。
- [x] 日志保持摘要化，长序列显示为 `<list len=...>`。
- [x] Market LLM Context 不包含完整价格序列。
- [x] Financial LLM Context 不包含完整财务历史。
- [x] DCF 仍由 Python 工具确定性计算。
- [x] Synthesis fallback 仍可触发。

## 提交建议

建议提交时按下面范围描述：

```text
Finalize documentation, demo materials, and release checklist
```

建议重点说明：

- 更新 README、环境模板和 Dockerfile。
- 增加演示手册、答辩讲稿、项目总结和 Dashboard 首屏截图。
- 保持现有多智能体链路、安全边界、缓存和异常降级机制不变。
- 补齐显式 `langchain` 依赖并刷新锁文件。

## 注意事项

- 当前目录没有检测到 `.git` 元数据，无法在本地生成真实 git diff 或 commit。
- `__pycache__` 已在 `.gitignore` 中；本机安全策略阻止了自动递归删除缓存目录。
- `.env` 包含本地私密配置，已被 `.gitignore` 忽略，不应提交。
- 演示依赖 AkShare 网络接口和 DashScope API，正式展示前建议提前跑一次 `app.multi_agent` 热身缓存。
