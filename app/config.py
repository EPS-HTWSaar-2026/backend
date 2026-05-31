# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    esp_host: str
    esp_port_1: int
    esp_port_2: int
    esp_port_3: int
    reconnect_delay: float
    ip: str

    class Config:
        env_file = ".env"

settings = Settings()