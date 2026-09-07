from app.analytics.financial_trend import (
    build_financial_trend_analysis,
)
from app.debug_helpers import (
    log_financial_trend_engine_smoke_result,
)


FINANCIAL_TREND_SMOKE_DATA = {

    "股票代码":
        "600519",

    "财务历史序列": [

        {
            "报告期":
                "2025-06-30",

            "每股收益": {
                "值": 36.94,
                "单位": "元/股",
            },

            "净资产收益率ROE": {
                "值": 19.03,
                "单位": "%",
            },

            "销售净利率": {
                "值": 52.10,
                "单位": "%",
            },

            "主营业务收入增长率": {
                "值": 9.1032,
                "单位": "%",
            },

            "净利润增长率": {
                "值": 8.8236,
                "单位": "%",
            },

            "资产负债率": {
                "值": 14.5,
                "单位": "%",
            },

            "流动比率": {
                "值": 6.1,
                "单位": "无量纲",
            },

            "每股经营现金流": {
                "值": 50.0,
                "单位": "元/股",
            },
        },

        {
            "报告期":
                "2026-06-30",

            "每股收益": {
                "值": 36.8243,
                "单位": "元/股",
            },

            "净资产收益率ROE": {
                "值": 17.72,
                "单位": "%",
            },

            "销售净利率": {
                "值": 50.7516,
                "单位": "%",
            },

            "主营业务收入增长率": {
                "值": 1.4699,
                "单位": "%",
            },

            "净利润增长率": {
                "值": -2.029,
                "单位": "%",
            },

            "资产负债率": {
                "值": 15.1931,
                "单位": "%",
            },

            "流动比率": {
                "值": 5.5895,
                "单位": "无量纲",
            },

            "每股经营现金流": {
                "值": 56.5489,
                "单位": "元/股",
            },
        },
    ],
}


def run_smoke_test() -> dict:
    result = build_financial_trend_analysis(
        FINANCIAL_TREND_SMOKE_DATA
    )

    log_financial_trend_engine_smoke_result(
        result
    )

    return result


if __name__ == "__main__":
    run_smoke_test()
