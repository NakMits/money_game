import os

from sqlalchemy import create_engine, engine as engine_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


def create_engine_url():
    db_driver_name = "mysql+pymysql"
    cloud_sql_connection_name = os.getenv("CLOUD_SQL_CONNECTION_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME")

    # 本番環境用（ cloud_run & cloud_sql ）
    if cloud_sql_connection_name:
        db_url = engine_.url.URL(
            drivername=db_driver_name,
            username=db_user,
            password=db_password,
            database=db_name,
            query=dict({"unix_socket": f"/cloudsql/{cloud_sql_connection_name}"}),
        )
    # 開発環境用
    else:
        db_url = engine_.url.URL(
            drivername=db_driver_name,
            username=db_user,
            password=db_password,
            database=db_name,
            host=os.environ.get("DB_HOST", "127.0.0.1"),
        )

    return db_url


engine = create_engine(
    create_engine_url(),
    pool_size=5,
    max_overflow=2,
    pool_timeout=30,
    pool_recycle=1800
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
