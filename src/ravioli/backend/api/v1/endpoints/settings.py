from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ravioli.backend.core.database import get_db
from ravioli.backend.core.models import SystemSetting
from ravioli.backend.core.schemas import SystemSetting as SystemSettingSchema, SystemSettingBase

router = APIRouter()

@router.get("/{key}", response_model=SystemSettingSchema)
def get_setting(key: str, db: Session = Depends(get_db)):
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting

@router.put("/{key}", response_model=SystemSettingSchema)
def update_setting(key: str, setting_in: SystemSettingBase, db: Session = Depends(get_db)):
    if key != setting_in.key:
        raise HTTPException(status_code=400, detail="Key in path does not match key in body")
        
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if setting:
        setting.value = setting_in.value
    else:
        setting = SystemSetting(key=setting_in.key, value=setting_in.value)
        db.add(setting)
        
    db.commit()
    db.refresh(setting)
    return setting
