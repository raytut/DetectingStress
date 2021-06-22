##########################################################################
#   Summary function to plot bars with sd or se in them
##########################################################################

data_summary <- function(data, varname, groupnames){
    require(plyr)
    summary_func <- function(x, col){
        c(mean = mean(x[[col]], na.rm=TRUE),
          sd = sd(x[[col]], na.rm=TRUE), 
          se = (sd(x[[col]], na.rm=TRUE))/sqrt(length(x[[col]])) )
    }
    data_sum<-ddply(data, groupnames, .fun=summary_func,
                    varname)
    data_sum <- rename(data_sum, c("mean" = varname))
    return(data_sum)
}

##########################################################################
#   lmer Cohens D: Function to get cohens D from LMER Mods
##########################################################################

cal_lm_effect <- function(x, paired_test){
  require (jtools)
  require (effectsize)
  if(missing(paired_test)) {
    paired_test=TRUE
  }
summary_model <- summ(x, digits=4)
test_list <- summary_model$coeftable[,0]
test_df <- data.frame(nrow=test_list)
test_df$CohensD <- 0
for (i in (1:length(test_df$CohensD))){
  t_value <- summary_model$coeftable[i,3]
  df_val <-  summary_model$coeftable[i,4]
  cohen_d <- t_to_d(t_value, df_val)
  cohen_d <- abs(cohen_d$d)
  test_df[i,1] <- cohen_d
}
print(test_df)
}

##########################################################################
#   Utility function to print lmer results and dist.
##########################################################################

model_output <- function(model){
    print(summ(model, digits=3))
    print(check_collinearity(model))
}


##########################################################################
#   LOSO: Leave-One-Subject-Out
# Function to run LOSO analysis with our data
##########################################################################

rf.loso <- function(Data, SubNr, xvars, yvar, NoTree) {
  # Initialize List
  forest.loso <- NULL
  forest.loso$conf_mat <- NULL
  forest.loso$error_rate <- NULL
  forest.loso$predictions <- NULL
  count=0
  check=0
  
  # Combine all variables for subsetting
  Vars=c(yvar, xvars)
  
  # Initiate subject level loop
  for (i in unique(Data[[SubNr]])){
    try({
      # Make the DF without the subject
      df.train <- subset(Data, Data[[SubNr]] !=i)
      df.train <- df.train[, Vars]
      df.train <- na.omit(df.train)
      
      xvars <- Vars[Vars != yvar]
      
      # Make a random forest with the training data
      forest.train <- randomForest( as.formula(paste(yvar, "~", paste(xvars, collapse="+"))),
                                    data=df.train, 
                                    ntree=NoTree,
                                    importance = TRUE)
      
      # Make the test data frame with the subject left out
      df.test <- subset(Data, Data[[SubNr]]==i)
      df.test <- df.test[, Vars]
      df.test <- na.omit(df.test)
      
      # Make the predictions
      forest.loso$predictions[[i]] <- predict(forest.train, newdata=df.test)
      
      # Get confusion Matrix for Subject
      forest.loso$conf_mat[[i]] <- table(observed=df.test[[yvar]], predicted=forest.loso$predictions[[i]])
      
      # Calculate Error Rate
      observations <-sum( forest.loso$conf_mat[[i]])
      error1 <- forest.loso$conf_mat[[i]][1,2]
      error2 <-  forest.loso$conf_mat[[i]][2,1]
      
      forest.loso$error_rate[[i]] <- (error1 + error2)/observations
      
      # Track progress
      count=count+1
      complete=round((count/length(unique(Data[[SubNr]] )))*100)
      if (check < complete) {
        print(paste(check, "% complete", sep=""), quote=FALSE)
        check=check+10
      }
    })
  }
  print(paste("100% complete"), quote=FALSE)
  class(forest.loso) <- "RF-LOSO Model"
  return(forest.loso)
} 


##########################################################################
#   LOBO: Leave-One-Beep-Out
# Function to run LOBO random forests
##########################################################################
rf.lobo <- function(Data, SubNr, xvars, yvar, NoTree, progress) {
  # First set progress watcher 
  if(missing(progress)){
    progress=TRUE
  }
  # Initialize List
  rf.lemao.output <- NULL
  rf.lemao.output$conf_mat <- NULL
  rf.lemao.output$error_rate <- NULL
  rf.lemao.output$subject
  # Counter
  count=0
  check=0
  # Combine all variables for subsetting
  Vars=c(yvar, xvars)
  # Initiate subject level loop
  for (i in unique(Data[[SubNr]])){
    try({ 
      # Make a df for a single subject 
      df.rf <- subset(Data, Data[[SubNr]]==i)
      df.rf <- df.rf[, Vars]
      df.rf <- na.omit(df.rf)
      xvars <- Vars[Vars != yvar]
      # Loop over each beep to test the predictions
      for (j in 1:nrow(df.rf)) {
        # Subset data frames
        df.test <- df.rf[j,]
        df.train <- df.rf[-c(j),]
        # Train forest
        forest.train <- randomForest (as.formula(paste(yvar,"~", paste(xvars,collapse="+"))),
                                      data=df.train, 
                                      ntree=NoTree,
                                      importance = TRUE)
        # Make the predictions
        prediction <- (predict(forest.train, newdata=df.test)) ==  df.test[[yvar]]
        rf.lemao.output$error_rate <- c( rf.lemao.output$error_rate, prediction)
        rf.lemao.output$subject[[i]]$error <- c( rf.lemao.output$error_rate, prediction)
      } 
      # Totals
      sub_trues <- length(rf.lemao.output$subject[[i]]$error[rf.lemao.output$subject[[i]]$error=="TRUE"])
      sub_falses <- length(rf.lemao.output$subject[[i]]$error[rf.lemao.output$subject[[i]]$error=="FALSE"])
      rf.lemao.output$subject[[i]]$error_rate <- sub_falses/(sub_trues+sub_falses)*100
      rf.lemao.output$total$subject_errors[i] <- sub_falses/(sub_trues+sub_falses)*100
    }, silent=T)
    # Track progress
    count=count+1
    complete=round((count/length(unique(Data[[SubNr]] )))*100)
    if (progress == TRUE){ 
      if (check < complete) {
        print(paste(check, "% complete", sep=""), quote=FALSE)
        check=check+10
      }
    }
    # Get total error rate, and range for per-subject predictions
    # Totals
    trues <- length(rf.lemao.output$error_rate[rf.lemao.output$error_rate=="TRUE"])
    falses <- length(rf.lemao.output$error_rate[rf.lemao.output$error_rate=="FALSE"])
    rf.lemao.output$total$error_rate <- falses/(trues+falses)*100
    
  } 
  if (progress==TRUE){ 
    print("100% Complete", quote=FALSE)
  } 
  class(rf.lemao.output) <- "RF-LOBO Model"
  return(rf.lemao.output)}


##########################################################################
#   LOBO Bootstrap
#
#   Function that does permutations on the data before running
#   the LOBO model. Compiles prediction errors ti a number of iterations. 
#   I was unable to run in in parallel so this function would take a very 
#   long time. Check the notebook for the work around. 
#
##########################################################################

rf.BootstrapError <- function(Data, Shuffle, Iterations, SubjectId, xvar, yvar, Trees){
    # Set up empty lists
    rf.shuffled <- list()
    rf.output <- NULL
    rf.output$BootstrapError <- list()
    check <- 0
    require(randomForest)
    # Start
    print (paste("Running", Iterations, "iterations. Will let you know when I'm done..."), quote=F)
    # Loop over reshuffled dataFrame with parrallel processing
    for( i in (1:Iterations)){
        # Specify data frame and shuffle coloumns
        Data_shuffle <- Data
        Data_shuffle[[Shuffle]] <- sample(Data_shuffle[[Shuffle]], replace=T)
        # Run LOBO function on shuffled Data
        forest.lobo.shuffle <- rf.lobo(Data=Data_shuffle,
                                       SubNr=SubjectId,
                                       xvars=xvar,
                                       yvar=yvar,
                                       NoTree=Trees, 
                                       progress=F)
        # Record the prediction rates
        forest.shuffle.probability <- forest.lobo.shuffle$tota$subject_error
        forest.shuffle.probability <- as.data.frame(forest.shuffle.probability)
        rf.output$BootstrapError[i] <-  list(forest.shuffle.probability)
    } 
    
    # Initiate first dataframe
    try({
        rf.output$DataFrame <-  rf.output$BootstrapError[[1]]
        rf.output$DataFrame[["id"]] <-  rownames(rf.output$BootstrapError[[1]])
        # Merge remaining dataframes into one
        for (dataframes in 2:length(rf.output$BootstrapError)){
            forest.tempdf <- rf.output$BootstrapError[[dataframes]]
            forest.tempdf$id <-  rownames(forest.tempdf)
            rf.output$DataFrame  <- merge(forest.tempdf, rf.output$DataFrame , by="id")
        }
        rf.output$DataFrame$TotalEstimatedError <- rowMeans(
            rf.output$DataFrame[, -which(names(rf.output$DataFrame) %in% c("id"))])
    })
    print("Done! Are your results nice?", quote=F)
    return(rf.output)
}



##########################################################################
#   Test a randomforest LOBO or LOSO against Bootstrap Error
#
#   Function to test the LOBO or LOSO against the bootstrap permutation 
#   from above.
#
##########################################################################

rf.null_test <- function(lobo_input, bootstrap_error, model_type, method){
        
    # If type if missing, assume LOBO
    if(missing(model_type)){
        model_type="LOBO"}
    # If method not specified, test against null distribution
    if(missing(method)){
        method="norm" }

    # Load Required library + Initiate output variables
    require(poolr)
    null_test=list()
    null_test$p_val=array()
    
    # Begin loop
    for (i in 1:length( bootstrap_error[,1])){
        # Select subject + bootstrap errors
        sub=( bootstrap_error[i,1])
        sub_bootstrap <-( bootstrap_error[i,3:10002])
        # Turn to a coloumn
        sub_bootstrap <- transpose( sub_bootstrap)
        # Get mean and sd
        sub_bootstrap_mean <- mean( sub_bootstrap$V1)
        sub_bootstrap_sd <- sd( sub_bootstrap$V1)
        # Do a Z transformation of toal scores
        sub_bootstrap_z <-  scale(sub_bootstrap$V1, center = TRUE, scale = TRUE)
     
        # If LOBO and P value calcualted from normal distribution
        if (model_type=="LOBO"){
            if (method=="norm"){
                # Get mean error
                sub_mean_error<- (lobo_input$total$subject_errors[i])
                # Z-Transfomr and divide by sd for Z-Score
                sub_mean_error_z<- (lobo_input$total$subject_errors[i]) - sub_bootstrap_mean
                sub_z_score <- sub_mean_error_z/sub_bootstrap_sd
                # Append to list
                null_test$p_val[i]<-pnorm(sub_z_score)  
                }}
        # If LOBO + P value from actual distribution of error
        if (model_type=="LOBO"){
            if (method=="actual"){
                # Get mean error + Calculate proprotion less than
                sub_mean_error<- (lobo_input$total$subject_errors[i]) 
                null_test$p_val[i]<-(sum((sub_bootstrap$V1 < sub_mean_error)))/(length(sub_bootstrap$V1))  
                }}
        # If LOSO + Normal distribution
        if (model_type=="LOSO"){{
            if (method=="norm")
                # Get mean error
                sub_mean_error<- (as.numeric(lobo_input$error_rate[i])*100)
                # Z-Transfomr and divide by sd for Z-Score
                sub_mean_error_z<- (as.numeric(lobo_input$error_rate[i])*100) - sub_bootstrap_mean
                sub_z_score <- sub_mean_error_z/sub_bootstrap_sd
                # Append to list
                null_test$p_val[i]<-pnorm(sub_z_score)   }}
        
        # If LOSO + Actual
        if (model_type=="LOSO"){{
            if (method=="actual")
                # Get mean error of model
                sub_mean_error <- (as.numeric(lobo_input$error_rate[i])*100)
                # compare to null
                null_test$p_val[i]<-(sum((sub_bootstrap$V1 < sub_mean_error)))/(length(sub_bootstrap$V1))   }}
   }
    
    # Remove the nans to combile the p-values 
    if (model_type=="LOBO"){
        p_val <- null_test$p_val[!is.na(null_test$p_val)]
        p_val[p_val < 0.00000000001] = (1/10000)
        null_test$combined <- stouffer(p_val)
        return(null_test)
        print(null_test$combined)
    }
    
    if (model_type=="LOSO"){
        p_val <- null_test$p_val[!is.na(null_test$p_val)]
        p_val[p_val < 0.00000000001] = (1/10000)
        null_test$combined <- stouffer(p_val)
        return(null_test)
        print(null_test$combined)
    }
}



##########################################################################
#   Temporal lagging function
#
#   Utility function to temporally lag a variable, taking into acount
#   each day.
#
##########################################################################

lag_var <- function(x, id, obs, day, data, lag) {
    
    # Code characters for later use
    id_mer <- as.character(id)
    obs_mer <- as.character(obs)
    x_lag <- (paste(as.character(x),"lag", sep="."))
  
    # get 'x', 'id', 'obs', 'day', and 'time' arguments (will be NULL when unspecified)
    x    <- data[[x]]
    id   <- data[[id]]
    obs  <- data[[obs]]
    day  <- data[[day]]
    ind <- as.numeric(rownames(data))
    
    # Lagging Section
    #########################################################################
    # Intialize Data frames
    dat <- data.frame(ind=ind,x=x, id=id, day=day, obs=obs)
    sub_append <- data.frame()
    # Lag at subject level
    for (subjects in (unique(dat$id))){
        sub <- subset(dat, id==subjects)
        # Now we lag each day
        for (days in 1:length(unique(day))){
            # Arrange by obs and lag
            sub_day <- subset(sub, day==days)
            sub_day <- sub_day %>% arrange(obs) 
            sub_day[[x_lag]] <- Lag(sub_day$x, lag)
            sub_append <- rbind(sub_append, sub_day)
        }
    }
    # Reorder rows so that they much original dataframe
    lag_df <- data.frame(ind=sub_append$ind, lag=sub_append[[x_lag]])
    rownames(lag_df) <- (lag_df$ind)
    lag_vec <- lag_df$lag[order(lag_df$ind)]
    #########################################################################
    return(lag_vec)
}




