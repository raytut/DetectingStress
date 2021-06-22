"""

This script accepts either an input argument for a subject (with edits) or will
loop over subjects to convert their multiple E4 sessions into a single csv file 
for stress and control weeks. 

Given a subject ID, it will access the folder, extract the time stamps,
merge all sessions with timestamps into one file, and save it as a single file
with all time stamps for each data pount. 

    - Time stamps are calcualted by adding the sampling frequency to the 
        start time of the recording
    - ACC data is also inclueds a calculation for mean displacement taking 
        the XYZ directions into a single value
    - IBI timestamps are derived by adding the time from onset to the start 
        time of the recording
        
        
Author:         Rayyan Toutounji
Last Modified:  08-APR-2020

"""

#Import Libraries
import os, errno, ast
import numpy as np
import pandas as pd
import datetime as dt
from datetime import timedelta

#Turnoff write warning in Pandas
pd.options.mode.chained_assignment = None  


#Loop over subjects
for sub_nr in range(1,200):
    #Print which subject, and set directories
    print ('Processing subject number ' + str(sub_nr))
    #Set sub nr as padded string
    sub=str(sub_nr)
    sub = sub.rjust (3, '0')
    #Make array with the two sessions for loop
    sessions = ['control/', 'stress/']
    for session_type in sessions:
        
        #Path with E4 files. Only run if the files exist
        filepath = ("/project/3013068.02/data/3013068.02_BaLS_sub_" + str(sub) + "/logs/e4/"+str(session_type))
        if os.path.isdir(filepath)==True:
            if len(os.listdir(filepath) ) >= 1:
                
                #Set as working directory
                os.chdir (str(filepath))
                
                #Check if merge directory (for output) exists, if not then make it
                try:
                    os.makedirs('merge/')
                except FileExistsError:
                    pass
                
                #Set E4 data types for loop
                data_types=['EDA.csv','TEMP.csv', 'IBI.csv','BVP.csv', 'HR.csv', 'ACC.csv']
                for data_type in data_types:
                   
                    #Get all directories with E4 sessions for subject, merge directory from the list
                    directories = [x[1] for x in os.walk(filepath)]
                    dir_list=[item for item in directories[0]]
                    dir_list.remove('merge')  
                    
                    #Make Empty DF as master df for data type
                    full_df=pd.DataFrame()
                    
                    #IBI is special case
                    if data_type=='IBI.csv':
                        
                        #Select Directory from available list
                        for k in dir_list:
                            
                            #Select File for single session, import as df
                            file_name=((str(k))+'/'+ data_type)
                            
                            #Only run if IBI files contains data (Skip over empty files)
                            if os.stat(file_name).st_size!=0:
                                
                                #Read CSV
                                df=pd.read_csv(file_name, sep=',', header=0)
                                #Get time stamp
                                time=list(df)
                                time=time[0]
                                time=float(time) 
                                
                                #Rename time column to time, data to Data
                                df=df.rename(columns={ df.columns[0]: "Time" })
                                df=df.rename(columns={ df.columns[1]: "Data" })
                                
                                #Add the starttime from time stamp (time) to the column+Convert to datetime
                               # time=dt.datetime.fromtimestamp(time)
                                df['Time']=time + df['Time']
                                df['Time']=pd.to_datetime(df['Time'],unit='s')
                            
                                #Append to master data frame the clear it for memory
                                full_df =full_df.append(df)[df.columns.tolist()]
                                df=pd.DataFrame()
                                
                        #Convert IBI to ms and sort by date:
                        full_df['Data']=full_df['Data']*1000
                        full_df = full_df.sort_values('Time', ascending=True)
                        
                        #Set Output Names and direcotries, save as csv
                        outputdir=('merge/')
                        outputname='full_'+str(data_type)
                        fullout=(str(outputdir)+str(outputname))
                        full_df.to_csv(str(fullout),sep='\t',index=False)
                        
                    #ACC also special case, implement alternate combination method
                    elif data_type=='ACC.csv':
                        
                        #Select Directory, go through files
                        for k in dir_list:
                            
                            #Select File, Import as df
                            file_name=((str(k))+'/'+ data_type)  
                            df=pd.read_csv(file_name, sep=',', header=0)
                            
                            #Get time stamp (Used Later)
                            time=list(df)
                            time=time[0]
                            time=float(time) 
                            
                            #Get Sampling Frequency, convert to time
                            samp_freq=df.iloc[0,0]
                            samp_freq=float(samp_freq)
                            samp_time=1/samp_freq
                        
                            #Drop sampling rate from df (first row)
                            df=df.drop([0])
                            
                            #Rename data columns to corresponding axes
                            df=df.rename(columns={ df.columns[0]: "ACC_X" })
                            df=df.rename(columns={ df.columns[1]: "ACC_Y" })
                            df=df.rename(columns={ df.columns[2]: "ACC_Z" })
                                    
                            #Make array of time stamps
                            df_len=len(df)
                            time=pd.to_datetime(time,unit='s')
                            times = [time]
                            for i in range (1,(df_len)):
                                time = time + timedelta(seconds=samp_time)
                                times.append (time)
        
                            #Add time and data to dataframe
                            df['Time'] = times
                            
                            #Append to master data frame
                            full_df =full_df.append(df)
                            df=pd.DataFrame()
                        #Sort master by date:
                        full_df = full_df.sort_values('Time', ascending=True)
                        
                        #Set Output Names and direcotries, save as csv
                        outputdir=('merge/')
                        outputname='full_'+str(data_type)
                        fullout=(str(outputdir)+str(outputname))
                        full_df.to_csv(str(fullout),sep='\t',index=False)
                        
                    #All other data structures:              
                    else:
                        for k in dir_list:
                            #Select File, Import to df
                            file_name=((str(k))+'/'+ data_type)  
                            df=pd.read_csv(file_name, sep=',', header=0)
                            ##Get start time+sampling frequency
                            start_time = list(df)
                            start_time=start_time[0]
                            samp_freq=df.iloc[0,0]
                            #Change samp freq to samp time
                            samp_time=1/samp_freq
                            #Drop sampling rate from df
                            df=df.drop([0])
                            #Convert start time to date time
                            start_time=int(float(start_time))
                            start_time=pd.to_datetime(start_time,unit='s')
                            #Make array of time
                            file_len=len(df)	
                            times = [start_time]
                            for i in range (1,(file_len)):
                                start_time = start_time + timedelta(seconds=samp_time)
                                times.append (start_time)
                            #Add time and data to dataframe
                            df['Time']= times
                            #Rename first column to Data
                            df=df.rename(columns={df.columns[0]: "Data" })
                            #Append to master data frame
                            full_df =full_df.append(df)
                            df=pd.DataFrame()
                        
                        #Sort by date:
                        full_df = full_df.sort_values('Time', ascending=True)
                        
                        #Set Output Names and direcotries
                        outputdir=('merge/')
                        outputname='full_'+str(data_type)
                        #Output Raw File
                        fullout=(str(outputdir)+str(outputname))
                        full_df.to_csv(str(fullout),sep='\t',index=False)
        
            
    
        
    
    
    
    
