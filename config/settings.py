from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Centralized settings for ATLAS application loaded from environment variables and .env file.
    """
    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    gemini_api_key_2: str = Field(default="", validation_alias="GEMINI_API_KEY_2")
    gemini_api_key_3: str = Field(default="", validation_alias="GEMINI_API_KEY_3")

    ollama_model: str = Field(default="llama3.2", validation_alias="OLLAMA_MODEL")
    ollama_host: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_HOST")
    wake_word_model_path: str = Field(default="./models/hey_atlas.onnx", validation_alias="WAKE_WORD_MODEL_PATH")
    whisper_model_size: str = Field(default="small", validation_alias="WHISPER_MODEL_SIZE")
    piper_voice_path: str = Field(default="./models/en_US-piper.onnx", validation_alias="PIPER_VOICE_PATH")
    audit_log_path: str = Field(default="./storage/audit.jsonl", validation_alias="AUDIT_LOG_PATH")
    confirmation_timeout_s: int = Field(default=15, validation_alias="CONFIRMATION_TIMEOUT_S")
    phone_ip: str = Field(default="10.195.17.165", validation_alias="PHONE_IP")
    phone_port: int = Field(default=8765, validation_alias="PHONE_PORT")
    adb_device_id: Optional[str] = Field(default=None, validation_alias="ADB_DEVICE_ID")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
