from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ravioli.backend.core.database import get_db
from ravioli.backend.core.models import SystemSetting as SystemSettingModel
from ravioli.backend.core.schemas import SystemSetting as SystemSettingSchema, SystemSettingBase
from ravioli.backend.core.encryption import encrypt_value, decrypt_value

router = APIRouter()

# Fields within a setting's value dict that should be encrypted at rest
_SENSITIVE_FIELDS = {"api_key"}

_REDACTED = "••••••••"


def _encrypt_sensitive(value: dict) -> dict:
    """Return a copy of value with sensitive fields encrypted."""
    out = dict(value)
    for field in _SENSITIVE_FIELDS:
        if field in out and out[field]:
            out[field] = encrypt_value(out[field])
    return out


def _redact_sensitive(value: dict) -> dict:
    """Return a copy of value with sensitive fields replaced by a redacted placeholder."""
    out = dict(value)
    for field in _SENSITIVE_FIELDS:
        if field in out and out[field]:
            out[field] = _REDACTED
    return out


@router.get("/{key}", response_model=SystemSettingSchema)
def get_setting(key: str, db: Session = Depends(get_db)):
    setting = db.query(SystemSettingModel).filter(SystemSettingModel.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    # Return a copy with sensitive fields redacted — never expose raw ciphertext or plaintext to the frontend
    redacted_value = _redact_sensitive(setting.value)
    return SystemSettingSchema(key=setting.key, value=redacted_value, updated_at=setting.updated_at)


@router.put("/{key}", response_model=SystemSettingSchema)
def update_setting(key: str, setting_in: SystemSettingBase, db: Session = Depends(get_db)):
    if key != setting_in.key:
        raise HTTPException(status_code=400, detail="Key in path does not match key in body")

    # If the frontend sends back our redacted placeholder, preserve the existing encrypted value
    existing = db.query(SystemSettingModel).filter(SystemSettingModel.key == key).first()
    incoming = dict(setting_in.value)

    for field in _SENSITIVE_FIELDS:
        if field in incoming:
            if incoming[field] == _REDACTED:
                # User did not change the sensitive field — keep the existing encrypted value
                if existing and field in existing.value:
                    incoming[field] = existing.value[field]
                else:
                    incoming[field] = ""
            elif incoming[field]:
                # New plaintext value — encrypt it
                incoming[field] = encrypt_value(incoming[field])
            # Empty string means the user cleared the field

    if existing:
        existing.value = incoming
    else:
        existing = SystemSettingModel(key=key, value=incoming)
        db.add(existing)

    db.commit()
    db.refresh(existing)

    # Return redacted response
    redacted_value = _redact_sensitive(existing.value)
    return SystemSetting(key=existing.key, value=redacted_value, updated_at=existing.updated_at)
