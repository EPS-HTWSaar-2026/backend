# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    esp_host: str = "192.168.1.100"
    esp_port_1: int = 4001
    esp_port_2: int = 4002
    esp_port_3: int = 4003
    reconnect_delay: float = 5.0

    class Config:
        env_file = ".env"

settings = Settings()