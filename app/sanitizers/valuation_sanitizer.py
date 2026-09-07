from app.runtime import is_failure_result


def sanitize_dcf_result(
    result,
):

    if not isinstance(
        result,
        dict,
    ):

        return result

    if is_failure_result(
        result
    ):
        return result

    return dict(result)
