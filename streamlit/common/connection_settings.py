from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectionSettings:
    database_name: str
    mart_schema: str
    int_schema: str
    stg_schema: str
    raw_schema: str
