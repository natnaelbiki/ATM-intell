import dask.dataframe as dd


def merge(df1, df2):
	# Convert pandas DataFrames to Dask DataFrames
	df1 = dd.from_pandas(df1, npartitions=4)  # Adjust npartitions based on your dataset size and memory
	df2 = dd.from_pandas(df2, npartitions=4)


	# Compute the result if necessary to view the changes (for Dask, this triggers computation)
	# Merge with an indicator to find matched and unmatched data
	merged = df1.merge( df2, left_on=['TERMINAL_ID', 'FROM_ACCOUNT_NO', 'TRXN_TIME'], 
		right_on=['ATM_BR_NUMBER', 'DR_ACCT', 'TXN_TIME'], how='outer', indicator=True)

	# Filter matched and unmatched data
	matched = merged[merged['_merge'] == 'both'].compute()
	unmatched_df2 = merged[merged['_merge'] == 'right_only'].compute()
	unmatched_df2 = unmatched_df2.drop(columns=['_merge'], errors='ignore')

	unmatched_df1 = merged[merged['_merge'] == 'left_only'].compute()
	unmatched_df1 = unmatched_df1.drop(columns=['_merge'], errors='ignore')
	return matched, unmatched_df1, unmatched_df2


def cbe_successful_merge():
	# Convert pandas DataFrames to Dask DataFrames
	df1 = dd.from_pandas(df1, npartitions=4)  # Adjust npartitions based on your dataset size and memory
	df2 = dd.from_pandas(df2, npartitions=4)


	# Compute the result if necessary to view the changes (for Dask, this triggers computation)
	# Merge with an indicator to find matched and unmatched data
	merged = df1.merge( df2, left_on=['TERMINAL_ID', 'REQUESTED_AMOUNT'], 
		right_on=['ATM_BR_NUMBER', 'TXN_AMOUNT'], how='outer', indicator=True)

	# Filter matched and unmatched data
	matched = merged[merged['_merge'] == 'both'].compute()
	unmatched_df2 = merged[merged['_merge'] == 'right_only'].compute()
	unmatched_df2 = unmatched_df2.drop(columns=['_merge'], errors='ignore')

	unmatched_df1 = merged[merged['_merge'] == 'left_only'].compute()
	unmatched_df1 = unmatched_df1.drop(columns=['_merge'], errors='ignore')
	return matched, unmatched_df1, unmatched_df2


def merge_other(df1, df2):
	# Convert pandas DataFrames to Dask DataFrames
	df1 = dd.from_pandas(df1, npartitions=4)  # Adjust npartitions based on your dataset size and memory
	df2 = dd.from_pandas(df2, npartitions=4)


	# Merge with an indicator to find matched and unmatched data
	merged = dd.merge(df1, df2, left_on=['TERMINAL_ID', 'TRXN_TIME'], 
		right_on=['ATM_BR_NUMBER', 'TXN_TIME'], how='outer', indicator=True)

	# Filter matched and unmatched data
	matched = merged[merged['_merge'] == 'both'].compute()
	unmatched_df2 = merged[merged['_merge'] == 'right_only'].compute()
	unmatched_df2 = unmatched_df2.drop(columns=['_merge'], errors='ignore')

	unmatched_df1 = merged[merged['_merge'] == 'left_only'].compute()
	unmatched_df1 = unmatched_df1.drop(columns=['_merge'], errors='ignore')

	return matched, unmatched_df1, unmatched_df2


def other_match_by_card_(df1, df2):
	# Creating helper columns for the merge condition
	df1['merge_key'] = df1['card_no'].str[:6] + df1['card_no'].str[-4:]
	df2['merge_key'] = df2['card number'].str[:6] + df2['card number'].str[-4:]

	# Merging based on the helper column
	merged_df = pd.merge(df1, df2, on='merge_key', how='inner')

	# Dropping the helper column as it's no longer needed after the merge
	merged_df.drop('merge_key', axis=1, inplace=True)
	print(merged_df)


