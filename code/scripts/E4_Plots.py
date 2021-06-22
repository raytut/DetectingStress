#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This script will plot an E4 session for a given subject and session
"""
#Import Libraries
import os
import readline
import numpy as np
import pandas as pd
import datetime as dt
from datetime import datetime, timedelta
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons
from matplotlib.widgets import SpanSelector

#Turnoff write warning in Pandas
pd.options.mode.chained_assignment = None  
          
#Input
sub = input ("\nParticipant number? ( e.g. 1 , 2, 3...): ")
session_type= input('\nSession (control or stress): ')
sub_nr = sub.rjust (3, '0')
print ("\nLoading...")

#Set file path, and import IBI, HR, SCR File
filepath1 = ("/project/3013068.02/data/3013068.02_BaLS_sub_" + sub_nr+ "/logs/e4/"+str(session_type) + "/merge")
os.chdir (str(filepath1))
#IBI
df_IBI=pd.read_csv("full_IBI.csv", sep='\t')
df_IBI['Time']=pd.to_datetime(df_IBI['Time'], format='%Y-%m-%d %H:%M:%S')
df_IBI=df_IBI.set_index('Time')
df_IBI=df_IBI.resample('1S').fillna('ffill', limit=600) # resample and inteprolate
#HR
df_HR= pd.read_csv("full_HR.csv", sep='\t')
df_HR['Time']=pd.to_datetime(df_HR['Time'], format='%Y-%m-%d %H:%M:%S')
df_HR=df_HR.set_index('Time')
df_HR=df_HR.resample("1S").asfreq() # Resample 1HZ
#SCR
df_SCR= pd.read_csv("full_EDA.csv", sep='\t')
df_SCR['Time']=pd.to_datetime(df_SCR['Time'], format='%Y-%m-%d %H:%M:%S')
df_SCR=df_SCR.set_index('Time')
df_SCR=df_SCR.resample("250L").asfreq()#Resample 4HZ
#Temp
df_temp= pd.read_csv("full_TEMP.csv", sep='\t')
df_temp['Time']=pd.to_datetime(df_temp['Time'], format='%Y-%m-%d %H:%M:%S')
df_temp=df_temp.set_index('Time')
df_temp=df_temp.resample('250L').asfreq() #Resample 4HZ
#ACC
df_acc= pd.read_csv("full_ACC.csv", sep='\t')
df_acc['Time']=pd.to_datetime(df_acc['Time'], format='%Y-%m-%d %H:%M:%S')
df_acc=df_acc.set_index('Time')
df_acc=df_acc.resample('31250us').asfreq() # Resample 32HZ
# Plots
Title=('E4 Data\nSubject ' + sub_nr +', '+session_type +' week')
plt.rcParams["font.family"] = 'Cambria'
plt.style.use('ggplot')
# Plot
fig, axs = plt.subplots(5, sharex=True)
fig.suptitle(Title)

# HR
axs[0].plot(df_HR.index.values, df_HR.Data, 'purple', )
axs[0].grid(b=True, which='both', axis='both', color='lightgrey', markevery=5)
axs[0].set(xlabel=' ', ylabel='Heart Rate')
axs[0].set_ylim(ymin=50, ymax=160)
# IBI
axs[1].plot(df_IBI.index.values, df_IBI.Data, 'steelblue')
axs[1].grid(b=True, which='both', axis='both', color='lightgrey', markevery=5) 
axs[1].set(xlabel=' ', ylabel='IBI (ms)')
# SCR
axs[2].plot(df_SCR.index.values, df_SCR.Data, 'gold')
axs[2].grid(b=False, which='both', axis='both', color='lightgrey', markevery=5) 
axs[2].set(xlabel=' ', ylabel='SC ($\mu$S)')
axs[2].set_ylim(ymin=-5, ymax=10)
# Temp
axs[3].plot(df_temp.index.values, df_temp.Data, 'tomato')
axs[3].grid(b=True, which='both', axis='both', color='lightgrey', markevery=5)
axs[3].set(xlabel=' ', ylabel='Temp ($^\circ$C)')
axs[3].set_ylim(ymin=15, ymax=45)
# ACC
axs[4].plot(df_acc.index.values, df_acc.ACC_X, 'blue', alpha=0.4)
axs[4].plot(df_acc.index.values, df_acc.ACC_Y, 'red', alpha=0.4)
axs[4].plot(df_acc.index.values, df_acc.ACC_Z, 'green', alpha=0.4)
axs[4].grid(b=True, which='both', axis='both', color='lightgrey', markevery=5)
axs[4].set(xlabel='Time', ylabel='ACC')
axs[4].set_ylim(ymin=-10)

# Plot
plt.show()


