Author: Rayyan Tutunji


Scripts contained here are used in the preprocessing of files derived from the Ecological Momentary Assessments (EMA) and the Empatica E4 data for the Stress Resilience and the Brain in Medical Students study (STRAIN-MD). Scripts are used in the following order:

	1. EMA_Cleaner.py: Script is used to clean data acquired during the EMA weeks in the study using CastorEDC. The script will clean up some participant ID's and the time stamps of the survey. It performs the preprocessing on both the data aquired during waking times and the sleep assessments. This allows the file to be used in step 3. 
	
	2. E4_Cleaner.py: This script loops through the subjects log files from the E4 sessions for each of the weeks (i.e., control week, and stress week). Multiple E4 sessions are recorded for each participant in each week. This script will bring these sessions together for each week into one TXT/CSV file, including the time stamps of each acquired sample. The script takes into account the sampling frequencies. The resulting file for each modality is a two-coloumn format with time stamps in one coloumn, and the recorded E4 signal at that time point. 
	
	3. E4_Features.py: This script will go through the cleaned file generated in step [1], on a subject by subject basis. It will load in the subjects E4 files from step [2]. Using the timestamps from the EMA file in a row-by-row basis, the script windows a 10 minute period before the survey for each survey, and extracts corresponding physiology features in that period of time. The resulting file can be used for statistical analysis (see stats directory). 
	
N.B.: Paths in scripts need to be adjusted according to where you run the code from! 