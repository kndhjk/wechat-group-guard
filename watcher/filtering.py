def is_group_allowed(group_name: str, allowed_groups: list[str]) -> bool:
    if not allowed_groups:
        return True
    return group_name in allowed_groups
