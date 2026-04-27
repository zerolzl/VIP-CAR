"""管理外部数据库连接引擎的生命周期"""
import logging
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

try:
    import pyodbc
    pyodbc.pooling = False
except ImportError:
    pass


class ExternalDbEngineManager:
    def __init__(self):
        self._engine: Optional[Engine] = None
        self._current_config_hash: Optional[str] = None

    def get_engine(self, host: str, port: int, database_name: str,
                   username: str, password: str, db_type: str = "mssql") -> Engine:
        config_hash = f"{db_type}:{host}:{port}:{database_name}:{username}"
        if self._engine is not None and self._current_config_hash == config_hash:
            return self._engine

        connection_string = self._build_connection_string(
            db_type=db_type,
            host=host,
            port=port,
            database_name=database_name,
            username=username,
            password=password
        )
        
        pool_size = 3
        max_overflow = 2
        
        self._engine = create_engine(
            connection_string,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=1800,
            pool_pre_ping=True,
            pool_timeout=10,
            echo=False,
        )
        self._current_config_hash = config_hash
        logger.info(f"{db_type.upper()}引擎已创建: {host}:{port}/{database_name}")
        return self._engine

    def _build_connection_string(self, db_type: str, host: str, port: int,
                                database_name: str, username: str, password: str) -> str:
        """根据数据库类型构建连接字符串"""
        db_type = db_type.lower()
        
        if db_type == "mssql":
            return (
                f"mssql+pyodbc://{username}:{password}"
                f"@{host}:{port}/{database_name}"
                f"?driver=ODBC+Driver+18+for+SQL+Server"
                f"&TrustServerCertificate=yes"
            )
        elif db_type == "mysql":
            return (
                f"mysql+pymysql://{username}:{password}"
                f"@{host}:{port}/{database_name}"
                f"?charset=utf8mb4"
            )
        elif db_type == "postgresql":
            return (
                f"postgresql+psycopg2://{username}:{password}"
                f"@{host}:{port}/{database_name}"
            )
        elif db_type == "sqlite":
            return f"sqlite:///{database_name}"
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")

    def dispose(self):
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._current_config_hash = None
            logger.info("外部数据库引擎已销毁")


external_engine_manager = ExternalDbEngineManager()
