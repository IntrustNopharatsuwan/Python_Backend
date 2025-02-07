from fastapi import FastAPI
import pandas as pd

def combination_trsnsform(rawdata):
    #Merge and Clean Raw Data
    productmaster = pd.read_excel("Product Master.xlsx")
    mergedata = rawdata.merge(productmaster[['MATERIAL', 'MATERIAL REF']], how='left', on='MATERIAL')
    mergedata = mergedata[['MATERIAL', 'ORDER_CDATE', 'ORDER_NO', 'MATERIAL REF', 'QUANTITY']]
    mergedata['MAT'] = mergedata.apply(lambda d: d['MATERIAL REF'] if pd.notna(d['MATERIAL REF']) else d['MATERIAL'], axis=1)

    mergedata = mergedata.merge(productmaster[['MATERIAL','DESCRIPTION']], how='left', left_on='MAT',right_on='MATERIAL')
    mergedata = mergedata.groupby(['ORDER_NO','MAT','DESCRIPTION']).agg(QUANTITY = ('QUANTITY','sum')).reset_index()

    mergedata['PRODUCT'] = mergedata['DESCRIPTION'] + ' (' + mergedata['MAT'] +')_ [' + mergedata['QUANTITY'].astype(int).astype(str) + ']'
    mergedata = mergedata[['ORDER_NO', 'PRODUCT']]
    mergedata[['ORDER_NO', 'PRODUCT']] = mergedata[['ORDER_NO', 'PRODUCT']].astype(str)

    groupdata = mergedata.groupby('ORDER_NO')['PRODUCT'].agg(lambda x: ','.join(x)).reset_index()

    mixdata = groupdata.groupby(['PRODUCT']).count().reset_index()
    mixdata.sort_values(by=['ORDER_NO'],ascending=False,inplace=True)
    mixdata.columns = ['shortname (sku) [qty]','count order']

    split_df = mixdata[:1000]['shortname (sku) [qty]'].str.split(',', expand=True)
    result = pd.concat([mixdata[:1000][['count order']], split_df], axis=1)
    result.columns = ['count order'] + [f'product [qty] {i+1}' for i in range(split_df.shape[1])]
    result.reset_index(drop=True,inplace=True)


app = FastAPI()

@app.get("/combination")
def combination():
    rawdata = pd.read_excel("orders.xlsx")
    data = combination_trsnsform(rawdata)
    return data.to_dict(orient="records")