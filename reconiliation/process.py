def upload_files_view(request):
    try:
        if request.method == 'POST':
            form = UploadFilesForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    # Read uploaded files into DataFrames
                    excel_file1 = request.FILES['file1']
                    excel_file2 = request.FILES['file2']
                    df1 = pd.read_excel(excel_file1)
                    df2 = pd.read_excel(excel_file2)

                    # Save DataFrames to temporary files
                    temp_dir = tempfile.mkdtemp()
                    df1_path = os.path.join(temp_dir, 'df1.xlsx')
                    df2_path = os.path.join(temp_dir, 'df2.xlsx')
                    df1.to_excel(df1_path, index=False)
                    df2.to_excel(df2_path, index=False)

                    # Store file paths in session for access in processing view
                    request.session['df1_path'] = df1_path
                    request.session['df2_path'] = df2_path

                    return redirect('processing_view')
                except Exception as e:
                    error_trace = traceback.format_exc()
                    return HttpResponse(f"An error occurred: {str(error_trace)}")
            else:
                return render(request, 'upload.html', {'form': form})
        else:
            form = UploadFilesForm()
        return render(request, 'upload.html', {'form': form})
    except Exception as e:
        error_trace = traceback.format_exc()
        return HttpResponse(f"An error occurred: {str(error_trace)}")
    

def processing_view(request):
    try:
         # Retrieve file paths from session
        df1_path = request.session.get('df1_path')
        df2_path = request.session.get('df2_path')

        # Initialize context
        context = {}

        if df1_path and df2_path:
            try:
                # Load DataFrames from files
                financial_dataframe = pd.read_excel(df1_path)
                activity_dataframe = pd.read_excel(df2_path)

                # clean both data frames
                financial_dataframe = clean_financial_dataframe(financial_dataframe)
                activity_dataframe = clean_activity_dataframe(activity_dataframe)

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
                CBE_ONLY_FINANCIAL_SUCCESSFUL_MATCHED, CBE_ONLY_ACTIVITY_UNMATCHED = merge(CBE_ONLY_FINANCIAL_SUCCESSFUL, CBE_ONLY_ACTIVITY)
                
                CBE_ONLY_ACTIVITY_UNMATCHED = clean_unmatched_activity_dataframe(CBE_ONLY_ACTIVITY_UNMATCHED)
                CBE_ONLY_FINANCIAL_REVERSAL_MATCHED, CBE_ONLY_ACTIVITY_UNMATCHED = merge(CBE_ONLY_FINANCIAL_REVERSAL, CBE_ONLY_ACTIVITY_UNMATCHED)
                
                CBE_ONLY_ACTIVITY_UNMATCHED = clean_unmatched_activity_dataframe(CBE_ONLY_ACTIVITY_UNMATCHED)
                CBE_ONLY_FINANCIAL_FAILED_MATCHED, CBE_ONLY_ACTIVITY_UNMATCHED = merge(CBE_ONLY_FINANCIAL_FAILED, CBE_ONLY_ACTIVITY_UNMATCHED)
                CBE_ONLY_ACTIVITY_UNMATCHED = clean_unmatched_activity_dataframe(CBE_ONLY_ACTIVITY_UNMATCHED)
                
                #process other financial report
                OTHER_ONLY_FINANCIAL_SUCCESSFUL_MATCHED, OTHER_ONLY_ACTIVITY_UNMATCHED = merge_other(OTHER_ONLY_FINANCIAL_SUCCESSFUL, OTHER_ONLY_ACTIVITY)

                OTHER_ONLY_ACTIVITY_UNMATCHED = clean_unmatched_activity_dataframe(OTHER_ONLY_ACTIVITY_UNMATCHED)
                OTHER_ONLY_FINANCIAL_REVERSAL_MATCHED, OTHER_ONLY_ACTIVITY_UNMATCHED = merge_other(OTHER_ONLY_FINANCIAL_REVERSAL, OTHER_ONLY_ACTIVITY_UNMATCHED)

                OTHER_ONLY_ACTIVITY_UNMATCHED = clean_unmatched_activity_dataframe(OTHER_ONLY_ACTIVITY_UNMATCHED)
                OTHER_ONLY_FINANCIAL_FAILED_MATCHED, OTHER_ONLY_ACTIVITY_UNMATCHED = merge_other(OTHER_ONLY_FINANCIAL_FAILED, OTHER_ONLY_ACTIVITY_UNMATCHED)
                OTHER_ONLY_ACTIVITY_UNMATCHED = clean_unmatched_activity_dataframe(OTHER_ONLY_ACTIVITY_UNMATCHED)

                



                # Save the processed DataFrame to a new Excel file
                processed_file_name = 'processed_data.xlsx'
                processed_file_path = os.path.join(settings.MEDIA_ROOT, processed_file_name)
                

                with pd.ExcelWriter(processed_file_path, engine='openpyxl') as writer:
                    CBE_ONLY_FINANCIAL_SUCCESSFUL_MATCHED.to_excel(writer, sheet_name='CBE_FIN_ACT_SUCCESS_MATCHED', index=False)
                    CBE_ONLY_FINANCIAL_REVERSAL_MATCHED.to_excel(writer, sheet_name='CBE_FIN_ACT_REVERSAL_MATCHED', index=False)
                    CBE_ONLY_FINANCIAL_FAILED_MATCHED.to_excel(writer, sheet_name='CBE_FIN_ACT_FAILED_MATCHED', index=False)
                    OTHER_ONLY_FINANCIAL_SUCCESSFUL_MATCHED.to_excel(writer, sheet_name='OTH_FIN_ACT_SUCCESS_MATCHED', index=False)
                    OTHER_ONLY_FINANCIAL_REVERSAL_MATCHED.to_excel(writer, sheet_name='OTH_FIN_ACT_REVERSAL_MATCHED', index=False)
                    OTHER_ONLY_FINANCIAL_FAILED_MATCHED.to_excel(writer, sheet_name='OTH_FIN_ACT_FAILED_MATCHED', index=False)
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
                    #CBE matched



                # Update context for template
                context['file_name'] = processed_file_name
                context['status'] = 'Processing complete. Ready for download.'

                # Clean up: Remove temporary files and clear session paths
                os.remove(df1_path)
                os.remove(df2_path)
                del request.session['df1_path']
                del request.session['df2_path']

            except Exception as e:
                error_trace = traceback.format_exc()
                context['status'] = f"An error occurred: {str(error_trace)}"
        else:
            context['status'] = "No data available for processing."

        return render(request, 'processing.html', context)
    except Exception as e:
       error_trace = traceback.format_exc()
       return HttpResponse(f"An error occurred: {str(error_trace)}")

def download_view(request, file_name):
    try:
    # Construct the file path using the name
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)  # Ensure MEDIA_ROOT is configured
        
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                return response
        else:
            return HttpResponse("File not found.")
    except Exception as e:
        return HttpResponse(f"An error occurred: {str(e)}")
