import akshare as ak
import pandas as pd
from langchain.tools import tool
import re

from app.runtime import (
    build_failure_result,
    cached_call,
    is_failure_result,
    log_exception,
    safe_error_message,
)

A_SHARE_SECURITY_MASTER = {
    "贵州茅台": "600519",
    "五粮液": "000858",
}

CACHE_TTL_STOCK_SEARCH = 24 * 60 * 60
CACHE_TTL_MARKET_HISTORY = 10 * 60
CACHE_TTL_FINANCIAL_DATA = 6 * 60 * 60


def cached_external_data(
    namespace: str,
    ttl_seconds: int,
    source: str,
    stage: str,
    producer,
    **cache_key,
):
    try:

        return cached_call(
            namespace,
            ttl_seconds,
            producer,
            **cache_key,
        )

    except Exception as error:

        log_exception(
            source,
            error,
            stage,
        )

        return build_failure_result(
            source=source,
            message=safe_error_message(
                error
            ),
            stage=stage,
            **cache_key,
        )


def fetch_financial_analysis_indicator_df(
    stock_code: str,
):
    def fetch_df():
        return ak.stock_financial_analysis_indicator(
            symbol=stock_code
        )

    return cached_external_data(
        namespace="ak_financial_analysis_indicator_df",
        ttl_seconds=CACHE_TTL_FINANCIAL_DATA,
        source="AkShare",
        stage="stock_financial_analysis_indicator",
        producer=fetch_df,
        stock_code=stock_code,
    )

def normalize_a_share_code(stock_code: str) -> str:
    """
    将各种可能的A股股票代码格式统一转换为6位纯数字代码。

    支持：
    600519
    600519.SH
    SH600519
    sh600519
    000001.SZ
    SZ000001

    最终统一返回：
    600519
    000001
    """

    stock_code = str(stock_code).strip()

    # 提取连续6位数字
    match = re.search(r"\d{6}", stock_code)

    if not match:
        raise ValueError(
            f"无法从输入 {stock_code!r} 中识别6位A股股票代码"
        )

    return match.group()

@tool
def roe(net_income: float, equity: float) -> float:
    """
    根据已知的净利润和股东权益计算 ROE。

    重要规则：
    只有当 net_income 和 equity 已经由用户明确提供，
    或由其他数据工具真实返回时，才能调用本工具。

    严禁猜测、估算或自行编造 net_income 和 equity。
    如果缺少任一参数，不要调用本工具。
    """
    return net_income / equity


@tool
def roic(
    operating_income: float,
    total_debt: float,
    equity: float,
    cash_and_equivalents: float,
    tax_rate: float = 0.35,
) -> float:
    """
    根据真实财务数据计算 ROIC。

    只有当 operating_income、total_debt、equity、
    cash_and_equivalents 已由用户提供或数据工具真实返回时才能调用。

    严禁自行猜测或补充任何财务数据。
    如果缺少必要参数，不要调用本工具。
    """
    net_operating_profit_after_tax = operating_income * (1 - tax_rate)
    invested_capital = total_debt + equity - cash_and_equivalents
    return net_operating_profit_after_tax / invested_capital


@tool
def owner_earnings(
    net_income: float,
    depreciation_amortization: float = 0.0,
    capital_expenditures: float = 0.0
):
    """
    根据真实财务数据计算 Owner Earnings。

    只有当所需数据由用户提供或其他数据工具真实返回时才能调用。

    不允许为了完成分析而自行估算净利润、折旧摊销或资本开支。
    """
    return net_income + depreciation_amortization - capital_expenditures



@tool
def discounted_cash_flow(
    free_cash_flow: float,
    growth_rate: float = 0.05,
    discount_rate: float = 0.10,
    terminal_growth_rate: float = 0.02,
    num_years: int = 5,
):
    """
    使用简化 DCF 模型计算企业价值。

    参数：
    free_cash_flow:
        当前自由现金流。
        必须来自用户明确提供的数据或真实数据工具，
        不得由模型猜测。

    growth_rate:
        预测期自由现金流年增长率。

    discount_rate:
        折现率。

    terminal_growth_rate:
        永续增长率。

    num_years:
        显式预测期年数。

    注意：
    growth_rate、discount_rate、
    terminal_growth_rate 和 num_years
    若使用默认值，必须向用户明确披露。
    """

    # ---------------------------------
    # 参数检查
    # ---------------------------------

    if free_cash_flow is None:
        raise ValueError(
            "free_cash_flow 不能为空"
        )

    if num_years <= 0:
        raise ValueError(
            "num_years 必须大于0"
        )

    if discount_rate <= terminal_growth_rate:
        raise ValueError(
            "discount_rate 必须大于 "
            "terminal_growth_rate"
        )

    # ---------------------------------
    # 显式预测期
    # ---------------------------------

    projected_cash_flows = []

    present_value_cash_flows = []

    total_present_value = 0.0

    for year in range(
        1,
        num_years + 1,
    ):

        projected_fcf = (
            free_cash_flow
            * (1 + growth_rate) ** year
        )

        present_value = (
            projected_fcf
            / (1 + discount_rate) ** year
        )

        projected_cash_flows.append({
            "年份": year,
            "预测自由现金流": projected_fcf,
            "折现后自由现金流": present_value,
        })

        present_value_cash_flows.append(
            present_value
        )

        total_present_value += (
            present_value
        )

    # ---------------------------------
    # Terminal Value
    # ---------------------------------

    final_year_fcf = (
        free_cash_flow
        * (1 + growth_rate) ** num_years
    )

    terminal_cash_flow = (
        final_year_fcf
        * (1 + terminal_growth_rate)
    )

    terminal_value = (
        terminal_cash_flow
        / (
            discount_rate
            - terminal_growth_rate
        )
    )

    discounted_terminal_value = (
        terminal_value
        / (1 + discount_rate) ** num_years
    )

    # ---------------------------------
    # Enterprise Value
    # ---------------------------------

    enterprise_value = (
        total_present_value
        + discounted_terminal_value
    )

    # ---------------------------------
    # 必须 RETURN
    # ---------------------------------

    return {
        "输入参数": {
            "自由现金流": free_cash_flow,
            "增长率": growth_rate,
            "折现率": discount_rate,
            "永续增长率": terminal_growth_rate,
            "预测年数": num_years,
        },

        "预测期现金流": (
            projected_cash_flows
        ),

        "预测期现金流现值合计": (
            total_present_value
        ),

        "终值": terminal_value,

        "终值现值": (
            discounted_terminal_value
        ),

        "企业价值": enterprise_value,
    }

@tool
def get_a_share_quote(stock_code: str):
    """
    获取A股最近一个交易日的单日行情，包括：
    开盘价、最高价、最低价、收盘价和成交量。

    参数：
    - stock_code: 6位A股股票代码，例如：
      - 600519
      - 000001
      - 300750

    适用于用户明确询问：
    - 最新行情
    - 最近一个交易日OHLC
    - 当日最高价/最低价/开盘价

    如果用户询问20日、60日等一段时间的市场表现，
    应使用 get_a_share_history，不应同时调用本工具。
    """

    # 判断股票所属交易所
    # 6、9开头一般为上海市场
    stock_code = normalize_a_share_code(stock_code)

    if stock_code.startswith(("6", "9")):
        symbol = "sh" + stock_code
    else:
        symbol = "sz" + stock_code

    def fetch_quote():

        # 使用新浪数据源获取A股日线数据
        df = ak.stock_zh_a_daily(
            symbol=symbol,
            start_date="20260101",
            end_date="20261231",
            adjust="qfq"
        )

        # 如果没有获取到数据
        if df.empty:
            return build_failure_result(
                source="AkShare",
                stage="get_a_share_quote",
                message=(
                    f"未找到股票代码 {stock_code} 的行情数据"
                ),
                stock_code=stock_code,
            )

        # 按日期排序，防止数据顺序异常
        df = df.sort_values("date").reset_index(drop=True)

        # 获取最近一个交易日
        row = df.iloc[-1]

        return {
            "代码": stock_code,
            "日期": str(row["date"]),
            "开盘价": float(row["open"]),
            "最高价": float(row["high"]),
            "最低价": float(row["low"]),
            "收盘价": float(row["close"]),
            "成交量": float(row["volume"]),
        }

    return cached_external_data(
        namespace="a_share_quote",
        ttl_seconds=CACHE_TTL_MARKET_HISTORY,
        source="AkShare",
        stage="get_a_share_quote",
        producer=fetch_quote,
        stock_code=stock_code,
    )


@tool
def get_financial_indicators(stock_code: str):
    """
    获取A股上市公司的最新一期核心财务指标。

    stock_code 示例：
    - 600519
    - 000001
    - 300750
    """

    stock_code = normalize_a_share_code(stock_code)

    def fetch_financial_indicators():

        df = fetch_financial_analysis_indicator_df(
            stock_code
        )

        if is_failure_result(
            df
        ):
            return df

        if df is None or df.empty:
            return build_failure_result(
                source="AkShare",
                stage="get_financial_indicators",
                message=(
                    f"未找到股票代码 {stock_code} 的财务指标数据"
                ),
                stock_code=stock_code,
            )

        # 数据按照时间正序排列，因此最后一行为最新报告期
        row = df.iloc[-1]

        indicators = {
            "股票代码": stock_code,
            "报告期": str(row["日期"]),

            # 盈利能力
            "每股收益": row["摊薄每股收益(元)"],
            "净资产收益率ROE": row["净资产收益率(%)"],
            "加权净资产收益率ROE": row["加权净资产收益率(%)"],
            "销售毛利率": row["销售毛利率(%)"],
            "销售净利率": row["销售净利率(%)"],
            "总资产净利润率": row["总资产净利润率(%)"],

            # 成长能力
            "主营业务收入增长率": row["主营业务收入增长率(%)"],
            "净利润增长率": row["净利润增长率(%)"],
            "净资产增长率": row["净资产增长率(%)"],

            # 营运能力
            "应收账款周转率": row["应收账款周转率(次)"],
            "存货周转率": row["存货周转率(次)"],
            "总资产周转率": row["总资产周转率(次)"],

            # 偿债能力
            "流动比率": row["流动比率"],
            "速动比率": row["速动比率"],
            "资产负债率": row["资产负债率(%)"],

            # 现金流
            "每股经营现金流": row["每股经营性现金流(元)"],
            "经营现金流与净利润比率_原始值":row["经营现金净流量与净利润的比率(%)"],
        }

        # 将 NaN 转换成 None，避免给大模型返回 nan
        indicators = {
            key: None if pd.isna(value) else value
            for key, value in indicators.items()
        }

        return indicators

    return cached_external_data(
        namespace="financial_indicators",
        ttl_seconds=CACHE_TTL_FINANCIAL_DATA,
        source="AkShare",
        stage="get_financial_indicators",
        producer=fetch_financial_indicators,
        stock_code=stock_code,
    )

# =========================================================
# Financial History Tool
# =========================================================

@tool
def get_financial_history(
    stock_code: str,
    periods: int = 12,
):
    """
    获取A股历史财务指标序列。

    stock_code 应为6位A股股票代码，例如600519。

    periods 表示最多返回最近多少期财务报告，
    默认返回最近12期。

    本工具只返回数据源中真实存在的历史财务指标，
    不补齐、不预测、不插值缺失数据。
    """

    # =========================================
    # 1. 参数防御
    # =========================================

    stock_code = normalize_a_share_code(
        stock_code
    )

    if periods <= 0:
        raise ValueError(
            "periods 必须大于0"
        )

    # =========================================
    # 2. 获取 AkShare 财务指标
    # =========================================

    df = (
        fetch_financial_analysis_indicator_df(
            stock_code
        )
    )

    if is_failure_result(
        df
    ):
        return df

    if df is None or df.empty:

        return build_failure_result(
            source="AkShare",
            stage="get_financial_history",
            message=(
                f"未找到股票代码 {stock_code} 的财务历史数据"
            ),
            stock_code=stock_code,
        )

    df = df.copy()

    # =========================================
    # 3. 日期标准化
    # =========================================

    if "日期" not in df.columns:

        raise ValueError(
            "财务指标数据缺少日期字段"
        )

    df["_报告期"] = (
        pd.to_datetime(
            df["日期"],
            format="%Y-%m-%d",
            errors="coerce",
        )
    )

    df = (
        df[
            df["_报告期"].notna()
        ]
        .copy()
    )

    if df.empty:

        return {
            "股票代码": stock_code,
            "实际报告期数量": 0,
            "财务历史序列": [],
        }

    # =========================================
    # 4. 时间排序
    # =========================================

    df = (
        df
        .sort_values(
            "_报告期"
        )
        .reset_index(
            drop=True
        )
    )

    # =========================================
    # 5. 最近 N 期
    # =========================================

    recent = (
        df
        .tail(
            periods
        )
        .copy()
    )

    # =========================================
    # 6. 安全读取数值
    # =========================================

    def safe_value(
        row,
        column_name: str,
    ):
        """
        None / NaN -> None
        数值 -> float
        """

        if column_name not in row.index:
            return None

        value = row[
            column_name
        ]

        if pd.isna(
            value
        ):
            return None

        try:

            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return value

    # =========================================
    # 7. AkShare 字段映射
    # =========================================

    column_mapping = {

        # -------------------------------------
        # 盈利能力
        # -------------------------------------

        "每股收益":
            "摊薄每股收益(元)",

        "净资产收益率ROE":
            "净资产收益率(%)",

        "加权净资产收益率ROE":
            "加权净资产收益率(%)",

        "销售毛利率":
            "销售毛利率(%)",

        "销售净利率":
            "销售净利率(%)",

        "总资产净利润率":
            "总资产净利润率(%)",

        # -------------------------------------
        # 成长能力
        # -------------------------------------

        "主营业务收入增长率":
            "主营业务收入增长率(%)",

        "净利润增长率":
            "净利润增长率(%)",

        "净资产增长率":
            "净资产增长率(%)",

        # -------------------------------------
        # 运营效率
        # -------------------------------------

        "应收账款周转率":
            "应收账款周转率(次)",

        "存货周转率":
            "存货周转率(次)",

        "总资产周转率":
            "总资产周转率(次)",

        # -------------------------------------
        # 偿债能力
        # -------------------------------------

        "流动比率":
            "流动比率",

        "速动比率":
            "速动比率",

        "资产负债率":
            "资产负债率(%)",

        # -------------------------------------
        # 现金流
        # -------------------------------------

        "每股经营现金流":
            "每股经营性现金流(元)",
    }

    # =========================================
    # 8. 构建历史财务序列
    # =========================================

    financial_series = []

    for _, row in recent.iterrows():

        item = {
            "报告期":
                row[
                    "_报告期"
                ].strftime(
                    "%Y-%m-%d"
                )
        }

        for (
            output_name,
            source_column,
        ) in column_mapping.items():

            value = safe_value(
                row,
                source_column,
            )

            if value is not None:

                item[
                    output_name
                ] = value

        financial_series.append(
            item
        )

    # =========================================
    # 9. 返回
    # =========================================

    return {
        "股票代码":
            stock_code,

        "实际报告期数量":
            len(
                financial_series
            ),

        "财务历史序列":
            financial_series,
    }

@tool
def get_a_share_history(
    stock_code: str,
    days: int = 60
):
    """
    获取A股历史行情及区间统计指标。

    stock_code 应为6位A股代码，例如600519。
    如果收到600519.SH、SH600519等格式，
    工具会自动转换为标准6位股票代码。

    本工具已经包含：
    - 数据截止日期
    - 最新收盘价
    - 最近交易日成交量
    - 20日/60日收益率
    - 20日/60日均价
    - 年化波动率
    - 最大回撤
    - 成交量统计
    - 最近N个交易日价格时间序列
    - MA20 / MA60 时间序列
    """

    # =========================
    # 0. 参数检查
    # =========================

    stock_code = normalize_a_share_code(
        stock_code
    )

    if days <= 0:
        raise ValueError(
            "days 必须大于0"
        )

    # =========================
    # 1. 判断交易所
    # =========================

    if stock_code.startswith(
        ("6", "9")
    ):
        symbol = "sh" + stock_code
    else:
        symbol = "sz" + stock_code

    # =========================
    # 2. 获取历史行情
    # =========================

    def fetch_market_history_df():
        return ak.stock_zh_a_daily(
            symbol=symbol,
            start_date="20250101",
            end_date="20261231",
            adjust="qfq"
        )

    df = cached_external_data(
        namespace="a_share_history_df",
        ttl_seconds=CACHE_TTL_MARKET_HISTORY,
        source="AkShare",
        stage="get_a_share_history",
        producer=fetch_market_history_df,
        stock_code=stock_code,
        days=days,
        adjust="qfq",
    )

    if is_failure_result(
        df
    ):
        return df

    if df is None or df.empty:
        return build_failure_result(
            source="AkShare",
            stage="get_a_share_history",
            message=(
                f"未找到股票代码 {stock_code} 的历史行情数据"
            ),
            stock_code=stock_code,
        )

    # 按日期排序
    df = (
        df
        .sort_values("date")
        .reset_index(drop=True)
    )

    # 至少需要2个交易日
    if len(df) < 2:
        return build_failure_result(
            source="AkShare",
            stage="get_a_share_history",
            message=(
                f"股票代码 {stock_code} 的历史数据不足"
            ),
            stock_code=stock_code,
        )

    # =========================
    # 3. 标准化数值列
    # =========================

    df["close"] = (
        df["close"]
        .astype(float)
    )

    df["volume"] = (
        df["volume"]
        .astype(float)
    )

    # =========================
    # 4. 在完整历史数据上计算均线
    # =========================
    #
    # 注意：
    # 必须先在完整df上算MA，
    # 再截取最近days天。
    #
    # 否则如果先截取60天，
    # 前19天MA20、前59天MA60
    # 会因为缺乏更早历史数据而为空。
    # =========================

    df["MA20"] = (
        df["close"]
        .rolling(
            window=20,
            min_periods=20
        )
        .mean()
    )

    df["MA60"] = (
        df["close"]
        .rolling(
            window=60,
            min_periods=60
        )
        .mean()
    )

    # =========================
    # 5. 截取最近N个交易日
    # =========================

    recent = (
        df
        .tail(days)
        .copy()
    )

    close = (
        recent["close"]
        .astype(float)
    )

    volume = (
        recent["volume"]
        .astype(float)
    )

    latest_close = float(
        close.iloc[-1]
    )

    # =========================
    # 6. 基础结果
    # =========================

    result = {
        "股票代码":
            stock_code,

        "数据截止日期":
            str(
                recent.iloc[-1]["date"]
            ),

        "实际交易日数量":
            len(recent),

        "最新收盘价":
            latest_close,

        "价格口径":
            "前复权",
    }

    # =========================
    # 7. 收益率
    # =========================

    if len(df) >= 21:

        close_20_days_ago = float(
            df["close"].iloc[-21]
        )

        result[
            "近20日收益率(%)"
        ] = (
            latest_close
            / close_20_days_ago
            - 1
        ) * 100

    else:

        result[
            "近20日收益率(%)"
        ] = None

    if len(df) >= 61:

        close_60_days_ago = float(
            df["close"].iloc[-61]
        )

        result[
            "近60日收益率(%)"
        ] = (
            latest_close
            / close_60_days_ago
            - 1
        ) * 100

    else:

        result[
            "近60日收益率(%)"
        ] = None

    # =========================
    # 8. 均线
    # =========================

    latest_ma20 = (
        df.iloc[-1]["MA20"]
    )

    if pd.notna(
        latest_ma20
    ):

        ma20 = float(
            latest_ma20
        )

        result[
            "20日均价"
        ] = ma20

        result[
            "当前价格相对20日均线(%)"
        ] = (
            latest_close
            / ma20
            - 1
        ) * 100

    else:

        result[
            "20日均价"
        ] = None

        result[
            "当前价格相对20日均线(%)"
        ] = None

    latest_ma60 = (
        df.iloc[-1]["MA60"]
    )

    if pd.notna(
        latest_ma60
    ):

        ma60 = float(
            latest_ma60
        )

        result[
            "60日均价"
        ] = ma60

        result[
            "当前价格相对60日均线(%)"
        ] = (
            latest_close
            / ma60
            - 1
        ) * 100

    else:

        result[
            "60日均价"
        ] = None

        result[
            "当前价格相对60日均线(%)"
        ] = None

    # =========================
    # 9. 波动率
    # =========================

    daily_returns = (
        close
        .pct_change()
        .dropna()
    )

    if len(
        daily_returns
    ) > 1:

        annualized_volatility = (
            daily_returns.std()
            * (252 ** 0.5)
            * 100
        )

        result[
            "年化波动率(%)"
        ] = float(
            annualized_volatility
        )

    else:

        result[
            "年化波动率(%)"
        ] = None

    # =========================
    # 10. 最大回撤
    # =========================

    running_max = (
        close
        .cummax()
    )

    drawdown = (
        close
        / running_max
        - 1
    )

    max_drawdown = (
        drawdown.min()
        * 100
    )

    result[
        "区间最大回撤(%)"
    ] = float(
        max_drawdown
    )

    # =========================
    # 11. 成交量
    # =========================

    result[
        "最近交易日成交量"
    ] = float(
        volume.iloc[-1]
    )

    if len(volume) >= 20:

        average_volume_20 = float(
            volume
            .tail(20)
            .mean()
        )

        result[
            "20日平均成交量"
        ] = (
            average_volume_20
        )

        if average_volume_20 != 0:

            result[
                "成交量相对20日均量"
            ] = (
                float(
                    volume.iloc[-1]
                )
                / average_volume_20
            )

        else:

            result[
                "成交量相对20日均量"
            ] = None

    else:

        result[
            "20日平均成交量"
        ] = None

        result[
            "成交量相对20日均量"
        ] = None

    # =========================
    # 12. 清理汇总指标中的NaN
    # =========================
    #
    # 注意：
    # 必须在加入“价格序列”之前处理。
    # 因为pd.isna(list)会返回数组。
    # =========================

    cleaned_result = {}

    for key, value in (
        result.items()
    ):

        if value is None:

            cleaned_result[
                key
            ] = None

        elif (
            isinstance(
                value,
                float
            )
            and pd.isna(
                value
            )
        ):

            cleaned_result[
                key
            ] = None

        else:

            cleaned_result[
                key
            ] = value

    result = cleaned_result

    # =========================
    # 13. 构造价格时间序列
    # =========================

    price_series = []

    for _, row in (
        recent.iterrows()
    ):

        row_ma20 = (
            None
            if pd.isna(
                row["MA20"]
            )
            else float(
                row["MA20"]
            )
        )

        row_ma60 = (
            None
            if pd.isna(
                row["MA60"]
            )
            else float(
                row["MA60"]
            )
        )

        price_series.append({
            "日期":
                str(
                    row["date"]
                ),

            "收盘价":
                float(
                    row["close"]
                ),

            "MA20":
                row_ma20,

            "MA60":
                row_ma60,
        })

    # =========================
    # 14. 加入时间序列
    # =========================

    result[
        "价格序列"
    ] = price_series

    return result

@tool
def search_a_share_stock(query: str):
    """
    根据A股股票名称或股票代码查找对应上市公司。

    query 可以是：
    - 股票代码，例如 "600519"
    - 完整股票名称，例如 "贵州茅台"
    - 部分名称，例如 "茅台"

    返回匹配的股票代码和股票名称。

    重要规则：
    本工具只用于股票名称和代码解析，
    不提供行情、财务或估值数据。
    """

    def fetch_stock_master():
        return ak.stock_info_a_code_name()

    df = cached_external_data(
        namespace="a_share_stock_master",
        ttl_seconds=CACHE_TTL_STOCK_SEARCH,
        source="AkShare",
        stage="search_a_share_stock",
        producer=fetch_stock_master,
        dataset="stock_info_a_code_name",
    )

    if is_failure_result(
        df
    ):
        return df

    if df is None or df.empty:
        return build_failure_result(
            source="AkShare",
            stage="search_a_share_stock",
            message="未获取到A股股票列表",
        )

    # 统一转成字符串，避免代码被解析成数字
    df["code"] = df["code"].astype(str).str.zfill(6)
    df["name"] = df["name"].astype(str)

    query = str(query).strip()

    # 1. 如果用户输入的是6位股票代码
    if query.isdigit():
        query = query.zfill(6)

        matched = df[df["code"] == query]

        if matched.empty:
            return f"未找到股票代码 {query}"

        row = matched.iloc[0]

        return {
            "股票代码": row["code"],
            "股票名称": row["name"],
            "匹配类型": "代码精确匹配",
        }

    # 2. 优先进行股票名称精确匹配
    exact_match = df[df["name"] == query]

    if not exact_match.empty:
        row = exact_match.iloc[0]

        return {
            "股票代码": row["code"],
            "股票名称": row["name"],
            "代码格式": "6位纯数字，不含交易所后缀",
            "匹配类型": "名称精确匹配",
        }

    # 3. 再进行名称模糊匹配
    fuzzy_match = df[
        df["name"].str.contains(
            query,
            case=False,
            na=False,
            regex=False,
        )
    ]

    if fuzzy_match.empty:
        return f"未找到与“{query}”匹配的A股股票"

    # 最多返回5个候选，防止一次给模型太多内容
    fuzzy_match = fuzzy_match.head(5)

    results = []

    for _, row in fuzzy_match.iterrows():
        results.append(
            {
                "股票代码": row["code"],
                "股票名称": row["name"],
            }
        )

    return {
        "查询词": query,
        "匹配类型": "名称模糊匹配",
        "候选数量": len(results),
        "候选股票": results,
    }

def compare_numeric(
    value_a,
    value_b,
    name_a,
    name_b,
    unit=None,
):
    if value_a is None or value_b is None:
        return {
            name_a: value_a,
            name_b: value_b,
            "单位": unit,
            "比较结果": "数据不足，无法比较",
        }

    difference = value_a - value_b

    if difference > 0:
        conclusion = f"{name_a}高于{name_b}"
    elif difference < 0:
        conclusion = f"{name_b}高于{name_a}"
    else:
        conclusion = "两者相同"

    # 百分比指标的差值使用“百分点”
    if unit == "%":
        difference_unit = "个百分点"
    else:
        difference_unit = unit

    return {
        name_a: value_a,
        name_b: value_b,
        "原始值单位": unit,
        "差值": abs(difference),
        "差值单位": difference_unit,
        "比较结果": conclusion,
    }

def resolve_a_share_stock(query: str):
    """
    内部股票解析函数。

    输入可以是：
    贵州茅台
    600519
    600519.SH

    返回标准化股票代码和名称。
    """

    query = str(query).strip()

    # 1. 名称精确匹配：优先使用本地 Security Master
    if query in A_SHARE_SECURITY_MASTER:
        return {
            "股票代码": A_SHARE_SECURITY_MASTER[query],
            "股票名称": query,
        }

    # 2. 输入本身是股票代码
    code_match = re.search(r"\d{6}", query)

    if code_match:
        code = normalize_a_share_code(query)

        for name, saved_code in A_SHARE_SECURITY_MASTER.items():
            if saved_code == code:
                return {
                    "股票代码": code,
                    "股票名称": name,
                }

    # 3. 再尝试 AkShare
    result = search_a_share_stock.invoke({
        "query": query
    })

    if is_failure_result(
        result
    ):
        raise ValueError(
            result.get(
                "错误信息",
                f"无法解析股票：{query}",
            )
        )

    if (
        isinstance(result, dict)
        and "股票代码" in result
        and "股票名称" in result
    ):
        return {
            "股票代码": result["股票代码"],
            "股票名称": result["股票名称"],
        }

    raise ValueError(
        f"无法解析股票：{query}"
    )

@tool
def compare_a_share_companies(
    stock_a: str,
    stock_b: str,
    days: int = 60,
):
    """
    横向比较两只A股股票的历史市场表现和最新财务指标。

    stock_a 和 stock_b 可以直接使用股票名称，例如：
    - 贵州茅台
    - 五粮液

    也可以使用6位股票代码。

    本工具会自动：
    1. 解析股票名称和代码
    2. 获取历史行情
    3. 获取最新财务指标
    4. 使用Python计算两家公司指标差异

    模型不得自行计算两家公司之间的指标差值。
    """

    # =====================================
    # 1. 股票解析
    # =====================================

    company_a = resolve_a_share_stock(stock_a)
    company_b = resolve_a_share_stock(stock_b)

    code_a = company_a["股票代码"]
    code_b = company_b["股票代码"]

    name_a = company_a["股票名称"]
    name_b = company_b["股票名称"]

    # =====================================
    # 2. 获取行情
    # =====================================

    history_a = get_a_share_history.invoke({
        "stock_code": code_a,
        "days": days,
    })

    history_b = get_a_share_history.invoke({
        "stock_code": code_b,
        "days": days,
    })

    # =====================================
    # 3. 获取财务指标
    # =====================================

    financial_a = get_financial_indicators.invoke({
        "stock_code": code_a,
    })

    financial_b = get_financial_indicators.invoke({
        "stock_code": code_b,
    })

    # =====================================
    # 4. 市场表现比较
    # =====================================

    market_comparison = {
        "近20日收益率": compare_numeric(
            history_a.get("近20日收益率(%)"),
            history_b.get("近20日收益率(%)"),
            name_a,
            name_b,
            "%"
        ),

        "近60日收益率": compare_numeric(
            history_a.get("近60日收益率(%)"),
            history_b.get("近60日收益率(%)"),
            name_a,
            name_b,
            "%"
        ),

        "年化波动率": compare_numeric(
            history_a.get("年化波动率(%)"),
            history_b.get("年化波动率(%)"),
            name_a,
            name_b,
            "%"
        ),

        "区间最大回撤": compare_drawdown(
            history_a.get("区间最大回撤(%)"),
            history_b.get("区间最大回撤(%)"),
            name_a,
            name_b,
        ),
    }

    # =====================================
    # 5. 财务指标比较
    # =====================================

    financial_comparison = {
        "净资产收益率ROE": compare_numeric(
            financial_a.get("净资产收益率ROE"),
            financial_b.get("净资产收益率ROE"),
            name_a,
            name_b,
            "%"
        ),

        "加权净资产收益率ROE": compare_numeric(
            financial_a.get("加权净资产收益率ROE"),
            financial_b.get("加权净资产收益率ROE"),
            name_a,
            name_b,
            "%"
        ),

        "销售净利率": compare_numeric(
            financial_a.get("销售净利率"),
            financial_b.get("销售净利率"),
            name_a,
            name_b,
            "%"
        ),

        "主营业务收入增长率": compare_numeric(
            financial_a.get("主营业务收入增长率"),
            financial_b.get("主营业务收入增长率"),
            name_a,
            name_b,
            "%"
        ),

        "净利润增长率": compare_numeric(
            financial_a.get("净利润增长率"),
            financial_b.get("净利润增长率"),
            name_a,
            name_b,
            "%"
        ),

        "资产负债率": compare_numeric(
            financial_a.get("资产负债率"),
            financial_b.get("资产负债率"),
            name_a,
            name_b,
            "%"
        ),

        "每股经营现金流": compare_numeric(
            financial_a.get("每股经营现金流"),
            financial_b.get("每股经营现金流"),
            name_a,
            name_b,
            "元"
        ),
    }

    # =====================================
    # 6. 最终结构化输出
    # =====================================

    return {
        "公司A": company_a,
        "公司B": company_b,

        "比较区间交易日数量": days,

        "行情数据截止日期": {
            name_a: history_a.get("数据截止日期"),
            name_b: history_b.get("数据截止日期"),
        },

        "财务报告期": {
            name_a: financial_a.get("报告期"),
            name_b: financial_b.get("报告期"),
        },

        "市场表现比较": market_comparison,

        "财务指标比较": financial_comparison,

        "解释限制": [
            "只能依据当前比较结果描述两家公司谁高谁低",
            "不得引用行业平均值或市场平均值",
            "不得据此评价公司整体优劣",
            "波动率较高只表示两家公司之间相对较高，不代表市场意义上的高波动",
            "资产负债率较低只表示两家公司之间相对较低，不代表绝对意义上的低负债",
        ],
    }

def compare_drawdown(
    value_a,
    value_b,
    name_a,
    name_b,
):
    """
    比较最大回撤的绝对幅度。
    """

    if value_a is None or value_b is None:
        return {
            name_a: value_a,
            name_b: value_b,
            "单位": "%",
            "比较结果": "数据不足，无法比较",
        }

    abs_a = abs(value_a)
    abs_b = abs(value_b)

    difference = abs_a - abs_b

    if difference > 0:
        conclusion = f"{name_a}最大回撤幅度大于{name_b}"
    elif difference < 0:
        conclusion = f"{name_b}最大回撤幅度大于{name_a}"
    else:
        conclusion = "两者最大回撤幅度相同"

    return {
        name_a: value_a,
        name_b: value_b,
        "回撤幅度差": abs(difference),
        "单位": "个百分点",
        "比较结果": conclusion,
    }

# =========================================================
# Financial History Local Smoke Test
# =========================================================


from app.sanitizers.financial_sanitizer import (
    sanitize_financial_history,
)
if __name__ == "__main__":
    from app.debug_helpers import log_financial_history_smoke_result

    result = (
        get_financial_history.invoke({
            "stock_code":
                "600519",

            "periods":
                12,
        })
    )

    safe_result = (
        sanitize_financial_history(
            result
        )
    )

    log_financial_history_smoke_result(
        result,
        safe_result,
    )
