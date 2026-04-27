from fastapi import APIRouter, HTTPException
from sqlmodel import select

from ..database import SessionDep
from ..models import EspConfig
from ..schemas import EspConfigPublic, EspConfigCreate, EspConfigUpdate

router = APIRouter(prefix="/api/esp-config", tags=["esp-config"])


@router.get("/", response_model=list[EspConfigPublic])
def get_all_esp_configs(session: SessionDep):
    """Retrieve all ESP Configurations."""
    configs = session.exec(select(EspConfig)).all()
    return configs


@router.post("/", response_model=EspConfigPublic)
def create_esp_config(config: EspConfigCreate, session: SessionDep):
    """Create a new ESP Configuration."""
    db_config = EspConfig.model_validate(config)
    session.add(db_config)
    session.commit()
    session.refresh(db_config)
    return db_config


@router.patch("/{config_id}", response_model=EspConfigPublic)
def update_esp_config(config_id: int, config_update: EspConfigUpdate, session: SessionDep):
    """Update an existing ESP Configuration."""
    db_config = session.get(EspConfig, config_id)
    if not db_config:
        raise HTTPException(status_code=404, detail="ESP Config not found")
    
    update_data = config_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_config, key, value)
        
    session.add(db_config)
    session.commit()
    session.refresh(db_config)
    return db_config


@router.delete("/{config_id}")
def delete_esp_config(config_id: int, session: SessionDep):
    """Delete an ESP Configuration."""
    db_config = session.get(EspConfig, config_id)
    if not db_config:
        raise HTTPException(status_code=404, detail="ESP Config not found")
    session.delete(db_config)
    session.commit()
    return {"ok": True, "message": "Deleted successfully"}
