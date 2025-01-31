from datetime import datetime as dt
import pandas as pd
import re

rawdata = pd.read_excel('Example.xlsx',header=None)

#Find Date Report
date_index = rawdata.index[rawdata.iloc[:,0].astype(str).apply(lambda raw : bool(re.findall('Period',raw)))]
rawdate_str = rawdata.iloc[:,0].iloc[date_index].pop(0)
date_str = '-'.join(rawdate_str.split('-')[-3:]).replace(' ','')
date_report = dt.strptime(date_str,'%b-%d-%Y')

#Rename Columns and Select values
columns_index = rawdata.index[rawdata.iloc[:,0].astype(str).apply(lambda raw: bool(re.findall('^Article',raw)))].to_list().pop()
rawdata.iloc[columns_index-1] = rawdata.iloc[columns_index-1].ffill().astype(str)
rawdata.iloc[columns_index][2:] = rawdata.iloc[columns_index-1][2:].apply(lambda raw: raw.replace('Branch_Code:','').replace(' ',''))+' '+rawdata.iloc[columns_index][2:].apply(lambda raw:  re.findall(r'\((.*?)\)',raw.replace('.',''))[0])
rawdata.columns = rawdata.iloc[columns_index].to_list()
rawdata.drop(columns=['Description'],axis=1,inplace=True)
rawdata.drop(index=range(columns_index+1),axis=1,inplace=True)
rawdata = rawdata[rawdata['Article'].apply(lambda d: isinstance(d,int))]

#Unpivot
data_melt = pd.melt(rawdata, id_vars=['Article'],var_name='type',value_name='value')
data_melt = data_melt[(data_melt['value'].notna()) & (~ data_melt['type'].str.contains('Total', na=False))]
data_melt['branch_id'] = data_melt['type'].apply(lambda branch: branch[:4])

#split qty
data_qty = data_melt[data_melt['type'].str.contains('Qty', na=False)].drop(columns=['type']).copy()
data_qty.rename(columns={'Article':'barcode','value':'qty'},inplace=True)

#split amount
data_amount = data_melt[~ data_melt['type'].str.contains('Qty', na=False)].drop(columns=['type']).copy()
data_amount.rename(columns={'Article':'barcode','value':'amount'},inplace=True)

#final data
data = data_qty.merge(data_amount,how='inner',on=['barcode','branch_id'])
data['sale_date'] = date_report