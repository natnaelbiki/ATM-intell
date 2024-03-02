from django.urls import path
from .views import ( HomeView, reports_view, upload_and_clean_activity_report,
 upload_and_clean_financial_report, full_matching_view, view_financial_report, 
 upload_financial_report, view_activity_report, upload_activity_report, 
 match_view, match_reports, results_view, clear_data_view)
urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('reports_view', reports_view, name='reports_view'),
    path('match/', match_view, name='match_view'),
    path('full_match/', full_matching_view, name='full_match_view'),
    path('results/', results_view, name='results_view'),
    path('financial_reports', view_financial_report, name='view_financial_report'),
    path('upload_financial', upload_financial_report, name='upload_financial_report'),
    path('activity_reports', view_activity_report, name='view_activity_report'),
    path('upload_activity', upload_activity_report, name='upload_activity_report'),
    path('clean_financial_report', upload_and_clean_financial_report, name='clean_financial_report'),
    path('clean_activity_report', upload_and_clean_activity_report, name='clean_activity_report'),
    path('match_reports', match_reports, name='match_reports'),
    path('clear-data/', clear_data_view, name='clear_data'),
]
