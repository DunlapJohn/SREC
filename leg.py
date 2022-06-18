import requests
import pandas as pd
import numpy as np
import streamlit as st
from plotly.subplots import make_subplots
import plotly.express as px
from plotly.graph_objs import *
import plotly.graph_objs as go

st.set_page_config(layout="wide")

APIKEY='03c5237bcdfb510318c717be2b6f7434'
headers = {'x-api-key': APIKEY}
state = ["VA"]
length = len(state)
i = 0
sponsors_usa= []
subjects_usa =[]

states = ["CA", "CO", "CT", "DE", 
           "IL", "MD", 
          "MA", "MN", "NV", "NJ", 
          "NM", "NY",  "PA", "VA"]

option = st.selectbox(
     'Choose a State',
     (states))

st.write('You selected:', option)

STATE=option

uploaded_file = st.file_uploader(f"Upload Comma Seperated List (CSV) of Keywords to Query all of {STATE} Bill's Descriptions")
if uploaded_file is not None:
    df1=pd.read_csv(uploaded_file)
else:
   df1 = match = pd.read_csv ('match.csv')
   st.warning("Default CSV is [ Solar, RPS, REC ]")


while i < length:
    api_base_url = f"https://api.legiscan.com/?key={APIKEY}&op=getMasterList&state={STATE}"
    url_address = f"{api_base_url}"  
    r = requests.get(url=url_address, headers=headers)
    print(r.status_code)
    j = r.json()
    print(j.keys())
    df = pd.DataFrame(j['masterlist'])
    df=df.transpose()

    df=(df[['title','bill_id','number','description']])
    df = pd.DataFrame(df)


    match = pd.read_csv ('match.csv')
    df['applies']=df['description'].str.contains('|'.join(match))


    df =df.dropna()
    df=df.loc[df['applies']]
    print(df['bill_id'])   

    BILL_ID=df['bill_id']

    length = len(BILL_ID)
    i = 0



    subjects =[]
    sponsors  =[]
    support_level =[]
    opp_level =[]
    total_count=[]
    while i < length:
        api_base_url=f"https://api.legiscan.com/?key={APIKEY}&op=getBill&id={BILL_ID[i]}"
        url_address = f"{api_base_url}"  
        r = requests.get(url=url_address, headers=headers).json()['bill']
        
        sponsors_names = pd.json_normalize(r,record_path=['sponsors'])
        sponsors_names = (sponsors_names['name']).values
        sponsors_frame =pd.DataFrame(sponsors_names)


             
        b = pd.json_normalize(r, record_path=['votes'])
        if not b.empty:
            total=(b['total'])
            yea=(b['yea'])
            nay=(b['nay'])
            support=(yea/total).mean()
            opp=(nay/total).mean()
            total=total.sum()
            sponsors_frame[1]=(support)
            sponsors_frame[2]=(opp)
            sponsors_frame[3]=(total)
        else:
            sponsors_frame[1] = 0
            sponsors_frame[2] = 0
            sponsors_frame[3]=(0)



        for x in sponsors_frame[0]:
             sponsors.append(x)
        for x in sponsors_frame[1]:
             support_level.append(x)
        for x in sponsors_frame[2]:
             opp_level.append(x)
        for x in sponsors_frame[3]:
             total_count.append(x)
        # for y in sponsors_support:
        #      support.append(y)
             

        

            
            
        i=i+1

    sponsors =pd.DataFrame(sponsors)
    sponsors.rename(columns = {0:f'{STATE} Bill Sponsors'}, inplace = True)

    support_level =pd.DataFrame(support_level)
    support_level.rename(columns = {0:f'AVG {STATE} Bill Support'}, inplace = True)
    
    opp_level =pd.DataFrame(opp_level)
    opp_level.rename(columns = {0:f'AVG {STATE} Bill Opposition'}, inplace = True)
    
    total_count =pd.DataFrame(total_count)
    total_count.rename(columns = {0:f'Total {STATE} Bill Votes'}, inplace = True)
    
    support_level=pd.concat([support_level, sponsors], axis=1)
    support_level=pd.concat([support_level, opp_level], axis=1)
    support_level=pd.concat([support_level, total_count], axis=1)
    
    support_level[f'Number of {STATE} Bill CSV Sponsorships']= support_level[f'{STATE} Bill Sponsors'].map(sponsors[f'{STATE} Bill Sponsors'].value_counts())

    support_level=support_level.groupby([f'{STATE} Bill Sponsors'])[f'AVG {STATE} Bill Support',f'AVG {STATE} Bill Opposition',f'Number of {STATE} Bill CSV Sponsorships',f'Total {STATE} Bill Votes'].mean()
    support_level =pd.DataFrame(support_level)
    
    support_level[f'Total Vote {STATE} Bill Opposition'] = support_level[f'Total {STATE} Bill Votes']*support_level[f'AVG {STATE} Bill Opposition']
    support_level[f'Total Vote {STATE} Bill Support'] = support_level[f'Total {STATE} Bill Votes']*support_level[f'AVG {STATE} Bill Support']
    

    support_level=support_level.sort_values(by=f'AVG {STATE} Bill Support')
    support_level=support_level.reset_index()





# Figs


fig1 = go.Figure()
fig1.add_trace(go.Bar(name='AVG Support',
    x=support_level[f'{STATE} Bill Sponsors'],
    y=(support_level[f'AVG {STATE} Bill Support']), 
    ),)
fig1.add_trace(go.Bar(name='AVG Opposition',
    x=support_level[f'{STATE} Bill Sponsors'],
    y=(support_level[f'AVG {STATE} Bill Opposition'])*-1,
    ),)
fig1.update_layout( title_text="Double Y Axis Example")
fig1.update_xaxes(title_text="xaxis title")
fig1.update_yaxes(title_text="<b>AVG Sentiment</b>")
fig1.update_layout(title_text=f"{STATE} Assembly's AVG Sentiment Recorded all for Sponsered Bills Related to CSV")
st.plotly_chart(fig1, use_container_width=True)



support_level=support_level.sort_values(by=f'Total Vote {STATE} Bill Support')

fig2 = go.Figure()
fig2.add_trace(
    go.Bar(name='Total Support',
    x=support_level[f'{STATE} Bill Sponsors'],
    y=(support_level[f'Total Vote {STATE} Bill Support']), 
    ),)
fig2.add_trace(
    go.Bar(name='Total Opposition',
    x=support_level[f'{STATE} Bill Sponsors'],
    y=(support_level[f'Total Vote {STATE} Bill Opposition'])*-1,
    ),)
fig2.update_layout(title_text="Double Y Axis Example")
fig2.update_xaxes(title_text="xaxis title")
fig2.update_yaxes(title_text="<b>Number of Votes </b>")
fig2.update_layout(title_text=f"{STATE} Assembly's Number of Votes Recorded for all Sponsered Bills Related to CSV")
st.plotly_chart(fig2, use_container_width=True)




@st.cache
def convert_df(support_level):
     # IMPORTANT: Cache the conversion to prevent computation on every rerun
     return support_level.to_csv().encode('utf-8')

csv = convert_df(support_level)

st.download_button(
     label="Download Current Dataframe",
     data=csv,
     file_name=f'{STATE}_CSV_Bill_Sponsor_dataframe_Jack Dunlap.csv',
     mime='text/csv',
 )

support_level= pd.DataFrame(support_level)
   
st.table(support_level)


