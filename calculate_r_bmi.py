import pandas as pd
import numpy as np
from scipy.interpolate import interp1d


def calculate_r_bmi(df, sex_column, bmi_column, age_column, age_in_months = True):
    #import reference table 
    url = 'https://raw.githubusercontent.com/molne1/Comparing-child-BMI/refs/heads/main/assets/2024-05-14_RBMI_SD1SD2.csv'

    rbmi_ref = pd.read_csv(url)
    rbmi_boy_ref = rbmi_ref[rbmi_ref['sex']==1]
    rbmi_girl_ref = rbmi_ref[rbmi_ref['sex']==2]

    SD_columns = rbmi_ref.columns[rbmi_ref.columns.str.startswith('SD')]
    SD_at_18_boy = rbmi_boy_ref.loc[rbmi_boy_ref['age_months']==216,SD_columns]
    SD_at_18_girl = rbmi_girl_ref.loc[rbmi_girl_ref['age_months']==216, SD_columns]

    rbmi = []
    rows_with_issues = []

    # make sure they all have the necessary columns
    for index, row in df.iterrows():
            try:
                sex = row[sex_column]
            except:
                print('Missing/Unable to read column for sex')
                rbmi.append(np.nan)
                rows_with_issues.append(index)
                break
            try:
                bmi = row[bmi_column] 
            except:
                print('Missing/Unable to read column for BMI')
                rbmi.append(np.nan)
                rows_with_issues.append(index)
                break
            try:
                if age_in_months:
                    age = int(row[age_column])
                else:
                     age = int(round(row[age_column]/12))
            except:
                print('Missing/Unable to read column for BMI')
                rbmi.append(np.nan)
                rows_with_issues.append(index)
                continue
            if age >216:
                print('Individual is above 18 yrs of age')
                rbmi.append(np.nan)
                rows_with_issues.append(index)    
                continue 

            try: # get the reference for each sex
                if sex == 1:
                    reference = rbmi_boy_ref
                    ref_18 = SD_at_18_boy
                elif sex ==2: #girl 
                    reference = rbmi_girl_ref
                    ref_18 = SD_at_18_girl
                else:
                    rbmi.append(np.nan)
                    rows_with_issues.append(index)
                    continue

            except:
                rbmi.append(np.nan)
                rows_with_issues.append(index)
                continue

            try:
                sd_columns = reference.columns[reference.columns.str.startswith('SD')]
                sd_columns_numbers = [*range(-4,40+1,1)]

                # find child's zscore at their age
                matching_age_bmi_values = reference.loc[reference["age_months"] == age, sd_columns].values.flatten().tolist()
                x_data = sd_columns_numbers
                y_data = matching_age_bmi_values
                y_f = interp1d(y_data, x_data,'linear')
                interp_zscore_value = (y_f(bmi))
                zscore_at_age = round(float(interp_zscore_value),2)
                
                #find bmi at 18 for zscore 
                x_data = ref_18.values.flatten().tolist()
                y_data = sd_columns_numbers
                y_f = interp1d(y_data, x_data,'linear')
                interp_rbmi_value = (y_f(zscore_at_age))
                rbmi_value = round(float(interp_rbmi_value),1)
                rbmi.append(rbmi_value)
            
            except:
                rbmi.append(np.nan)
                rows_with_issues.append(index)
                continue

    df['R-BMI'] = rbmi
    return df
df_test = pd.DataFrame( {'age_months':[100,5], 'sex':[1,2], 'bmi':[90,38]})

calculate_r_bmi(df_test, 'sex', 'bmi', 'age_months', age_in_months = True)
print('python\n', df_test)
