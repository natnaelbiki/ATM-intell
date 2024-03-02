import pandas as pd
from django.db import transaction
from .models import FinancialReport, ActivtyReport
from decimal import Decimal, InvalidOperation
from django.http import HttpResponse
from io import StringIO
from datetime import datetime
import re

def filter_reports(form):
    """Utility function to filter reports based on form data."""
    queryset = FinancialReport.objects.all()
    if form.cleaned_data['bank']:
        queryset = queryset.filter(bank__icontains=form.cleaned_data['bank'])
    if form.cleaned_data['terminal_id']:
        queryset = queryset.filter(TERMINAL_ID__icontains=form.cleaned_data['terminal_id'])
    if form.cleaned_data['business_date_start']:
        queryset = queryset.filter(BUSINESS_DATE__gte=form.cleaned_data['business_date_start'])
    if form.cleaned_data['business_date_end']:
        queryset = queryset.filter(BUSINESS_DATE__lte=form.cleaned_data['business_date_end'])
    if form.cleaned_data['from_account_no']:
        queryset = queryset.filter(FROM_ACCOUNT_NO__icontains=form.cleaned_data['from_account_no'])
    if form.cleaned_data['status']:
        queryset = queryset.filter(STATUS=form.cleaned_data['status'])
    return queryset


def activity_filter_reports(form):
    """Utility function to filter reports based on form data."""
    queryset = ActivtyReport.objects.all()
    if form.cleaned_data['bank']:
        queryset = queryset.filter(bank__icontains=form.cleaned_data['bank'])
    if form.cleaned_data['terminal_id']:
        queryset = queryset.filter(ATM_BR_NUMBER__icontains=form.cleaned_data['terminal_id'])
    if form.cleaned_data['txn_date_start']:
        queryset = queryset.filter(TXN_DATE__gte=form.cleaned_data['txn_date_start'])
    if form.cleaned_data['txn_date_end']:
        queryset = queryset.filter(TXN_DATE__lte=form.cleaned_data['txn_date_end'])
    if form.cleaned_data['from_account_no']:
        queryset = queryset.filter(DR_ACCT__icontains=form.cleaned_data['from_account_no'])
    return queryset


def df_to_excel_response(df, filename='download.xlsx'):
    
    # Create an HTTP response with the Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Use the pandas Excel writer and save to the response object
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    return response


def to_decimal(value, default=Decimal('0')):
    """
    Attempt to convert an unknown value type to a Decimal.
    """
    if value is None:
        return default
    
    try:
        return Decimal(str(value))
    except (TypeError, ValueError, InvalidOperation):
        return default


def convert_to_decimal(df, column_name):
    """
    Convert all values in a specified column of a DataFrame to Decimal.

    Parameters:
    - df: The Pandas DataFrame containing the column.
    - column_name: The name of the column to process.

    Returns:
    - The DataFrame with the specified column values converted to Decimal.
    """
    if column_name in df.columns:
        df[column_name] = df[column_name].apply(lambda x: to_decimal(x))
    else:
        print(f"Column '{column_name}' not found in DataFrame.")
        return None
    return df

def clean_account_number(df, field_name):
    if field_name in df.columns:
        # Convert field to string and remove trailing '.0'
        df[field_name] = df[field_name].astype(str).apply(lambda x: x[:-2] if x.endswith('.0') else x)
    return df



def create_cbe_financial_reports_from_dataframe(df, bank_type, user):
    """
    Create financial reports from a DataFrame.

    :param df: Pandas DataFrame with financial report data.
    :param bank_type: A string indicating the bank type ('CBE' or 'Other').
    :return: A boolean indicating if the operation was successful.
    """
    try:
        with transaction.atomic():
            for _, row in df.iterrows():
                FinancialReport.create_cbe_instance(
                    TERMINAL_ID=row['TERMINAL_ID'],
                    CARD_NUMBER=row['CARD_NUMBER'],
                    FROM_ACCOUNT_NO=row['FROM_ACCOUNT_NO'],
                    REQUESTED_AMOUNT=row['REQUESTED_AMOUNT'],
                    BUSINESS_DATE=row['BUSINESS_DATE'],
                    TRXN_TIME=row['TRXN_TIME'],
                    STATUS=row['STATUS'],
                    added_by=user  # Ensure this is correctly handled
                )
        return True
    except Exception as e:
        print(f"Error while cbe creating financial reports: {e}")
        return False


def create_other_financial_reports_from_dataframe(df, bank_type, user):
    """
    Create financial reports from a DataFrame.

    :param df: Pandas DataFrame with financial report data.
    :param bank_type: A string indicating the bank type ('CBE' or 'Other').
    :return: A boolean indicating if the operation was successful.
    """
    try:
        with transaction.atomic():
            for _, row in df.iterrows():
                FinancialReport.create_other_instance(
                    TERMINAL_ID=row['TERMINAL_ID'],
                    CARD_NUMBER=row['CARD_NUMBER'],
                    FROM_ACCOUNT_NO=row['FROM_ACCOUNT_NO'],
                    REQUESTED_AMOUNT=row['REQUESTED_AMOUNT'],
                    BUSINESS_DATE=row['BUSINESS_DATE'],
                    TRXN_TIME=row['TRXN_TIME'],
                    STATUS=row['STATUS'],
                    added_by=user  # Ensure this is correctly handled
                )
        return True
    except Exception as e:
        print(f"Error while other creating financial reports: {e}")
        return False


def handle_uploaded_file(f, model=None):
    """
    Reads an uploaded file into a pandas DataFrame.
    
    :param f: InMemoryUploadedFile, the uploaded file object.
    :param model: The Django model class (unused in this function, but can be used for customization).
    :return: A pandas DataFrame created from the uploaded file.
    """
    # Check the file extension to determine how to read it
    if str(f).endswith('.csv'):
        df = pd.read_csv(f)
    elif str(f).endswith(('.xls', '.xlsx')):
        df = pd.read_excel(f)
    else:
        df = pd.DataFrame()  # Return an empty DataFrame for unsupported file types
    return df


def convert_pasted_data_to_df(pasted_data, separator=','):
    """
    Converts pasted string data into a pandas DataFrame.
    
    :param pasted_data: str, the string containing the pasted data.
    :param separator: str, the separator used in the pasted data. Default is comma for CSV data.
    :return: A pandas DataFrame created from the pasted data.
    """
    # Use StringIO to convert the string data into a file-like object
    data_io = StringIO(pasted_data)
    # Read the data into a DataFrame, specifying the separator
    df = pd.read_csv(data_io, sep=separator)
    return df

def create_cbe_activity_reports_from_dataframe(df, user):
    """
    Create financial reports from a DataFrame.

    :param df: Pandas DataFrame with financial report data.
    :param bank_type: A string indicating the bank type ('CBE' or 'Other').
    :return: A boolean indicating if the operation was successful.
    """
    try:
        with transaction.atomic():
            for _, row in df.iterrows():
                ActivtyReport.create_cbe_instance(
                    ATM_BR_NUMBER=row['ATM_BR_NUMBER'],
                    PAN=row['PAN'],
                    DR_ACCT=row['DR_ACCT'],
                    TXN_AMOUNT=row['TXN_AMOUNT'],
                    TXN_DATE=row['TXN_DATE'],
                    TXN_TIME=row['TXN_TIME'],
                    added_by=user  # Ensure this is correctly handled
                )
        return True
    except Exception as e:
        print(f"Error while cbe creating activity reports: {e}")
        return False


def create_other_activity_reports_from_dataframe(df, user):
    """
    Create financial reports from a DataFrame.

    :param df: Pandas DataFrame with financial report data.
    :param bank_type: A string indicating the bank type ('CBE' or 'Other').
    :return: A boolean indicating if the operation was successful.
    """
    try:
        with transaction.atomic():
            for _, row in df.iterrows():
                ActivtyReport.create_other_instance(
                    ATM_BR_NUMBER=row['ATM_BR_NUMBER'],
                    PAN=row['PAN'],
                    DR_ACCT=row['DR_ACCT'],
                    TXN_AMOUNT=row['TXN_AMOUNT'],
                    TXN_DATE=row['TXN_DATE'],
                    TXN_TIME=row['TXN_TIME'],
                    added_by=user # Ensure this is correctly handled
                )
        return True
    except Exception as e:
        print(f"Error while other creating activity reports: {e}")
        return False

def convert_numeric_to_string(df, column):
    # Iterate over columns and check their data type
    for column in df.columns:
        # If the column is of a numeric type, convert it to string
        if pd.api.types.is_numeric_dtype(df[column]):
            df[column] = df[column].astype(str)
    return df


# Cleaning functions that take DataFrame and column name
def clean_date(df, col_name):
    df[col_name] = pd.to_datetime(df[col_name], errors='coerce').dt.date
    return df

def clean_time(df, col_name):
    df[col_name] = pd.to_datetime(df[col_name], errors='coerce').dt.time
    return df


def standardize_column_names(df, new_col_name, original_col_name):
    # Check if the original column name exists in the DataFrame
    if original_col_name in df.columns:
        # Rename the column
        df = df.rename(columns={original_col_name: new_col_name})
    # If the original column name does not exist, proceed without error
    return df


def standardize_dates(df, column_name):
    """
    Convert different date representations to a uniform format (YYYY-MM-DD).
    
    :param df: DataFrame containing the date column.
    :param column_name: The name of the column to standardize.
    """
    df[column_name] = pd.to_datetime(df[column_name]).dt.date
    return df


def standardize_times(df, column_name):
    """
    Convert different time representations to a uniform format (HH:MM:SS).
    
    :param df: DataFrame containing the time column.
    :param column_name: The name of the column to standardize.
    """
    df[column_name] = pd.to_datetime(df[column_name], format='%H:%M:%S').dt.time
    return df


def check_regexp_number(df, column_name):
    """
    Check if values in the specified column match the pattern: start with 100 and have 13 digits in total.
    
    :param df: DataFrame containing the column to check.
    :param column_name: The name of the column to check.
    :return: Series with Boolean values indicating whether each value matches the pattern.
    """
    pattern = r'^100\d{10}$'  # Starts with 100 and followed by any ten digits
    return df[column_name].astype(str).str.match(pattern)
