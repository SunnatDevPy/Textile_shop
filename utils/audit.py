from models import AuditLog


async def write_audit_log(
    *,
    entity: str,
    entity_id: int,
    action: str,
    actor: str = "system",
    details: str = "",
) -> None:
    await AuditLog.create(
        entity=entity,
        entity_id=entity_id,
        action=action,
        actor=actor,
        details=details,
    )
