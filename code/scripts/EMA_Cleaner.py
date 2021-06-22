#!/usr/bin/env python3
""" 
Script that imports the exported castor file containing data from EMA surveys, 
and applies different cleaning methods to both sleep and wake surveys:
    - Outputs the percent of surveys compeletted, drops those with incomplete surveys
    - Renames variables with space in names
    - Fixes issues with subjects IDs
    - Assign which surveys were in control vs stress weeks
    - For sleep surveys: calcualte date time, and time of sleep

Authors:        Rayyan Toutouni, Margo Willems
Last Modified:  05-JUN-2019

"""

#Import Libraries
import os
import numpy as np
import pandas as pd
import datetime as dt
from datetime import datetime, timedelta

#Turnoff write warning in Pandas
pd.options.mode.chained_assignment = None  

#File Path Location
filepath = ("/project/3013068.02/stats/EMA/")
os.chdir (str(filepath))
file = "EMA.xlsx"

#Read excel into dataframe for sleep and wake surveys
Day_df = pd.read_excel(file, '2._Momentary_Assessment')
Sleep_df = pd.read_excel(file, "1._Sleep_Assessment", header = 0, index_col = None)
EMA_n_tot= len(Day_df.index)
Sleep_n_tot= len(Sleep_df.index)


#Place imported df in array to loop
dfs=[Day_df, Sleep_df]
for index, EMA_df in enumerate(dfs):
    
    #Drop incomplete data, report percent complete
    #EMA_df = EMA_df[EMA_df['Survey Progress'] >= 100]
    EMA_n_com= len(EMA_df.index)
    if index==0:
       print('EMA Percent complete: '+str((EMA_n_com/EMA_n_tot)*100))
    else:
        print('Sleep Percent complete: '+str((EMA_n_com/Sleep_n_tot)*100))
        
    #Reformat Subject IDs
    EMA_df['Castor Record ID'] = EMA_df['Castor Record ID'].str.slice(0,7)
    
    #Reformat date-time so day is read firt
    EMA_df['Survey Completed On'] = pd.to_datetime(EMA_df['Survey Completed On'], dayfirst=True)
    
    #Make variable with date only for setting stress vs control weeks
    EMA_df['Survey_Date'] = EMA_df['Survey Completed On']
    EMA_df['Survey_Date'] = EMA_df['Survey Completed On'].astype(str)
    EMA_df['Survey_Date'] = EMA_df['Survey_Date'].str.slice(0,10)
    
    #Set first days of stress weeks
    Stress_Weeks=['2018-04-04', '2018-05-18', '2018-06-20', '2018-09-28', '2018-10-31', 
                  '2018-12-07', '2019-01-23', '2019-03-01', '2019-04-03', '2019-05-17',
                  '2019-06-19', '2019-09-27', '2019-10-30', '2019-12-06']
    stress_days = Stress_Weeks.copy()
    len_weeks=len(Stress_Weeks)
    
    #Loop to make weeks 7 days from start of each stress week
    for k in range(1,7):
        for i in range (0,len_weeks):
            #First convert the string to date time
            date_1 = dt.datetime.strptime((str(Stress_Weeks[i])), '%Y-%m-%d')
            #Add one day to that
            add_date= date_1 + dt.timedelta(days=k)
            #Append it to new list
            stress_days.append(str(add_date))
            
    #Function to shorten day string, then application       
    def remove_cruft(s):
        return s[0:10]
    stress_days=[remove_cruft(s) for s in stress_days]
    
    #Make a week type variable (1=Control, 2=Stress): First make all weeks into
    #a string with the OR line in between
    makeitastring = '|'.join(map(str, stress_days))
    
    #Condition in which date contains string (from above), and choices
    condition_EMA= [EMA_df['Survey_Date'].str.contains(makeitastring)]
    choices=[2]
    #Apply condition to week variable
    EMA_df['Week_Type'] = np.select(condition_EMA, choices, default=1)
    
    #Save Cleaned data file for EMA, for sleep do more stuff though
    if index == 0:
        EMA_df.columns = EMA_df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('(', '').str.replace(')', '')
        clean_file="EMA_Clean.csv"
        EMA_df.to_csv (clean_file, index = None, header=True)
        CP_Day_df=EMA_df
        #EMA_1_df =
    else:
        #Clean column headers, remove firts survey
        EMA_df.columns = EMA_df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('(', '').str.replace(')', '')
        EMA_df=EMA_df[EMA_df.survey_package_name != 'EMA 1.1']
        
        #Combine day and time (as string) reported for wake/sleep into date time
        ##Wake
        EMA_df["sleep_up_dt"] = EMA_df["sleep_up"].map(str) + ' ' + EMA_df["survey_date"]
        EMA_df['sleep_up_dt'] = pd.to_datetime(EMA_df['sleep_up_dt'], errors='coerce')
        ##Sleep
        EMA_df["sleep_down_dt"] = EMA_df["sleep_down"].map(str) + ' ' + EMA_df["survey_date"]
        EMA_df['sleep_down_dt'] = pd.to_datetime(EMA_df['sleep_down_dt'], errors='coerce')
        
        #Convert the time variable from string to time
        EMA_df['sleep_down'] = pd.to_datetime(EMA_df['sleep_down'], format='%H:%M').dt.time
        EMA_df['sleep_up'] = pd.to_datetime(EMA_df['sleep_up'], format='%H:%M').dt.time
        EMA_df=EMA_df.set_index(EMA_df.sleep_down_dt)
        
        #calculate time slept without correcting dt differences
        EMA_df['sleep_time']=abs((EMA_df['sleep_up_dt']-EMA_df['sleep_down_dt']).astype('timedelta64[m]'))/60
        
        #Correct for date time issues by subtracting 1 day if sleep longer than 12 hours
        #Set condition and choices
        conditions = [EMA_df['sleep_time'] > 12]
        choices = [EMA_df.sleep_down_dt-pd.DateOffset(1)]
        #Apply above conditions
        EMA_df['sleep_down_dt'] = np.select(conditions, choices, default=EMA_df['sleep_down_dt'])
        
        #Recalculate the propper time slept
        EMA_df['sleep_time']=abs((EMA_df['sleep_up_dt']-EMA_df['sleep_down_dt']).astype('timedelta64[m]'))/60
         
        #Make a df with waking EMA Surveys
        EMA_Sleep_df=CP_Day_df[
                (CP_Day_df.survey_package_name == 'EMA 2.1') | (CP_Day_df.survey_package_name == 'EMA 3.1')|
                (CP_Day_df.survey_package_name == 'EMA 4.1') | (CP_Day_df.survey_package_name == 'EMA 5.1')|
                (CP_Day_df.survey_package_name == 'EMA 6.1') | (CP_Day_df.survey_package_name == 'EMA 7.1')]

        #Merge with sleep questionnaires
        EMA_df=EMA_df.sort_values('survey_date')   
        EMA_Sleep_df=EMA_Sleep_df.sort_values('survey_date')
        EMA_df=EMA_df.set_index('survey_instance_id')
        EMA_Sleep_df=EMA_Sleep_df.set_index('survey_instance_id')
        
        #Drop extremes
        full_Sleep_df=pd.merge(EMA_df, EMA_Sleep_df)
        full_Sleep_df = full_Sleep_df.drop(full_Sleep_df[full_Sleep_df.sleep_time >40].index)
        full_Sleep_df = full_Sleep_df.drop(full_Sleep_df[full_Sleep_df.sleep_time <3].index)
        
        #Output to csv
        clean_file="Sleep_Clean.csv"
        full_Sleep_df.to_csv (clean_file, index = None, header=True)
        
        
    
