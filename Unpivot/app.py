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

columns_sale = [i for i,col in enumerate (rawdata.iloc[columns_index].apply(lambda raw: bool(re.findall('^Sales',str(raw)))).to_list()) if col].pop(0)
rawdata.iloc[columns_index][columns_sale:] = rawdata.iloc[columns_index-1][columns_sale:].apply(lambda raw: raw.replace('Branch_Code:','').replace(' ',''))+'/'+rawdata.iloc[columns_index][columns_sale:].apply(lambda raw:  re.findall(r'\((.*?)\)',raw.replace('.',''))[0])

rawdata.columns = rawdata.iloc[columns_index].to_list()
rawdata.drop(columns=['Description'],axis=1,inplace=True)
rawdata.drop(index=range(columns_index+1),axis=1,inplace=True)
rawdata = rawdata[rawdata['Article'].apply(lambda d: isinstance(d,int))]

#Unpivot
data_melt = pd.melt(rawdata, id_vars=['Article'],var_name='type',value_name='value')
data_melt = data_melt[(data_melt['value'].notna()) & (~ data_melt['type'].str.contains('Total', na=False))]
data_melt[['branch_id', 'unit']] = data_melt['type'].apply(lambda x: pd.Series(x.split('/')))

#Pivot
data = data_melt.pivot(index=['Article', 'branch_id'], columns='unit', values='value').reset_index()
data.columns.name = None
data['sale_date'] = date_report
new_columns = {
    "Article":"shop_barcode",
    'Qty':'qty',
    'THB':'amount'
}
data.rename(columns=new_columns,inplace=True)