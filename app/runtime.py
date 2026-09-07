import copy
import time
import traceback
from typing import Any, Callable


_MEMORY_CACHE: dict[tuple, dict[str, Any]] = {}


def safe_error_message(
    error: Exception,
) -> str:
    message = str(error).strip()

    if not message:
        message = error.__class__.__name__

    return message[:300]


def build_failure_result(
    source: str,
    message: str,
    stage: str | None = None,
    retryable: bool = True,
    **metadata: Any,
) -> dict[str, Any]:
    result = {
        "状态": "失败",
        "数据可用": False,
        "来源": source,
        "错误信息": str(message)[:300],
        "可重试": retryable,
    }

    if stage:
        result["阶段"] = stage

    for key, value in metadata.items():
        if value is not None:
            result[key] = value

    return result


def is_failure_result(
    value: Any,
) -> bool:
    return (
        isinstance(value, dict)
        and value.get("状态") == "失败"
    )


def _cache_key(
    namespace: str,
    args: tuple,
    kwargs: dict,
) -> tuple:
    normalized_kwargs = tuple(
        sorted(kwargs.items())
    )

    return (namespace, args, normalized_kwargs)


def cache_get(
    namespace: str,
    *args,
    **kwargs,
) -> Any | None:
    key = _cache_key(
        namespace,
        args,
        kwargs,
    )

    item = _MEMORY_CACHE.get(key)

    if not item:
        return None

    expires_at = item["expires_at"]

    if expires_at < time.time():
        _MEMORY_CACHE.pop(key, None)

        return None

    return copy.deepcopy(item["value"])


def cache_set(
    namespace: str,
    value: Any,
    ttl_seconds: int,
    *args,
    **kwargs,
) -> None:
    key = _cache_key(
        namespace,
        args,
        kwargs,
    )

    _MEMORY_CACHE[key] = {
        "expires_at": time.time() + ttl_seconds,
        "value": copy.deepcopy(value),
    }


def cached_call(
    namespace: str,
    ttl_seconds: int,
    producer: Callable[[], Any],
    *args,
    **kwargs,
) -> Any:
    cached = cache_get(
        namespace,
        *args,
        **kwargs,
    )

    if cached is not None:
        log_info(
            "Cache",
            f"HIT {namespace} {kwargs or args}",
        )

        return cached

    log_info(
        "Cache",
        f"MISS {namespace} {kwargs or args}",
    )

    value = producer()

    if not is_failure_result(value):
        cache_set(
            namespace,
            value,
            ttl_seconds,
            *args,
            **kwargs,
        )

    return value


def log_info(
    component: str,
    message: str,
) -> None:
    print(f"\n[{component}] {message}")


def log_section(
    component: str,
    title: str,
) -> None:
    log_info(
        component,
        f"========== {title} ==========",
    )


def log_summary(
    component: str,
    label: str,
    value: Any,
) -> None:
    log_info(
        component,
        f"{label}: {summarize_for_log(value)}",
    )


def log_exception(
    component: str,
    error: Exception,
    stage: str | None = None,
) -> None:
    prefix = (
        f"{stage}: "
        if stage
        else ""
    )

    log_info(
        component,
        f"{prefix}{safe_error_message(error)}",
    )


def summarize_for_log(
    value: Any,
    max_items: int = 8,
) -> Any:
    """
    输出调试摘要，避免把价格序列和财务历史长列表刷屏。
    """

    if isinstance(value, dict):
        summary = {}

        for key, item in value.items():
            if isinstance(item, list):
                summary[key] = (
                    f"<list len={len(item)}>"
                )

            elif isinstance(item, dict):
                summary[key] = (
                    f"<dict keys={list(item.keys())[:max_items]}>"
                )

            else:
                summary[key] = item

        return summary

    if isinstance(value, list):
        return f"<list len={len(value)}>"

    return value


def traceback_summary(
    error: Exception,
) -> str:
    lines = traceback.format_exception_only(
        type(error),
        error,
    )

    return "".join(lines).strip()[:500]
