
  create or replace   view USERDB_D_P01_LAK.USER_SMCB_01.stg_facility_master
  
  
  
  
  as (
    select
    "facility_code" as "FACILITY_CODE",
    "check" as "CHECK",
    "retail_data_sheet_name" as "RETAIL_DATA_SHEET_NAME",
    "search_keyword_competitor_map" as "SEARCH_KEYWORD_COMPETITOR_MAP",
    trim("facility_name") as "FACILITY_NAME",
    "po_level" as "PO_LEVEL",
    "facility_category" as "FACILITY_CATEGORY",
    "regional_office" as "REGIONAL_OFFICE",
    "branch_office" as "BRANCH_OFFICE",
    "facility_address_raw" as "FACILITY_ADDRESS_RAW",
    "inshop_store_name" as "INSHOP_STORE_NAME",
    "satellite" as "SATELLITE",
    "satellite_parent_store" as "SATELLITE_PARENT_STORE",
    "satellite_code" as "SATELLITE_CODE",
    "retail_store_1" as "RETAIL_STORE_1",
    "retail_store_2" as "RETAIL_STORE_2",
    "retail_store_3" as "RETAIL_STORE_3",
    "retail_internal_code_1" as "RETAIL_INTERNAL_CODE_1",
    "retail_internal_code_2" as "RETAIL_INTERNAL_CODE_2",
    "retail_internal_code_3" as "RETAIL_INTERNAL_CODE_3",
    "has_ds_or_satellite" as "HAS_DS_OR_SATELLITE",
    "has_ds_or_satellite_bool" as "HAS_DS_OR_SATELLITE_BOOL",
    "ds_flag" as "DS_FLAG",
    "ds_bool" as "DS_BOOL",
    "st_flag" as "ST_FLAG",
    "st_bool" as "ST_BOOL",
    "retail_flag" as "RETAIL_FLAG",
    "retail_bool" as "RETAIL_BOOL",
    "softbank_flag" as "SOFTBANK_FLAG",
    "softbank_bool" as "SOFTBANK_BOOL",
    "au_flag" as "AU_FLAG",
    "au_bool" as "AU_BOOL",
    "rakuten_mobile_flag" as "RAKUTEN_MOBILE_FLAG",
    "rakuten_mobile_bool" as "RAKUTEN_MOBILE_BOOL",
    "facility_group" as "FACILITY_GROUP",
    "notes" as "NOTES",
    "facility_category_2" as "FACILITY_CATEGORY_2",
    "business_floor_area" as "BUSINESS_FLOOR_AREA",
    "tenant_count" as "TENANT_COUNT"
from USERDB_D_P01_LAK.USER_SMCB_01.RAW_FACILITY_MASTER
  );

