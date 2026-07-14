from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectionSettings:
    label: str
    database_name: str
    raw_schema: str
    stg_schema: str
    int_schema: str
    mart_schema: str


def build_connection_settings(
    database_name: str, schema_names: list[str]
) -> list[ConnectionSettings]:
    profiles: list[ConnectionSettings] = []

    # RAW・STG・INT・MARTが全て含まれている場合は、検証環境と判定する
    if {"RAW", "STG", "INT", "MART"}.issubset(set(schema_names)):
        profiles.append(
            ConnectionSettings(
                label="検証環境",
                database_name=database_name,
                raw_schema="RAW",
                stg_schema="STG",
                int_schema="INT",
                mart_schema="MART",
            )
        )

    # データベース内のスキーマ文のConnectionSettingsクラスを生成する
    for schema in schema_names:
        if schema == "INFORMATION_SCHEMA":
            continue

        profiles.append(
            ConnectionSettings(
                label=schema,
                database_name=database_name,
                raw_schema=schema,
                stg_schema=schema,
                int_schema=schema,
                mart_schema=schema,
            )
        )

    return profiles
