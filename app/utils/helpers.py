from fastapi import HTTPException


VALID_STATUSES = ["todo", "in_progress", "done"]

VALID_TRANSITIONS = {
    "todo": ["in_progress"],
    "in_progress": ["done"],
    "done": []
}


def validate_status(status: str):
    if status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid status. Use: todo, in_progress, done"
        )


def validate_status_transition(old_status: str, new_status: str):
    validate_status(new_status)

    if old_status == new_status:
        return

    allowed_next = VALID_TRANSITIONS.get(old_status, [])

    if new_status not in allowed_next:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition from {old_status} to {new_status}"
        )