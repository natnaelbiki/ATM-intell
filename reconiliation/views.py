import pandas as pd
from .panda import (clean_financial_dataframe, 
    cbe_financial_dataframe, other_financial_dataframe, 
    clean_activity_dataframe, other_activity_dataframe, 
    cbe_activity_dataframe, cbe_financial_successful_dataframe,
    cbe_financial_failed_dataframe, cbe_financial_reversal_dataframe,
    other_financial_successful_dataframe, other_financial_failed_dataframe,
    other_financial_reversal_dataframe, clean_unmatched_activity_dataframe, 
    clean_unmatched_financial_dataframe)
from django.conf import settings
from .dask_optimizer import merge, merge_other
from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import tempfile
import os
from django.contrib.auth.decorators import login_required
import traceback 
from .models import FinancialReport, ActivtyReport
from .forms import (FinancialReportForm,  UploadActivityReportForm, UploadFinancialReportForm, 
    ActivityReportFilterForm, FullReportMatchForm, FinancialUploadForm, FinancialReportFilterForm, ReportUploadForm, DataUploadForm, ActivityReportForm)
from django.db import transaction
from .util import df_to_excel_response, activity_filter_reports, filter_reports, handle_uploaded_file, convert_pasted_data_to_df, create_cbe_activity_reports_from_dataframe, create_other_activity_reports_from_dataframe, create_cbe_financial_reports_from_dataframe, create_other_financial_reports_from_dataframe
from django.db.models import Q
from django.utils.dateparse import parse_date
from account.decorators import role_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.db.models import F
from io import StringIO


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    print(ip)


STATUS_CHOICES = [
        ('SUCCESSFUL', 'SUCCESSFUL'),
        ('FAILED', 'FAILED'),
        ('REVERSAL', 'REVERSAL'),
    ]
BANK_CHOICES = [
        ('CBE', 'CBE'),
        ('Other', 'Other'),
    ]


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'base.html'

#@role_required('ADMIN', 'MANAGER')
def view_financial_report(request):
    try:
        if 'download' in request.GET:
            get_client_ip(request)
            # Reapply filters for downloading
            form = FinancialReportFilterForm(request.GET)
            financial_reports = filter_reports(form) if form.is_valid() else FinancialReport.objects.none()

           
            # Convert to DataFrame
            df = pd.DataFrame(list(financial_reports.values('bank', 'TERMINAL_ID', 'BUSINESS_DATE', 'FROM_ACCOUNT_NO', 'REQUESTED_AMOUNT', 'STATUS')))
            
            # Convert DataFrame to Excel and return as response
            response = HttpResponse(content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename="filtered_financial_reports.xlsx"'
            with pd.ExcelWriter(response, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            return response
        else:
            get_client_ip(request)
            form = FinancialReportFilterForm(request.GET or None)
            financial_reports = filter_reports(form) if form.is_valid() else FinancialReport.objects.all()

            paginator = Paginator(financial_reports.order_by('-BUSINESS_DATE'), 10)  # Show 10 reports per page
            page = request.GET.get('page')
            try:
                financial_reports = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                financial_reports = paginator.page(1)
            except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
                financial_reports = paginator.page(paginator.num_pages)
        return render(request, 'financial/financial_view.html', {
            'form': form, 
            'financial_reports': financial_reports,
            'bank_filter': request.GET.get('bank'),
            'status_filter': request.GET.get('status'),
            'terminal_id_filter': request.GET.get('terminal_id'),
            'from_account_no_filter': request.GET.get('from_account_no'),
            'business_date_start': request.GET.get('business_date_start'),
            'business_date_end': request.GET.get('business_date_end'),
            'BANK_CHOICES': BANK_CHOICES,
            'STATUS_CHOICES': STATUS_CHOICES
            })
    except Exception as e:
        return render(request, 'error_page.html', {'e': e})



# Financial report uploader
def upload_financial_report(request):
    try:
        get_client_ip(request)
        if request.method == 'POST' and request.FILES.get('excel_file'):
            excel_file = request.FILES['excel_file']

            # Check if the file is an Excel file
            if not excel_file.name.endswith(('.xlsx', '.xls')):
                return HttpResponse('This is not an excel file.')

            try:
                # Use Pandas to parse the Excel file
                df = pd.read_excel(excel_file)
                cbe_df = cbe_financial_dataframe(clean_financial_dataframe(df))
                oth_df = other_financial_dataframe(clean_financial_dataframe(df)) 


                bank_type = 'CBE'  # Placeholder, adjust as necessary

                # Use the utility function to create instances
                if create_cbe_financial_reports_from_dataframe(cbe_df, bank_type, request.user) & create_other_financial_reports_from_dataframe(oth_df, 'OTHER', request.user):
                    return redirect('view_financial_report')  # Adjust with your success redirect
                else:
                    return render(request, 'error_page.html', {'e': 'Failed to create financial reports.'})
            except Exception as e:
                return render(request, 'error_page.html', {'e': e})

        # Render the upload form template if GET request
        return render(request, 'financial/upload_financial_report.html')
    except Exception as e:
        return render(request, 'error_page.html', {'e': e})



def view_activity_report(request):
    try:
        get_client_ip(request)
        if 'download' in request.GET:
            # Reapply filters for downloading
            form = ActivityReportFilterForm(request.GET)
            activity_reports = activity_filter_reports(form) if form.is_valid() else ActivtyReport.objects.none()

           
            # Convert to DataFrame
            df = pd.DataFrame(list(activity_reports.values('bank', 'ATM_BR_NUMBER', 'TXN_DATE', 'DR_ACCT', 'TXN_AMOUNT')))
            
            # Convert DataFrame to Excel and return as response
            response = HttpResponse(content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename="filtered_activity_reports.xlsx"'
            with pd.ExcelWriter(response, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            return response

        else:
            form = ActivityReportFilterForm(request.GET or None)
            activity_reports = activity_filter_reports(form) if form.is_valid() else ActivtyReport.objects.all()

            paginator = Paginator(activity_reports.order_by('-TXN_DATE'), 10)  # Show 10 reports per page
            page = request.GET.get('page')
            try:
                activity_reports = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                activity_reports = paginator.page(1)
            except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
                activity_reports = paginator.page(paginator.num_pages)
        return render(request, 'activity_list.html', {
            'form': form, 
            'activity_reports': activity_reports,
            'bank_filter': request.GET.get('bank'),
            'terminal_id_filter': request.GET.get('terminal_id'),
            'from_account_no_filter': request.GET.get('from_account_no'),
            'txn_date_start': request.GET.get('txn_date_start'),
            'txn_date_end': request.GET.get('txn_date_end'),
            })
    except Exception as e:
        return render(request, 'error_page.html', {'e': e})

#
def upload_activity_report(request):
    try:
        get_client_ip(request)
        if request.method == 'POST' and request.FILES.get('excel_file'):
            excel_file = request.FILES['excel_file']

            # Check if the file is an Excel file
            if not excel_file.name.endswith(('.xlsx', '.xls')):
                return render(request, 'error_page.html', {'e': e})

            try:
                # Use Pandas to parse the Excel file
                df = pd.read_excel(excel_file)
                cbe_df = cbe_activity_dataframe(clean_activity_dataframe(df))
                other_df = other_activity_dataframe(clean_activity_dataframe(df))

                # Use the utility function to create instances
                if create_cbe_activity_reports_from_dataframe(cbe_df, request.user) & create_other_activity_reports_from_dataframe(other_df, request.user):
                    return redirect('view_activity_report')  # Adjust with your success redirect
                else:
                    return render(request, 'error_page.html', {'e': 'Error occured on creating activity reports'})
            except Exception as e:
                return render(request, 'error_page.html', {'e': e})

        # Render the upload form template if GET request
        return render(request, 'activity/upload_activity_report.html')
    except Exception as e:
        return render(request, 'error_page.html', {'e': e})



def match_view(request):
    try:
        get_client_ip(request)
        # Convert the stored JSON back into DataFrames
        financial_df = pd.read_json(request.session.get('financial_df', '{}'))
        activity_df = pd.read_json(request.session.get('activity_df', '{}'))
        
        # Convert DataFrames to lists of dicts for pagination
        financial_records = financial_df.to_dict('records')
        activity_records = activity_df.to_dict('records')
        
       # Get page numbers for each report from request
        financial_page_number = request.GET.get('financial_page', 1)
        activity_page_number = request.GET.get('activity_page', 1)

        # Create paginators for each report
        financial_paginator = Paginator(financial_records, 10)  # Adjust the number per page as needed
        activity_paginator = Paginator(activity_records, 10)  # Adjust the number per page as needed

        # Get the requested page
        financial_page = financial_paginator.get_page(financial_page_number)
        activity_page = activity_paginator.get_page(activity_page_number)

        # Pass the paginated records to the template
        return render(request, 'match.html', {
            'financial_page': financial_page,
            'activity_page': activity_page,
        })
    except Exception as e:
        return render(request, 'error_page.html', {'e': e})


def results_view(request):
    # Example placeholder for processing and displaying matching results
    # Implement your matching logic here and pass results to context
    context = {
        'matching_results': "Matching results go here.",
    }
    return render(request, 'results.html', context)

def handle_uploaded_file(f):
    """Reads an uploaded file into a pandas DataFrame, supporting both CSV and Excel formats."""
    if f.name.endswith('.csv'):
        return pd.read_csv(f)
    elif f.name.endswith(('.xls', '.xlsx')):
        return pd.read_excel(f)
    else:
        raise ValueError("Unsupported file format.")

def full_matching_view(request):
    try:
        get_client_ip(request)
        if request.method == 'POST':
            form = FullReportMatchForm(request.POST, request.FILES)
            if form.is_valid():
                financial_report = request.FILES['financial_report']
                activity_report = request.FILES['activity_report']
                
                # Process files (assuming CSV for simplicity)
                financial_df = handle_uploaded_file(financial_report)
                activity_df = handle_uploaded_file(activity_report)

                # clean both data frames
                financial_dataframe = clean_financial_dataframe(financial_df)
                activity_dataframe = clean_activity_dataframe(activity_df)

                
                #Process cbe financial reports
                CBE_ONLY_FINANCIAL = cbe_financial_dataframe(financial_dataframe)
                CBE_ONLY_FINANCIAL_SUCCESSFUL = cbe_financial_successful_dataframe(CBE_ONLY_FINANCIAL)
                CBE_ONLY_FINANCIAL_FAILED = cbe_financial_failed_dataframe(CBE_ONLY_FINANCIAL)
                CBE_ONLY_FINANCIAL_REVERSAL = cbe_financial_reversal_dataframe(CBE_ONLY_FINANCIAL)

                    #process other financial reports
                OTHER_ONLY_FINANCIAL = other_financial_dataframe(financial_dataframe)
                OTHER_ONLY_FINANCIAL_SUCCESSFUL = other_financial_successful_dataframe(OTHER_ONLY_FINANCIAL)
                OTHER_ONLY_FINANCIAL_FAILED = other_financial_failed_dataframe(OTHER_ONLY_FINANCIAL)
                OTHER_ONLY_FINANCIAL_REVERSAL = other_financial_reversal_dataframe(OTHER_ONLY_FINANCIAL)


                    #process cbe account activity reports here
                CBE_ONLY_ACTIVITY = cbe_activity_dataframe(activity_dataframe)
                OTHER_ONLY_ACTIVITY = other_activity_dataframe(activity_dataframe)

                    #merge cbe account financial successful with cbe acount activity
                CBE_ONLY_FINANCIAL_SUCCESSFUL_MATCHED, CBE_ONLY_FINANCIAL_SUCCESSFUL_UNMATCHED, CBE_ONLY_ACTIVITY_UNMATCHED = merge(CBE_ONLY_FINANCIAL_SUCCESSFUL, CBE_ONLY_ACTIVITY)
                
                CBE_ONLY_ACTIVITY_UNMATCHED = clean_unmatched_activity_dataframe(CBE_ONLY_ACTIVITY_UNMATCHED)
                CBE_ONLY_FINANCIAL_REVERSAL_MATCHED, CBE_ONLY_FINANCIAL_REVERSAL_UNMATCHED, CBE_ONLY_ACTIVITY_UNMATCHED = merge(CBE_ONLY_FINANCIAL_REVERSAL, CBE_ONLY_ACTIVITY_UNMATCHED)
                
                    
                CBE_ONLY_ACTIVITY_UNMATCHED = clean_unmatched_activity_dataframe(CBE_ONLY_ACTIVITY_UNMATCHED)
                CBE_ONLY_FINANCIAL_FAILED_MATCHED, CBE_ONLY_FINANCIAL_FAILED_UNMATCHED, CBE_ONLY_ACTIVITY_UNMATCHED = merge(CBE_ONLY_FINANCIAL_FAILED, CBE_ONLY_ACTIVITY_UNMATCHED)
                CBE_ONLY_ACTIVITY_UNMATCHED = clean_unmatched_activity_dataframe(CBE_ONLY_ACTIVITY_UNMATCHED)
                    
                #process other financial report
                OTHER_ONLY_FINANCIAL_SUCCESSFUL_MATCHED, OTHER_ONLY_FINANCIAL_SUCCESSFUL_UNMATCHED, OTHER_ONLY_ACTIVITY_UNMATCHED = merge_other(OTHER_ONLY_FINANCIAL_SUCCESSFUL, OTHER_ONLY_ACTIVITY)

                OTHER_ONLY_ACTIVITY_UNMATCHED = clean_unmatched_activity_dataframe(OTHER_ONLY_ACTIVITY_UNMATCHED)
                OTHER_ONLY_FINANCIAL_REVERSAL_MATCHED, OTHER_ONLY_FINANCIAL_REVERSAL_UNMATCHED, OTHER_ONLY_ACTIVITY_UNMATCHED = merge_other(OTHER_ONLY_FINANCIAL_REVERSAL, OTHER_ONLY_ACTIVITY_UNMATCHED)

                OTHER_ONLY_ACTIVITY_UNMATCHED = clean_unmatched_activity_dataframe(OTHER_ONLY_ACTIVITY_UNMATCHED)
                OTHER_ONLY_FINANCIAL_FAILED_MATCHED, OTHER_ONLY_FINANCIAL_FAILED_UNMATCHED, OTHER_ONLY_ACTIVITY_UNMATCHED = merge_other(OTHER_ONLY_FINANCIAL_FAILED, OTHER_ONLY_ACTIVITY_UNMATCHED)
                OTHER_ONLY_ACTIVITY_UNMATCHED = clean_unmatched_activity_dataframe(OTHER_ONLY_ACTIVITY_UNMATCHED)                
                # Convert processed DataFrame to Excel
                response = HttpResponse(content_type='application/ms-excel')
                response['Content-Disposition'] = 'attachment; filename="processed_reports.xlsx"'
                    
                with pd.ExcelWriter(response, engine='openpyxl') as writer:
                    CBE_ONLY_FINANCIAL_SUCCESSFUL_MATCHED.to_excel(writer, sheet_name='CBE_FIN_ACT_SUCCESS_MATCHED', index=False)
                    CBE_ONLY_FINANCIAL_SUCCESSFUL_UNMATCHED.to_excel(writer, sheet_name='CBE_FIN_SUCCESS_UNMATCHED', index=False)
                    
                    CBE_ONLY_FINANCIAL_REVERSAL_MATCHED.to_excel(writer, sheet_name='CBE_FIN_ACT_REVERSAL_MATCHED', index=False)
                    CBE_ONLY_FINANCIAL_REVERSAL_UNMATCHED.to_excel(writer, sheet_name='CBE_FIN_REVERSAL_UNMATCHED', index=False)

                    CBE_ONLY_FINANCIAL_FAILED_MATCHED.to_excel(writer, sheet_name='CBE_FIN_ACT_FAILED_MATCHED', index=False)
                    CBE_ONLY_FINANCIAL_FAILED_UNMATCHED.to_excel(writer, sheet_name='CBE_FIN_FAILED_UNMATCHED', index=False)

                    OTHER_ONLY_FINANCIAL_SUCCESSFUL_MATCHED.to_excel(writer, sheet_name='OTH_FIN_ACT_SUCCESS_MATCHED', index=False)
                    OTHER_ONLY_FINANCIAL_SUCCESSFUL_UNMATCHED.to_excel(writer, sheet_name='OTH_FIN_SUCCESS_UNMATCHED', index=False)
                    
                    OTHER_ONLY_FINANCIAL_REVERSAL_MATCHED.to_excel(writer, sheet_name='OTH_FIN_ACT_REVERSAL_MATCHED', index=False)
                    OTHER_ONLY_FINANCIAL_REVERSAL_UNMATCHED.to_excel(writer, sheet_name='OTH_FIN_REVERSAL_UNMATCHED', index=False)
                    
                    OTHER_ONLY_FINANCIAL_FAILED_MATCHED.to_excel(writer, sheet_name='OTH_FIN_ACT_FAILED_MATCHED', index=False)
                    OTHER_ONLY_FINANCIAL_FAILED_UNMATCHED.to_excel(writer, sheet_name='OTH_FIN_FAILED_UNMATCHED', index=False)
                    
                    CBE_ONLY_ACTIVITY_UNMATCHED.to_excel(writer, sheet_name='CBE_ONLY_ACTIVITY_UNMATCHED', index=False)
                    OTHER_ONLY_ACTIVITY_UNMATCHED.to_excel(writer, sheet_name='OTH_ONLY_ACTIVITY_UNMATCHED', index=False)


                    financial_dataframe.to_excel(writer, sheet_name='Financial Cleaned', index=False)
                    activity_dataframe.to_excel(writer, sheet_name='Activity Cleaned', index=False)
                    #CBE writer
                    CBE_ONLY_FINANCIAL.to_excel(writer, sheet_name='CBE_ONLY_FINANCIAL', index=False)
                    CBE_ONLY_FINANCIAL_SUCCESSFUL.to_excel(writer, sheet_name='CBE_ONLY_FINANCIAL_SUCCESSFUL', index=False)
                    CBE_ONLY_FINANCIAL_FAILED.to_excel(writer, sheet_name='CBE_ONLY_FINANCIAL_FAILED', index=False)
                    CBE_ONLY_FINANCIAL_REVERSAL.to_excel(writer, sheet_name='CBE_ONLY_FINANCIAL_REVERSAL', index=False)
                    #Other writer
                    OTHER_ONLY_FINANCIAL.to_excel(writer, sheet_name='OTHER_ONLY_FINANCIAL', index=False)
                    OTHER_ONLY_FINANCIAL_SUCCESSFUL.to_excel(writer, sheet_name='OTHER_ONLY_FINANCIAL_SUCCESSFUL', index=False)
                    OTHER_ONLY_FINANCIAL_FAILED.to_excel(writer, sheet_name='OTHER_ONLY_FINANCIAL_FAILED', index=False)
                    OTHER_ONLY_FINANCIAL_REVERSAL.to_excel(writer, sheet_name='OTHER_ONLY_FINANCIAL_REVERSAL', index=False)
                
                    #activity for both
                    CBE_ONLY_ACTIVITY.to_excel(writer, sheet_name='CBE_ONLY_ACTIVITY', index=False)
                    OTHER_ONLY_ACTIVITY.to_excel(writer, sheet_name='OTHER_ONLY_ACTIVITY', index=False)
                return response
        else:
            form = FullReportMatchForm()
        return render(request, 'upload_reports.html', {'form': form})
    except Exception:
        error_message = traceback.format_exc()
        return render(request, 'error_page.html', {'e': error_message})


def upload_and_clean_financial_report(request):
    try:
        get_client_ip(request)
        if request.method == 'POST':
            form = UploadFinancialReportForm(request.POST, request.FILES)
            if form.is_valid():
                excel_file = request.FILES['file']
                df = handle_uploaded_file(excel_file)

                # Clean the data
                cleaned_df = clean_financial_dataframe(df)
                CBE_ONLY_FINANCIAL = cbe_financial_dataframe(cleaned_df)
                CBE_ONLY_FINANCIAL_SUCCESSFUL = cbe_financial_successful_dataframe(CBE_ONLY_FINANCIAL)
                CBE_ONLY_FINANCIAL_FAILED = cbe_financial_failed_dataframe(CBE_ONLY_FINANCIAL)
                CBE_ONLY_FINANCIAL_REVERSAL = cbe_financial_reversal_dataframe(CBE_ONLY_FINANCIAL)

                    #process other financial reports
                OTHER_ONLY_FINANCIAL = other_financial_dataframe(cleaned_df)
                OTHER_ONLY_FINANCIAL_SUCCESSFUL = other_financial_successful_dataframe(OTHER_ONLY_FINANCIAL)
                OTHER_ONLY_FINANCIAL_FAILED = other_financial_failed_dataframe(OTHER_ONLY_FINANCIAL)
                OTHER_ONLY_FINANCIAL_REVERSAL = other_financial_reversal_dataframe(OTHER_ONLY_FINANCIAL)


                # Convert cleaned DataFrame to Excel and return as response
                response = HttpResponse(
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                )
                response['Content-Disposition'] = 'attachment; filename="cleaned_financial_file.xlsx"'
                with pd.ExcelWriter(response, engine='openpyxl') as writer:
                    CBE_ONLY_FINANCIAL.to_excel(writer, sheet_name='CBE_ONLY_FINANCIAL', index=False)
                    CBE_ONLY_FINANCIAL_SUCCESSFUL.to_excel(writer, sheet_name='CBE_ONLY_FINA_SUCC', index=False)
                    CBE_ONLY_FINANCIAL_REVERSAL.to_excel(writer, sheet_name='CBE_ONLY_FINA_REVE', index=False)
                    CBE_ONLY_FINANCIAL_FAILED.to_excel(writer, sheet_name='CBE_ONLY_FINA_FAILED', index=False)
                    OTHER_ONLY_FINANCIAL.to_excel(writer, sheet_name='OTHER_ONLY_FINANCIAL', index=False)
                    OTHER_ONLY_FINANCIAL_SUCCESSFUL.to_excel(writer, sheet_name='OTHER_ONLY_FINL_SUCC', index=False)
                    OTHER_ONLY_FINANCIAL_REVERSAL.to_excel(writer, sheet_name='OTHER_ONLY_FINL_REVE', index=False)
                    OTHER_ONLY_FINANCIAL_FAILED.to_excel(writer, sheet_name='OTHER_ONLY_FINL_FAIL', index=False)

                return response
        else:
            form = UploadFinancialReportForm()
        return render(request, 'financial/clean_financial.html', {'form': form})
    except Exception as e:
        return render(request, 'error_page.html', {'e': e})



def upload_and_clean_activity_report(request):
    try:
        get_client_ip(request)
        if request.method == 'POST':
            form = UploadActivityReportForm(request.POST, request.FILES)
            if form.is_valid():
                activity_file = request.FILES['file']
                df = handle_uploaded_file(activity_file)

                cleaned_df = clean_activity_dataframe(df)  # Clean the data
                CBE_ONLY_ACTIVITY = cbe_activity_dataframe(cleaned_df)
                OTHER_ONLY_ACTIVITY = other_activity_dataframe(cleaned_df)


                # Convert cleaned DataFrame to Excel for download
                response = HttpResponse(
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                )
                response['Content-Disposition'] = 'attachment; filename="cleaned_activity_report.xlsx"'
                with pd.ExcelWriter(response, engine='openpyxl') as writer:
                    CBE_ONLY_ACTIVITY.to_excel(writer, sheet_name='CBE_ONLY_ACTIVITY', index=False)
                    OTHER_ONLY_ACTIVITY.to_excel(writer, sheet_name='OTHER_ONLY_ACTIVITY', index=False)
                return response
        else:
            form = UploadActivityReportForm()
        return render(request, 'activity/upload_and_clean_activity_report.html', {'form': form})
    except Exception as e:
        return render(request, 'error_page.html', {'e': e})


def reports_view(request):
    try:
        # Handle filtering
        financial_form = FinancialReportFilterForm(request.GET or None)
        activity_form = ActivityReportFilterForm(request.GET or None)

        financial_reports = filter_reports(financial_form) if financial_form.is_valid() else FinancialReport.objects.none()
        activity_reports = activity_filter_reports(activity_form) if activity_form.is_valid() else ActivtyReport.objects.all()

        financial_filter = financial_form
        activity_filter = activity_form


        if financial_form.is_valid():
            request.session['financial_filter'] = financial_form.cleaned_data
        if activity_form.is_valid():
            request.session['activity_filter'] = activity_form.cleaned_data
        
        # Handle pagination
        financial_paginator = Paginator(financial_reports.order_by('-BUSINESS_DATE'), 5)  # Adjust the number per page as needed
        activity_paginator = Paginator(activity_reports.order_by('-TXN_DATE'), 5)
        financial_page_number = request.GET.get('financial_page')
        activity_page_number = request.GET.get('activity_page')
        financial_reports = financial_paginator.get_page(financial_page_number)
        activity_reports = activity_paginator.get_page(activity_page_number)

        # Render page
        return render(request, 'dual_reports.html', {
            'financial_form': financial_form,
            'activity_form': activity_form,
            'financial_filter': financial_filter,
            'activity_filter': activity_filter,
            'financial_reports': financial_reports,
            'activity_reports': activity_reports,
        })
    except Exception as e:
        return render(request, 'error_page.html', {'e': e})



def match_reports(request):
    try:
        # Check if it's the right action
        if request.method == 'POST' and request.POST.get('action') == 'match':
            # Retrieve filtering criteria from session, request, or direct input
            financial_criteria = request.session.get('financial_filter', {})
            activity_criteria = request.session.get('activity_filter', {})
            
            # Initialize filter forms with the stored criteria
            financial_form = FinancialReportFilterForm(financial_criteria)
            activity_form = ActivityReportFilterForm(activity_criteria)

            # Filter datasets based on the criteria

            financial_reports = filter_reports(financial_form) if financial_form.is_valid() else FinancialReport.objects.none()
      
            activity_reports = activity_filter_reports(activity_form) if activity_form.is_valid() else ActivtyReport.objects.all()

            # Convert QuerySets to DataFrames for matching
            financial_df = pd.DataFrame(list(financial_reports.values()))
            activity_df = pd.DataFrame(list(activity_reports.values()))

            # Match data (customize this as needed based on your matching logic)
            matched_df = pd.merge(financial_df, activity_df, how='inner', left_on=['TERMINAL_ID', 'FROM_ACCOUNT_NO', 'TRXN_TIME', 'REQUESTED_AMOUNT'], right_on=['ATM_BR_NUMBER', 'DR_ACCT', 'TXN_TIME', 'TXN_AMOUNT'])

            # Convert to Excel and respond for download
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="matched_reports.xlsx"'
            with pd.ExcelWriter(response, engine='openpyxl') as writer:
                matched_df.to_excel(writer, sheet_name='Matched Data')
                # Add additional logic here for unmatched data if necessary
            return response

        # Handle non-POST or incorrect action
        return redirect('reports_view')  # Adjust redirect as needed
    except Exception as e:
        return render(request, 'error_page.html', {'e': e})

@role_required('ADMIN','MANAGER')
def clear_data_view(request):
    try:
        if request.method == 'POST':
            FinancialReport.objects.all().delete()
            ActivtyReport.objects.all().delete()
            messages.success(request, 'All data from ModelOne and ModelTwo has been successfully deleted.')
            return redirect(reverse('home'))  # Adjust the redirect as needed
        else:  # GET request displays confirmation page
            return render(request, 'confirm_clear.html')
    except Exception as e:
        return render(request, 'error_page.html', {'e': e})
