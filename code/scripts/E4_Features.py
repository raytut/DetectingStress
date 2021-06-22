#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" 
This script extracts features from the E4 data during wake and sleep periods, 
calcualtes different components of heart rate, and skin conductance within a 
time window specified by self reported measures.  This code will go through 
the cleaned EMA file (as a dataframe) line by line to extract the features 
for a given subject and EMA sample.

Authors:    Rayyan Toutounji
Date:       15-JUN-20
"""

# Import Libraries
import os
import numpy as np
import pandas as pd
import datetime as dt
from scipy import signal
from datetime import datetime, timedelta
# Import pyphysio for physio analysis
import pyphysio as ph
import pyphysio.filters.Filters as flt # Import filters
import pyphysio.estimators.Estimators as est # Import Estimators
import pyphysio.indicators.TimeDomain as td_ind # Import time domain
import pyphysio.indicators.FrequencyDomain as fd_ind # Import frequency domain estimators
import pyphysio.indicators.PeaksDescription as pk_ind # Import peak domain estimators
#Turnoff write warning in Pandas
pd.options.mode.chained_assignment = None  

#Import EMA data (cleaned beforehand)
filepath = ("/project/3013068.02/stats/EMA/")
os.chdir (str(filepath))
Wake_df = pd.read_csv("EMA_Clean.csv")
Sleep_df = pd.read_csv("Sleep_Clean.csv")
EMA_dfs = [Wake_df, Sleep_df]

#Extract Features from Both
for x, EMA_df in enumerate(EMA_dfs):
    EMA_df=EMA_df.sort_values('castor_record_id')  # Sort by subject ID
    #EMA_df=EMA_df[EMA_df.castor_record_id == 'sub_026'] #This line is for testing
    #Reformat datetimes for survey completion
    EMA_df['survey_completed_on']=pd.to_datetime(EMA_df['survey_completed_on'], format='%Y-%m-%d %H:%M:%S')
    
    #Reformat dates for sleep data + add extra coloumns for SCR storms
    if x==1: 
        EMA_df['sleep_down_dt']=pd.to_datetime(EMA_df['sleep_down_dt'], format='%Y-%m-%d %H:%M:%S')
        EMA_df['sleep_up_dt']=pd.to_datetime(EMA_df['sleep_up_dt'], format='%Y-%m-%d %H:%M:%S')
        sleep_feat=['sc_storm_tonic_mean', 'sc_storm_phasic_mean', 'sc_storm_phasic_mag',
                    'sc_storm_phasic_dur', 'sc_storm_phasic_num', 'sc_storm_phasic_auc']
        for i in sleep_feat:
            EMA_df[i]=np.nan
            
    #Initialize empty columns for features
    feats=['hr_mean','ibi_sd', 'ibi_mean', 'ibi_min', 'ibi_max', 
           'hr_rmssd', 'hr_sd','hr_min', 'hr_max', 'hr_hf', 'hr_lf', 'hr_lfhf',
           'sc_tonic_mean','sc_tonic_std','sc_tonic_range',
           'sc_phasic_mean', 'sc_phasic_std','sc_phasic_range',
           'sc_phasic_mag', 'sc_phasic_dur', 'sc_phasic_num','sc_phasic_auc',
           'temp_mean', 'temp_median', 'temp_sd', 'temp_slope',
           'acc_x', 'acc_y','acc_z', 'acc_delta', 'acc_x_sd', 'acc_y_sd','acc_z_sd', 'acc_delta_sd',
           'ibi_based_quality']
    for i in feats:
        EMA_df[i]=np.nan

    
    sub_echo='o' # used for tracking which subject we are at
    #Go through sleep df row by row
    for ind in EMA_df.index:
        #Get sub_ID
        sub_ID=EMA_df['castor_record_id'][ind]
        # Survey completion time
        survey_time=EMA_df['survey_completed_on'][ind]
        # Select time window for feature extraction
        if x==0:#For wake
            start_time=survey_time - pd.Timedelta(minutes=13)
            end_time=survey_time - pd.Timedelta(minutes=3)
            df_name='wake'
        elif x==1:#For sleep
            start_time=EMA_df['sleep_down_dt'][ind]
            end_time=EMA_df['sleep_up_dt'][ind]
            df_name='sleep'
          
        #Check if subject is new to reduce loading times
        if sub_echo != sub_ID:
            sub_echo=sub_ID
            now = dt.datetime.now()
            current_time=now.strftime("%Y-%m-%d %H:%M:%S")
            print ("Subject " + sub_echo + " " + df_name +" data started at " + current_time)
            
            #Clear variables for memory issues
            full_BVP=None
            full_IBI= None
            full_HR=None
            full_SCR=None
            full_temp=None
            full_ACC=None
            #Make empty DF to append all data
            full_BVP=pd.DataFrame()
            full_IBI=pd.DataFrame()
            full_HR=pd.DataFrame()
            full_SCR=pd.DataFrame()
            full_temp=pd.DataFrame()
            full_ACC=pd.DataFrame()
            
            #Two session in data
            sessions = ['control', 'stress']
            for session_type in sessions:
                #Set the file path and check if it exists to avoid errors. If it doesnt make empty DFs instead
                filepath1 = ("/project/3013068.02/data/3013068.02_BaLS_" + sub_ID + "/logs/e4/"+str(session_type) + "/merge")
                if os.path.isdir(filepath1)==True:                              
                    if len(os.listdir(filepath1) ) >= 1:
                        os.chdir (str(filepath1))
                         ## BVP
                        one_bvp= pd.read_csv("full_BVP.csv", sep='\t')
                        one_bvp['Time']=pd.to_datetime(one_bvp['Time'], format='%Y-%m-%d %H:%M:%S')
                        full_BVP=full_BVP.append(one_bvp)
                        ## IBI
                        one_IBI= pd.read_csv("full_IBI.csv", sep='\t')
                        one_IBI['Time']=pd.to_datetime(one_IBI['Time'], format='%Y-%m-%d %H:%M:%S')
                        full_IBI=full_IBI.append(one_IBI)
                        ## HR
                        one_HR= pd.read_csv("full_HR.csv", sep='\t')
                        one_HR['Time']=pd.to_datetime(one_HR['Time'], format='%Y-%m-%d %H:%M:%S')
                        full_HR=full_HR.append(one_HR)
                        ## SCR
                        one_SCR= pd.read_csv("full_EDA.csv", sep='\t')
                        one_SCR['Time']=pd.to_datetime(one_SCR['Time'], format='%Y-%m-%d %H:%M:%S')
                        full_SCR=full_SCR.append(one_SCR) 
                        ## Temp
                        one_temp= pd.read_csv("full_TEMP.csv", sep='\t')
                        one_temp['Time']=pd.to_datetime(one_temp['Time'], format='%Y-%m-%d %H:%M:%S')
                        full_temp=full_temp.append(one_temp)
                        ## ACC
                        one_acc= pd.read_csv("full_ACC.csv", sep='\t')
                        one_acc['Time']=pd.to_datetime(one_acc['Time'], format='%Y-%m-%d %H:%M:%S')
                        full_ACC=full_ACC.append(one_acc)
                 
            
        #Now check if the data frames are empty by sampling one, to make sure we 
        # dont try to source empty DFs that flag errors. 
        if full_SCR.size >= 10:
            
            #Select the data in time window + make a copy for the FFT
            temp_bvp = full_BVP[(full_BVP.Time > start_time) & (full_BVP.Time < end_time)]  
            temp_IBI = full_IBI[(full_IBI.Time > start_time) & (full_IBI.Time < end_time)]   
            temp_HR = full_HR[(full_HR.Time > start_time) & (full_HR.Time < end_time)] 
            temp_SCR= full_SCR[(full_SCR.Time > start_time) & (full_SCR.Time < end_time)] 
            temp_temp= full_temp[(full_temp.Time > start_time) & (full_temp.Time < end_time)]  
            temp_ACC = full_ACC[(full_ACC.Time > start_time) & (full_ACC.Time < end_time)] 
            
            #Only run if file longer than 10 samples
            if temp_IBI.size > 100:
                
                #Set index as time for FFT, and resample to 4hz
                IBI_fft = temp_IBI
                IBI_fft = IBI_fft.set_index(IBI_fft.Time)
                IBI_fft = IBI_fft.drop('Time', axis=1)
                IBI_fft = IBI_fft.resample('250ms').apply(np.mean)
                IBI_fft = IBI_fft.interpolate(method='nearest')
            
                #Apply a hanning window to the data
                signal_len = IBI_fft.Data.size
                hann_window = np.hanning(signal_len)
                hann_window = hann_window/np.sum(hann_window)
                IBI_fft = IBI_fft['Data']*hann_window
                
                #Do fast fourier transformation, with frequency
                IBI_fft = np.abs(np.fft.fft(IBI_fft)) #Fast fourier  
                IBI_freqs = IBI_fft**2   # Power
                #IBI_freqs= np.fft.fftfreq(IBI_fft.shape[-1])
                
                #Set cutoffs for high and low frequency components    
                LF_start = np.round(0.05/(4/signal_len))
                LF_stop = np.round(0.15/(4/signal_len))
                HF_start = np.round(0.15/(4/signal_len))
                HF_stop = np.round(0.4/(4/signal_len))
                
                #Calcualte LF, HF, and Ratio
                EMA_df['hr_lf'][ind]=np.sum(IBI_freqs[int(LF_start):int((LF_stop))])
                EMA_df['hr_hf'][ind]=np.sum(IBI_freqs[int(HF_start):int((HF_stop))])
                EMA_df['hr_lfhf'][ind]= (EMA_df['hr_lf'][ind])/(EMA_df['hr_hf'][ind])
                        
                #Calculate mean, standard deviation, max, min, RMSSD HR from data
                EMA_df['ibi_mean'][ind] = np.mean(temp_IBI['Data'])
                EMA_df['ibi_sd'][ind] = np.std(temp_IBI['Data']) 
                EMA_df['ibi_min'][ind] = np.min(temp_IBI['Data']) 
                EMA_df['ibi_max'][ind] = np.max(temp_IBI['Data']) 
                EMA_df['hr_rmssd'][ind] = np.sqrt(np.mean(np.square(np.diff(temp_IBI['Data']))))
                EMA_df['hr_mean'][ind] = np.mean(temp_HR.Data)
                EMA_df['hr_sd'][ind] = np.std(temp_HR['Data']) 
                EMA_df['hr_min'][ind] = np.min(temp_HR['Data']) 
                EMA_df['hr_max'][ind] = np.max(temp_HR['Data']) 
                
                # Get quality index from IBI:
                ibi_durations=(np.sum(temp_IBI.Data))/1000
                ibi_quality_index=ibi_durations/((10*60))
                EMA_df['ibi_based_quality'][ind]=ibi_quality_index
            #SC part
            ##If SC data too short, fill with nans
            if (temp_SCR['Data'].size > 20) & (np.mean(temp_SCR.Data) > 0.009):

                # Make eda signal into pyphysio
                eda_data=np.array(temp_SCR.Data)           
                eda_data = ph.EvenlySignal(values=eda_data, sampling_freq=4, signal_type ="eda", start_time=0)  
                
                try:
                    # Data cleaning (despike, highpass, low pass threshold)
                    eda_despike= flt.RemoveSpikes()(eda_data)
                    eda_denoise= flt.DenoiseEDA(threshold=0.02)(eda_despike)
                    eda_clean= ph.IIRFilter(fp=0.8, fs = 1.1, ftype='ellip')(eda_denoise)
                    
                    # Estimate signal drivers, 
                    eda_driver = ph.DriverEstim()(eda_clean)
                    # Separate tonic and phasic components
                    eda_phasic, eda_tonic, _ = ph.PhasicEstim(delta=0.02)(eda_driver)
                    
                    #Get Tonic Dirvet Components
                    EMA_df['sc_tonic_mean'][ind]=td_ind.Mean(delta=0.02)(eda_tonic)
                    EMA_df['sc_tonic_std'][ind]=td_ind.StDev(delta=0.02)(eda_tonic)
                    EMA_df['sc_tonic_range'][ind]=td_ind.Range(delta=0.02)(eda_tonic)
                    # Phasic components
                    EMA_df['sc_phasic_mean'][ind] =td_ind.Mean(delta=0.02)(eda_phasic)
                    EMA_df['sc_phasic_std'][ind] =td_ind.StDev(delta=0.02)(eda_phasic)
                    EMA_df['sc_phasic_range'][ind] =td_ind.Range(delta=0.02)(eda_phasic)
                    # Phasic Peaks
                    EMA_df['sc_phasic_mag'][ind]=pk_ind.PeaksMean(delta=0.02, win_pre=1, win_post=8)(eda_phasic)
                    EMA_df['sc_phasic_dur'][ind]= pk_ind.DurationMean(delta=0.02, win_pre=1, win_post=8)(eda_phasic)
                    EMA_df['sc_phasic_num'][ind]=pk_ind.PeaksNum(delta=0.02)(eda_phasic)
                    EMA_df['sc_phasic_auc'][ind]=td_ind.AUC(delta=0.02)(eda_phasic)
                except:
                    print ( sub_ID + ' time point ' + str(start_time)+  ' to ' +  str(end_time)  + ' failed...' )
                
                # For sleep, also get SCR storms
                if x==1: 
                    scr_storm_len=int(round(len(temp_SCR.Data)*0.25))
                    scr_end= temp_SCR.Time.iloc[scr_storm_len]
                    temp_SCR_storm=full_SCR[(full_SCR.Time > start_time) & (full_SCR.Time < scr_end)] 
                    
                    # Make eda signal into pyphysio
                    eda_storm_data=np.array(temp_SCR_storm.Data)           
                    eda_storm_data = ph.EvenlySignal(values=eda_storm_data, sampling_freq=4, 
                                                     signal_type = 'eda', start_time=0)  
                    try:
                        # Data cleaning (despike, highpass, low pass threshold)
                        eda_storm_despike= flt.RemoveSpikes()(eda_storm_data)
                        eda_storm_denoise= flt.DenoiseEDA(threshold=0.02)(eda_storm_despike)
                        eda_storm_clean= ph.IIRFilter(fp=0.1, fs = 1.1, ftype='ellip')(eda_storm_denoise)
                        
                        # Estimate signal drivers, 
                        eda_storm_driver = ph.DriverEstim()(eda_storm_clean)
                        # Separate tonic and phasic components
                        eda_storm_phasic, eda_storm_tonic, _ = ph.PhasicEstim(delta=0.02)(eda_storm_driver)
                        
                        # Add to dataframe
                        EMA_df['sc_storm_tonic_mean'][ind]=td_ind.Mean(delta=0.02)(eda_storm_tonic)
                        # Phasic components
                        EMA_df['sc_storm_phasic_mean'][ind] =td_ind.Mean(delta=0.02)(eda_storm_phasic)
                        # Phasic Peaks
                        EMA_df['sc_storm_phasic_mag'][ind]=pk_ind.PeaksMean(delta=0.02)(eda_phasic)
                        EMA_df['sc_storm_phasic_dur'][ind]= pk_ind.DurationMean(delta=0.02)(eda_phasic)
                        EMA_df['sc_storm_phasic_num'][ind]=pk_ind.PeaksNum(delta=0.02)(eda_phasic)
                        EMA_df['sc_storm_phasic_auc'][ind]=td_ind.AUC(delta=0.02)(eda_phasic)    
                    except:
                        print ( sub_ID + ' time point ' + str(start_time)+  ' and ' +  str(end_time)  + ' failed...' )
                        
            #Skin temperarture: 
            if temp_temp.size > 10:  
                #ST mean
                EMA_df['temp_mean'][ind]=temp_temp['Data'].mean()
                #ST median
                EMA_df['temp_median'][ind]=temp_temp['Data'].median()
                # ST SD
                EMA_df['temp_sd'][ind]=temp_temp['Data'].std()
                #ST slope
                line_fit=np.polyfit(range(len(temp_temp['Data'].values)),temp_temp['Data'].values,1)  #fit line through data
                EMA_df['temp_slope'][ind]=line_fit[0]
    
    
            # Accelorometer Data
            if temp_ACC['ACC_X'].size > 20:
                
                # Get absolute differences
                temp_ACC['ACC_X']=np.array(abs(temp_ACC['ACC_X'].diff(-1)))
                temp_ACC['ACC_Y']=np.array(abs(temp_ACC['ACC_Y'].diff(-1)))
                temp_ACC['ACC_Z']=np.array(abs(temp_ACC['ACC_Z'].diff(-1)))
                #Calculate the sum of squares from the difference for total ACC
                temp_ACC['ACC_tot']=np.sqrt(temp_ACC['ACC_X']**2+temp_ACC['ACC_Y']**2+temp_ACC['ACC_Z']**2)
                #Apply Temporal filter of 1 second
                N=32
                acc_delta=np.convolve(temp_ACC['ACC_tot'], np.ones((N,))/N, mode='valid')
                # Append mean displacements + SDs to df
                EMA_df['acc_x'][ind]=np.mean(temp_ACC['ACC_X'])
                EMA_df['acc_x_sd'][ind]=np.std(temp_ACC['ACC_X'])
                EMA_df['acc_y'][ind]=np.mean(temp_ACC['ACC_Y'])
                EMA_df['acc_y_sd'][ind]=np.std(temp_ACC['ACC_Y'])
                EMA_df['acc_z'][ind]=np.mean(temp_ACC['ACC_Z'])
                EMA_df['acc_z_sd'][ind]=np.std(temp_ACC['ACC_Z'])
                EMA_df['acc_delta'][ind]=np.nanmean(temp_ACC['ACC_tot'])
                EMA_df['acc_delta_sd'][ind]=np.nanstd(temp_ACC['ACC_tot'])
                
            # #Write out dataframe everytime
            if x==0:
                  feature_file="/project/3013068.02/stats/EMA/EMA_Clean_Features_10min.csv"
            else:
                  feature_file="/project/3013068.02/stats/EMA/Sleep_Clean_Features_10min.csv"
            # #Write it out every time:
            EMA_df.to_csv (feature_file, index = None, header=True)
             
