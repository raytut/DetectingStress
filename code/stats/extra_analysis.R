

# Calcualte our measure of interest
df_EMA.true <- EMA_Data %>% dplyr::group_by(sub_id) %>% dplyr::mutate(mean_stress_c=scale(mean_stress, center=TRUE), mean_stress_m=median(mean_stress, na.rm=T)) %>%
    dplyr::mutate(stress_bin=if_else(mean_stress>(mean_stress_m), "More", "Less" )) %>% ungroup() %>% mutate(stress_bin=as.factor(stress_bin))
tab.ema_trues <- df_EMA.true %>% dplyr::group_by(Week_Type, stress_bin) %>% dplyr::summarise(count(stress_bin)) %>% print()

# Now we estimate the LOBO Model from the dichotomziation
model.dichot_lobo <- rf.lobo(Data=df_EMA.true, SubNr = "sub_id", xvars="stress_bin", yvar="Week_Type", NoTree =5000, progress=F)
model.dichot_lobo$total