import time

START_TIME = time.time()

metrics = {
    "total_requests": 0,
    "successful_requests": 0,
    "error_requests": 0,
    "total_response_time": 0.0,
    "recent_errors": []
}


def record_request(status_code: int, response_time: float, path: str, method: str):
    metrics["total_requests"] += 1
    metrics["total_response_time"] += response_time

    if status_code >= 400:
        metrics["error_requests"] += 1
        metrics["recent_errors"].append({
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_time": response_time
        })

        metrics["recent_errors"] = metrics["recent_errors"][-10:]
    else:
        metrics["successful_requests"] += 1


def get_metrics():
    uptime = round(time.time() - START_TIME, 2)

    total = metrics["total_requests"]
    avg_response_time = 0

    if total > 0:
        avg_response_time = round(metrics["total_response_time"] / total, 4)

    return {
        "system_health": "running",
        "uptime_seconds": uptime,
        "total_requests": metrics["total_requests"],
        "successful_requests": metrics["successful_requests"],
        "error_requests": metrics["error_requests"],
        "average_response_time_seconds": avg_response_time,
        "recent_errors": metrics["recent_errors"]
    }