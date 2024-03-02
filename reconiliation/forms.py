from django import forms
from .models import FinancialReport, ActivtyReport

MATCHING_FIELDS_FINANCIAL = [
    ('TERMINAL_ID', 'TID'),
    ('FROM_ACCOUNT_NO', 'ACCOUNT'),
    ('REQUESTED_AMOUNT', 'AMOUNT'),
    ('TRXN_TIME', 'TIME'),
]

MATCHING_FIELDS_ACTIVITY = [
    ('ATM_BR_NUMBER', 'TID'),
    ('DR_ACCT', 'ACCOUNT'),
    ('TXN_AMOUNT', 'AMOUNT'),
    ('TXN_TIME', 'TIME'),
]
class UploadFinancialReportForm(forms.Form):
    file = forms.FileField()

class UploadActivityReportForm(forms.Form):
    file = forms.FileField()

class FullReportMatchForm(forms.Form):
    financial_report = forms.FileField(label='Financial Report')
    activity_report = forms.FileField(label='Activity Report')

class FinancialUploadForm(forms.Form):
    financial_report = forms.FileField(label='Financial Report')

class ActivtyUploadForm(forms.Form):
    activity_report = forms.FileField(label='Activity Report')


class FinancialReportForm(forms.ModelForm):
    class Meta:
        model = FinancialReport
        fields = '__all__'
        exclude = ('added_by',)


class ActivityReportForm(forms.ModelForm):
    class Meta:
        model = ActivtyReport
        fields = '__all__'
        exclude = ('added_by',)

class ReportUploadForm(forms.Form):
    financial_file = forms.FileField(required=False, label='Financial Report File')
    activity_file = forms.FileField(required=False, label='Activity Report File')
    financial_data = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Paste Financial Data here'}), required=False)
    activity_data = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Paste Activity Data here'}), required=False)

class DataUploadForm(forms.Form):
    financial_file = forms.FileField(required=False, label='Financial Report File')
    activity_file = forms.FileField(required=False, label='Activity Report File')
    financial_data = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Paste Financial Data here'}), required=False)
    activity_data = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Paste Activity Data here'}), required=False)



class FinancialReportFilterForm(forms.Form):
    bank = forms.ChoiceField(choices=[('', '--Select bank--')] + [(bank, bank) for bank in FinancialReport.objects.values_list('bank', flat=True).distinct()], required=False)
    terminal_id = forms.CharField(max_length=100, required=False, label="Terminal ID")
    business_date_start = forms.DateField(required=False, label="Business Date From")
    business_date_end = forms.DateField(required=False, label="Business Date To")
    from_account_no = forms.CharField(max_length=100, required=False, label="From Account No")
    status = forms.ChoiceField(choices=[('', '--Select status--')] + [(STATUS, STATUS) for STATUS in FinancialReport.objects.values_list('STATUS', flat=True).distinct()], required=False)

class ActivityReportFilterForm(forms.Form):
    bank = forms.ChoiceField(choices=[('', '--Select bank--')] + [(bank, bank) for bank in FinancialReport.objects.values_list('bank', flat=True).distinct()], required=False)
    terminal_id = forms.CharField(max_length=100, required=False, label="ATM_BR_NUMBER")
    txn_date_start = forms.DateField(required=False, label="Business Date From")
    txn_date_end = forms.DateField(required=False, label="Business Date To")
    from_account_no = forms.CharField(max_length=100, required=False, label="From Account No")
