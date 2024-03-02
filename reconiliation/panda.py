import pandas as pd
from .util import (convert_numeric_to_string as cnts, convert_to_decimal, clean_time, 
    clean_date, standardize_column_names, clean_account_number, check_regexp_number,
    standardize_times, standardize_dates)

#clean activity report
def clean_financial_dataframe(df):
    # Drop unnecessary fields
    df = df.drop(columns=['ACQUIRING_INSTITUTION', 'INSTITIUTION_NAME', 'TXN_CODE', 'AUTH_CODE', 'RESPONSE_CODE',
    	'RRN', 'RRN_VISA', 'REVERSAL_REASON_CODE', 'TRXN_DESCRIPTION', 'CARD_NUMBER 4'], errors='ignore')
    
    # Remove rows with zero values in specified field
    try:
        df = df[df['REQUESTED_AMOUNT'] != 0]
    except Exception as e:
        print(str(e))

    # cast to string
    df = clean_account_number(df, 'FROM_ACCOUNT_NO')
    df = cnts(df, 'TERMINAL_ID')
    df = convert_to_decimal(df, 'REQUESTED_AMOUNT')
    df = standardize_times(df, 'TRXN_TIME')
    df = standardize_dates(df, 'BUSINESS_DATE')
   
    
    return df


# For CBE Bank
 # Filters only CBE account from financial
def cbe_financial_dataframe(df):
    df = df[df['FROM_ACCOUNT_NO'].str.startswith('100')]    
    return df

# Filters only cbe account successful transaction from financial
def cbe_financial_successful_dataframe(df):
    df = df[df['STATUS'] == ('SUCCESSFUL')]    
    return df

# Filters only cbe account failed transaction from financial
def cbe_financial_failed_dataframe(df):
    df = df[df['STATUS'] == ('FAILED')]    
    return df

# Filters only cbe account reversal transaction from financial
def cbe_financial_reversal_dataframe(df):
    df = df[df['STATUS'] == ('REVERSAL')]    
    return df


#cleans unmatched activity data frame
def clean_unmatched_financial_dataframe(df):
    # Drop unnecessary fields
    df = df.drop(columns=['TERMINAL_ID_y','TRXN_TIME_y', 'FROM_ACCOUNT_NO_y', 'REQUESTED_AMOUNT_y', 'BUSINESS_DATE_y'], errors='ignore')
    
    # Rename fields
    df = df.rename(columns=['TERMINAL_ID_x','TRXN_TIME_x', 'FROM_ACCOUNT_NO_x', 'REQUESTED_AMOUNT_x', 'BUSINESS_DATE_x'])    
    return df



# For Other Bank
# Filters only Other bank account from financial
def other_financial_dataframe(df):
    df = df[df['FROM_ACCOUNT_NO'].str.startswith('0')] 
    return df


# Filters only cbe account successful transaction from financial
def other_financial_successful_dataframe(df):
    df = df[df['STATUS'] == ('SUCCESSFUL')]    
    return df

# Filters only cbe account failed transaction from financial
def other_financial_failed_dataframe(df):
    df = df[df['STATUS'] == ('FAILED')]    
    return df

# Filters only cbe account reversal transaction from financial
def other_financial_reversal_dataframe(df):
    df = df[df['STATUS'] == ('REVERSAL')]    
    return df



#clean activity report
def clean_activity_dataframe(df):
    # Drop unnecessary fields
    df = df.drop(columns=['AT_UNIQUE_ID', 'ATM_DR_ACCT_BR','TRXN__DATE', 'CARD_NO', 'CONTRA_BRANCH', 'MAGIX_ID', 'CR_ACCT', 'CR_CCY',
    	'LAST FOUR CARD NUMBER', 'NARRATIVE', 'REF_NO'], errors='ignore')
        
    # Remove rows with zero values in specified field
    try:
        df = df[df['TXN_AMOUNT'] != 0]
    except Exception as e:
        print(str(e))
    df = convert_to_decimal(df, 'TXN_AMOUNT')
    df = clean_account_number(df, 'TXN_AMOUNT')
    df = standardize_column_names(df, 'TXN_DATE', 'TXN__DATE')
    df = standardize_times(df, 'TXN_TIME')
    df = standardize_dates(df, 'TXN_DATE')
    df = cnts(df, 'DR_ACCT')
    
    return df



#cleans unmatched activity data frame
def clean_unmatched_activity_dataframe(df):
    # Drop unnecessary fields
    df = df.drop(columns=['CARD_NUMBER','TRXN__DATE', 'BUSINESS_DATE_x', 'STATUS'], errors='ignore')
    
    # Rename fields
    df = df.rename(columns={'BUSINESS_DATE_y': 'BUSINESS_DATE'})    
    return df

#cleans unmatched activity data frame
def clean_unmatched_other_activity_dataframe(df):
    # Drop unnecessary fields
    df = df.drop(columns=['CARD_NUMBER','TRXN__DATE', 'BUSINESS_DATE_x', 'STATUS', 'FROM_ACCOUNT_NO_x'], errors='ignore')
    
    # Rename fields
    df = df.rename(columns={'FROM_ACCOUNT_NO_y': 'FROM_ACCOUNT_NO'})    
    return df


#filters only cbe account from activity
def cbe_activity_dataframe(df):
    df = df[df['DR_ACCT'].str.startswith('100')]    
    return df

# Filters only Other bank account from financial
def other_activity_dataframe(df):
    df = df[df['DR_ACCT'].str.startswith('ETB12635')] 
    return df



#perform matching
def perform_matching(left_df, right_df, financial_fields, activity_fields):
    """
    Perform matching between two DataFrames based on selected fields.
    
    Parameters:
    - left_df: DataFrame for FinancialReport.
    - right_df: DataFrame for ActivityReport.
    - financial_fields: List of field names to match on from FinancialReport.
    - activity_fields: List of field names to match on from ActivityReport.
    
    Returns:
    - DataFrame with matching records.
    """
    # Ensure the fields lists have the same length and contain valid column names
    if len(financial_fields) != len(activity_fields):
        raise ValueError("Field lists must have the same number of elements.")
    
    # Rename the columns in both DataFrames for matching, to ensure columns names align
    rename_mapping_left = {old: new for old, new in zip(financial_fields, activity_fields)}
    left_df_renamed = left_df.rename(columns=rename_mapping_left)
    
    # Perform the inner join on the renamed columns
    matching_df = pd.merge(left_df_renamed, right_df, left_on=activity_fields, right_on=activity_fields)
    
    return matching_df