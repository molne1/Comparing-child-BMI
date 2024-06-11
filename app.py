import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import Dash, dcc, html, Input, Output, callback
import flask
import dash_bootstrap_components as dbc
import re
from scipy.interpolate import interp1d


#---------------------------------------------------
SBMI = pd.read_csv('assets/2024-05-14_SBMI_SD1SD2.csv', usecols=['sex', 'age_months', '25', '30','35', '40', '45', '50', '55', '60' ] )
WHO = pd.read_csv('assets/2024-05-14_WHO_original_clean.csv', usecols= [ 'sex', 'age_months','SD0','SD1', 'SD2','SD3', 'SD4', 'SD5', 'SD6', 'SD7', 'SD8'])
IOTF = pd.read_csv('assets/2024_05_14_IOTF.csv', usecols= ['sex', 'age_months', 'BMI_25', 'BMI_30','BMI_35', 'BMI_40', 'BMI_45', 'BMI_50', 'BMI_55', 'BMI_60',])
CDC_pct = pd.read_csv('assets/2024-05-08_CDC_2022_clean.csv', usecols=['sex', 'age_months', 'P85','P95', 'pct120ofP95','pct140ofP95', 'pct150ofP95','pct160ofP95', 'pct180ofP95', 'pct190ofP95', 'pct200ofP95'])
CDC = pd.read_csv('assets/2024-05-08_CDC_2022_clean.csv', usecols=['sex', 'age_months',  'SD0', 'SD0.5', 
                                                                   'SD1', 'SD1.5', 'SD2', 'SD2.5', 'SD3', 'SD3.5', 'SD4',
                                                                   'SD4.5', 'SD5'] )


SBMI.name = 'SBMI'
WHO.name = 'WHO'
IOTF.name = 'IOTF'
CDC_pct.name = 'CDC_pct'
CDC.name = 'CDC'


boys = {}
girls = {}
ALL_references = [SBMI, WHO,IOTF, CDC_pct, CDC]
for reference in ALL_references:
    boys[f'{reference.name}'] = reference[reference['sex'] == 1]
    girls[f'{reference.name}'] = reference[reference['sex'] == 2]
    
#-----------------------------------------
# SBMI functions 
SBMI_ref = pd.read_csv('assets/2024-06-04_sbmi_expanded_SD_SD1-SD2.csv')

def LMS(bmi, list_with_LMS):
    L = list_with_LMS["L"].item()         
    M = list_with_LMS["M"].item()
    S = list_with_LMS["S"].item()
    
    z_score = (((bmi/ M) ** L )- 1) / (L * S)
    return z_score

def numeric_values_from_sd_columns(list_columns):
    list_sd = []
    for name in list_columns:
        cleaned_name = re.sub("\D", "", name)
        if "neg" in name:
            cleaned_name = "-" + cleaned_name
        list_sd.append(float(cleaned_name))
    return list_sd

def sbmi_cutoff_18(sd_columns, zscore, sex):
    reference_18 = SBMI_ref[SBMI_ref['age_months']== 216]
    if sex == 1:
        reference_row = reference_18[reference_18['sex']==1]
    else:
        reference_row =  reference_18[reference_18['sex']==2]

    x_data  = numeric_values_from_sd_columns(sd_columns)
    y_data = reference_row[sd_columns].values[0]
    y_f = interp1d(x_data, y_data, 'linear')
    sbmi = y_f(zscore)
    return sbmi   

def sbmi_cutoff_below_3SD(zscore, sex):
    reference_18 = SBMI_ref[SBMI_ref['age_months']== 216]

    if sex == 1:
        reference_row = reference_18[reference_18['sex']==1]
    else:
        reference_row =  reference_18[reference_18['sex']==2]

    L= reference_row['L']
    M = reference_row['M']
    S = reference_row['S']
    
    BMI = M*(1+L*S*zscore)**(1/L)
    return BMI     
     
def sbmi_zscore(age, sex, bmi):
    sd_columns =  [col for col in SBMI_ref if col.startswith('SD')]

    if int(age) <= int(216):
            if sex == 1:
                reference = SBMI_ref[SBMI_ref['sex']==1]
            else:
                reference =  SBMI_ref[SBMI_ref['sex']==2]
            
            # find zscore for bmi
            reference_row = reference[reference['age_months']== age]
            zscore = LMS(bmi, reference_row)
                
            if zscore <=3:
                sbmi_return = sbmi_cutoff_below_3SD(zscore, sex)
                sbmi_string = "s-BMI: " +str(np.round(sbmi_return, 1))

            else:
                y_data  = numeric_values_from_sd_columns(sd_columns)
                x_data = reference_row[sd_columns].values[0]
                y_f = interp1d(x_data, y_data, 'linear')
                sbmi_zscore = y_f(bmi)
                # take zscore and give it the BMI value at 18 years old. 
                sbmi_return = sbmi_cutoff_18(sd_columns, sbmi_zscore, sex)
                sbmi_string = "s-BMI: " +str(np.round(sbmi_return, 1))
                
    return (sbmi_return,sbmi_string)
#-----------------------------------------
server = flask.Flask(__name__) 

#-----------------------------------------

SBMI_color = 'goldenrod'
WHO_color = '#009CDE'
IOTF_color = 'green'
CDC_color = 'red'
CDCpct_color = 'maroon'


ylabel = 'Body Mass Index (kg/m^2)'
xlabel = 'Age (Years)'
fs_label = 18

#-----------------------------------
app = dash.Dash(__name__,
                title="Child BMI references for children with overweight or obesity.",
                suppress_callback_exceptions=True, server=server, 
                external_stylesheets=[dbc.themes.SANDSTONE])

app.layout = dbc.Container([
    dbc.Row([html.H1("   ")],className=" mb-5"),
    dbc.Row([html.H1("Reference BMI comparator")],className="text-center my-4 p-3 bg-light text-black rounded"),
    dbc.Row([html.H2("for Children with Overweight or Obesity")],className=" text-center mb-5"),

    dbc.Row([dbc.Col([
                html.H5([dbc.Badge("About",color = 'light', className= "p-2")]),
                html.P("This app was built with the purpose of visually comparing different child body mass index (BMI) references for children with overweight or obesity. "),
                html.P("The app relies on open data from a set of publications and official websites. More information is presented beneath the graph. ")
                ], className = "p-3" ),
             dbc.Col([html.H5([dbc.Badge("How-to",color = 'light', className= "p-2")]), 
                        html.P("Choose sex by the switch on the left of the graph. Under the graph you find references, you can choose what curves. Select sliders as you wish."),
                        html.P("Optional, if you would like to display a child's data point on the graph you can add age and BMI)"),
                        html.P("The graph is interactive so you can also zoom in and out get exact values by hovering above a specific line. If you would like an A4 format, use format switch.") ], 
                        className = 'p-3')
            ]),

    dbc.Row([dbc.Col(dcc.Graph(id='graph-container'), width = 12,   md = 9),
             dbc.Col([
                dbc.Row([html.P('Options', className= 'bg-light')  , 
                         dbc.Col(html.H6("sex")), 
                         dbc.Col(
                            dbc.Checklist(
                            className="btn-group",
                                id="sex",
                                    # inputClassName="btn-check",
                                    # labelClassName="btn btn-primary",
                                    # labelCheckedClassName="active",
                                    options=[{"label": "", "value": 2}]
                                            ,
                                    value = [],
                                    switch=True, 
                                                
                            ))
                    ]), 
                dbc.Row([   
                         dbc.Col(html.H6("format")), 
                         dbc.Col(
                            dbc.Checklist(
                            className="btn-group",
                                id="layout",
                                    # inputClassName="btn-check",
                                    # labelClassName="btn btn-primary",
                                    # labelCheckedClassName="active",
                                    options=[{"label": "", "value": True}]
                                            ,
                                    value = [],
                                    switch=True, 
                                                
                            )),
                    ]), 
                
                dbc.Row([
                        html.P("Child", className= 'bg-light mt-3'), 
                        dbc.Label("age"),
                        dbc.Input(id = 'age_years', placeholder='years', type='number',min=0, max=20, className=" bc-light"),
                        dbc.Input(id = 'age_months', placeholder='months', type='number' ,min=0, max=12,),
                        html.Label("BMI", className="mt-1 "),
                        dbc.Input(id = 'BMI', placeholder='kg/m^2', type='number', value='', min=14.7, max=70,step='0.1')
                        ],
                       
                    ),
                dbc.Row(
                    dbc.Card(id = 'sbmi', className="mb-3 mt-4  p-2", color="primary", inverse=True)
                        )
                ],
                    className = "mt-3 ",width = 12,  md = 3, 
                )],
            
        className ="border"
    ),

dbc.Row([
        dbc.Col([ html.H6("s-BMI", style={"color": SBMI_color}),
                dbc.Checklist(

                    id='checkbox-container_SBMI',
                    options=[
                        {'label': 'BMI25 - overweight', 'value': '25'},
                        {'label': 'BMI30 - obesity', 'value': '30'},
                        {'label': 'BMI35 - severe obesity', 'value': '35'},
                        {'label': 'BMI40', 'value': '40'},
                        {'label': 'BMI45', 'value': '45'},
                        {'label': 'BMI50', 'value': '50'},
                        {'label': 'BMI55', 'value': '55'},
                        {'label': 'BMI60', 'value': '60'}
                    ],
                    value = ["25"],
                    switch=True
                  
                )]), 
    
        dbc.Col([
                html.H6("World Health Organisation", style={"color": WHO_color}),
                dbc.Checklist(

                    id='checkbox-container_WHO',
                    options=[
                        {'label': 'SD0', 'value': 'SD0'},
                        {'label': 'SD1 - overweight', 'value': 'SD1'},
                        {'label': 'SD2 - obesity', 'value': 'SD2'},
                        {'label': 'SD3', 'value': 'SD3'},
                        {'label': 'SD4', 'value': 'SD4'},
                        {'label': 'SD5', 'value': 'SD5'},
                        {'label': 'SD6', 'value': 'SD6'},
                        {'label': 'SD7', 'value': 'SD7'},
                        {'label': 'SD8', 'value': 'SD8'},
                    ],
                    value =['SD1'],
                switch=True
                  
                )
            ], 
        ),
        dbc.Col([
                html.H6("International Obesity Task Force", style={"color": IOTF_color}), 
                dbc.Checklist(
                    id='checkbox-container_IOTF',
                    options=[
                        {'label': 'BMI25 - overweight', 'value': 'BMI_25'},
                        {'label': 'BMI30 - obesity', 'value': 'BMI_30'},
                        {'label': 'BMI35 - severe obesity', 'value': 'BMI_35'},
                        {'label': 'BMI40', 'value': 'BMI_40'},
                        {'label': 'BMI45', 'value': 'BMI_45'},
                        {'label': 'BMI50', 'value': 'BMI_50'},
                        {'label': 'BMI55', 'value': 'BMI_55'},
                        {'label': 'BMI60', 'value': 'BMI_60'},
                    ],
                    value = ["BMI_25"],
                    switch=True

                 
                )
            ],
           
        ),
        dbc.Col([
                html.H6("CDC (Extended SD)",style={"color": CDC_color}),
                dbc.Checklist(
                    id='checkbox-container_CDC',
                    options=[
                        {'label': 'SD0', 'value': 'SD0'},
                        {'label': 'SD1', 'value': 'SD1'},
                        {'label': 'SD2', 'value': 'SD2'},
                        {'label': 'SD3', 'value': 'SD3'},
                        {'label': 'SD4', 'value': 'SD4'},
                        {'label': 'SD5', 'value': 'SD5'},
         
                    ], value =['SD1'],
                    switch=True
                  
                )
            ],  className =""
        ),
        dbc.Col([
                html.H6("% above 95 percentile (CDC) ",style={"color": CDCpct_color}),
                dbc.Checklist(
                    id='checkbox-container_CDC95P',
                    options=[
                        {'label': '85 percentile - overweight', 'value': 'P85'},
                        {'label': '95 percentile - obesity ', 'value': 'P95'},
                        {'label': '120% - severe obesity ', 'value': 'pct120ofP95'},
                        {'label': '140%', 'value': 'pct140ofP95'},
                        {'label': '150%', 'value': 'pct150ofP95'},
                        {'label': '160%', 'value': 'pct160ofP95'},
                        {'label': '180%', 'value': 'pct180ofP95'},
                        {'label': '200%', 'value': 'pct200ofP95'}
                    ],
                    value =['P85'],
                    switch=True
                    
                )
            ]
        ),
    ]),  
dbc.Row([
    dbc.Accordion([
            dbc.AccordionItem(
                [ html.B("Reference:"),
                 html.P("The reference population for s-BMI is the WHO population, as such s-BMI shares SD0, SD1, SD2, SD3 with the WHO reference. However, to add SD levels above 3 SD the difference between 1st and 2nd SD was added."),
                 html.P(""),
                 html.B("Cut-offs"),
                 html.P("Overweight: s-BMI >25 "),
                 html.P("Obesity: s-BMI >30 "),
                 html.P("Severe Obesity: s-BMI >35 "),
                 html.P(""),
                 html.B("Estimate child's BMI"),
                 html.P("To estimate an individual child's BMI, age is first determined as months. LMS zscore is estimated.  For each child their BMI is compared to SD levels at the corresponding age, by linear interpolation. This results in a child’s z-score, which is then compared to an18 years old and by linear interpolation the corresponding BMI is estimated. This is similar to the method IOTF uses with the exception that s-BMI uses linear interpolation."),
                 html.P(""),
                 html.B("Links"),
                 html.P(""),
                 html.A("Go to GitHub for processed table", href="https://raw.githubusercontent.com/molne1/Comparing-child-BMI/main/assets/2024-05-14_SBMI_SD1SD2.csv ", target="_blank"),
                ],
                title="Standardized BMI to the age of 18 years (s-BMI)",
            ),
            dbc.AccordionItem(
                [html.B("Reference"),
                html.P("The reference values for 0-5 years and 5-19 years were retrieved from the WHO webbpage. For 0-5 years, expanded tables which utilised age in days were converted to months using the WHO recommended length of a month ( 1 month = 30.4375 days), found in the instructions "),
                html.P("Both tables were combined for girls and boys to achieve a continuous age span (0-228 months). The 4th SD was created by the WHO by taking the difference between the 2nd and 3rd SD and added to 3 SD.  To create additional levels, the same difference was added for each increase in SD."),
                html.P("Name of file retrieved 0-5 years (2023-06-28): bfa-girls-zscore-expanded-tables.xlsx &  bfa-boys-zscore-expanded-tables.xlsx (columns: Day, L, M, S, SD4neg, SD3neg, SD2neg, SD1neg, SD0, SD1, SD2, SD3, SD4)"),
                html.P("Name of file retrieved 5-19 years (2023-06-28): bmi-girls-z-who-2007-exp.xlsx & bmi-boys-z-who-2007-exp.xlsx (columns: Day, L, M, S, SD4neg, SD3neg, SD2neg, SD1neg, SD0, SD1, SD2, SD3, SD4)"),
                html.P(""),
                html.B("Cut-offs"),
                html.P("Overweight:  BMI > 1 SD (only if child is older than 5 years) "),
                html.P("Obesity: BMI > 2 SD (only if child is older than 5 years)  "),
                html.P("Severe Obesity: missing"),
                html.P(""),
                html.B("Links"),
                html.P(""),
                html.A("Go to reference WHO 0-5 years ", href="https://www.who.int/toolkits/child-growth-standards/standards/body-mass-index-for-age-bmi-for-age", target="_blank"),
                html.P(""),
                html.A("Go to reference WHO 5-19 years ", href="https://www.who.int/tools/growth-reference-data-for-5to19-years/indicators/bmi-for-age", target="_blank"),
                html.P(""),
                html.A("Go to GitHub for processed table", href="https://raw.githubusercontent.com/molne1/Comparing-child-BMI/main/assets/2024-05-14_WHO_original_clean.csv", target="_blank"),
                
                ],

                title="World Health Organisation(WHO)",),
            dbc.AccordionItem(
                [html.B("Reference"), 
                 html.P("Reference tables were retrieved from the article Extended international (IOTF) body mass index cut-offs for thinness, overweight and obesity (Cole & Lobstein, 2012, doi:10.1111/j.2047-6310.2012.00064.x) in Supplement Table S1 & S2."),
                 html.P(" Name of file retrieved (2023-06-28): ijpo64-sup-0001-si.doc - Table S1. BMI LMS coefficients corresponding to the international (IOTF) cut-offs (Columns:  Age (Years), L, M, S (Boys), L, M, S (Girls)), & ijpo64-sup-0002-si.doc - Table S2. Revised international IOTF BMI cut-offs (kg/m^2) using the pooled LMS curves. (Columns: Age (Years), BMI 16*, BMI 17*, BMI 18.5*, BMI 25*, BMI 30*, BMI 35* (Boys), BMI 16*, BMI 17*, BMI 18.5*, BMI 25*, BMI 30*, BMI 35* (girls))"),
                 html.P("The tables were converted from Word documents to Excel files. IOTF z-scores (“BMI cut-offs”) were calculated for a range of BMI values with LMS values for 18-year olds, using LMS calculation: Z = (((BMI/M) ^L)-1)/ (L*S) "),
                 html.B("Cut-offs"),
                 html.P("Overweight:  BMI >25  "),
                 html.P("Obesity:  BMI>30  "),
                 html.P("Severe Obesity: BMI >35 "),
                 html.P(""),
                 html.B("Links"),
                 html.P(""),
                 html.A("Go to Article", href="https://onlinelibrary.wiley.com/doi/10.1111/j.2047-6310.2012.00064.x", target="_blank"),
                 html.P(""),
                 html.A("Go to GitHub for processed table", href="https://github.com/molne1/Comparing-child-BMI/blob/main/assets/2024_05_14_IOTF.csv", target="_blank"),
                 html.P(" "),
                ],
                
                title="International Obesity Task Force (IOTF)"),
            
            dbc.AccordionItem(
                [html.B("Reference"),
                 html.P("The reference values for 2-20 years from CDC was retrieved from the CDC website. The extended table with new values above the 95th percentile (z = 1.645) released in 2022 are used, below the 95th percentile are the original CDC 2000 values. "),
                 html.P("Name of file retrieved (2024-05-08): bmi-age-2022.csv (Columns: sex, agemos, L, M, S, sigma, P3, P5, P10, P25, P50, P75, P85, P90, P95, P98, P99, P99_9, P99_99, pct120ofP95, Z2neg, Z1_5neg, Z1neg, Z0_5neg, Z0, Z0_5, Z1, Z1_5, Z2, Z2_5, Z3, Z3_5, Z4, Z4_5, Z5"),
                 html.P("Their age values are expressed as 24, 24.5, 25.5, ..., 390.5, 240, 240.5. The half months represent the whole of the month but does not include the next month, ex. 25.5 is for whole month of 25 but does not include 26. The coding for sex is 1=male; 2=female"),
                 html.P("Columns with “Z” was changed to “SD”, and separated from percentile curves. Besides the existing 120 percent of 95th percentile, additional percent of 95th percentile were added (130, 140, 150, 160, 170, 180, 200)"),
                 html.P(" "),
                 html.B("Cut-offs"),
                 html.P("Overweight: BMI >85th percentile (~1st SD)"),
                 html.P("Obesity: BMI >95th percentile (~1.5 SD)"),
                 html.P("Severe Obesity: BMI >120% of 95th percentile or above 35 kg/m^2"),
                 html.P(""),
                 html.B("Links"),
                 html.P(""),
                 html.A("Go to CDC webpage", href="https://www.cdc.gov/growthcharts/extended-bmi-data-files.html", target="_blank"),
                 html.P(""),
                 html.A("Go to GitHub for processed table", href="https://raw.githubusercontent.com/molne1/Comparing-child-BMI/main/assets/2024-05-08_CDC_2022_clean.csv", target="_blank"),
                ],
                title="Center for Disease Control and Prevention(CDC)", className= 'bc-ligth' ), 
        ],start_collapsed=True )],
    className ="mt-5 "
), 
dbc.Row(
    [html.P("This app was created by Maja Engsner, the code is openly available at GitHub, and together with the graph is free to use under creative commons licence (CC). No funding was received for creating this app. Find links below to Maja Engsner's profile on Uppsala University and LinkedIn as well as the GitHub repository", className= "mt-4"),
     html.Span
     ([
        dbc.Badge(
            "Uppsala University",
            href="https://www.uu.se/kontakt-och-organisation/personal?query=N20-1653",
            color="danger",
            className="text-decoration-none p-2 me-2",
        ),
        dbc.Badge(
            "LinkedIn",
            href="https://www.linkedin.com/in/maja-engsner-b4b194141/",
            color="primary",
            className="text-decoration-none p-2 mx-2",
        ),
        dbc.Badge(
            "GitHub repository",
            href="https://github.com/molne1/Comparing-child-BMI",
            color="secondary",
            className="text-decoration-none p-2 mx-2",
        )],

    )])
])

@app.callback(
    Output(component_id='graph-container', component_property='figure'),
    Output(component_id='sbmi', component_property='children'),

    [Input(component_id = 'sex', component_property = 'value'),
     Input(component_id = 'layout', component_property = 'value'),
     Input(component_id = 'age_years', component_property = 'value'),
     Input(component_id = 'age_months', component_property = 'value'),
     Input(component_id = 'BMI', component_property = 'value'),
    
     Input(component_id =  'checkbox-container_SBMI', component_property='value'), 
    Input(component_id = 'checkbox-container_WHO', component_property='value'), 
    Input(component_id = 'checkbox-container_IOTF', component_property = 'value'),
    Input(component_id = 'checkbox-container_CDC', component_property='value'), 
    Input(component_id = 'checkbox-container_CDC95P', component_property = 'value'),
    ]
)
def update_graph(sex, layout, age_years, age_months, bmi, SBMI, WHO, IOTF, CDC, CDC95P):
    if sex == []:
        SBMI_axes = girls['SBMI']  
        WHO_axes = girls['WHO']
        IOTF_axes = girls['IOTF']
        CDC_axes = girls['CDC']
        CDC95P_axes = girls['CDC_pct']  
        text = 'girl'
        sex_nr = 2

    if sex == [2]:
        SBMI_axes = boys['SBMI']  
        WHO_axes = boys['WHO']
        IOTF_axes = boys['IOTF']
        CDC_axes = boys['CDC']
        CDC95P_axes = boys['CDC_pct']
        text = 'boy'
        sex_nr = 1

    fig = go.Figure()
#SBMI
    for level in reversed(SBMI):
        fig.add_trace(go.Scatter(x=SBMI_axes['age_months'], y=SBMI_axes[level], mode='lines', name=level,
                                 line=dict(color=SBMI_color), showlegend=False))
        
        label = f'SBMI-{level}'
        placement_y = 98
        max_value_x = SBMI_axes[(SBMI_axes['age_months'] == placement_y)][level].iloc[0]
        fig.add_annotation(x=placement_y, y=max_value_x, text=label, showarrow=False, font=dict(size=8), bgcolor="white",
                           bordercolor = SBMI_color, borderwidth=1)
#WHO
    for level in reversed(WHO):
        fig.add_trace(go.Scatter(x=WHO_axes['age_months'], y=WHO_axes[level], mode='lines', name=level,
                                 line=dict(color=WHO_color), showlegend=False))
        
        label = f'WHO-{level}'
        placement_y = 119
        max_value_x = WHO_axes[(WHO_axes['age_months'] == placement_y)][level].iloc[0]
        fig.add_annotation(x=placement_y, y=max_value_x, text=label, showarrow=False, font=dict(size=8), bgcolor="white",
                           bordercolor = WHO_color, borderwidth=1)
#IOTF       
    for level in reversed(IOTF):
        fig.add_trace(go.Scatter(x=IOTF_axes['age_months'], y=IOTF_axes[level], mode='lines', name=level,
                                     line=dict(color=IOTF_color), showlegend=False))

        label = f'IOTF-{level}'
        placement_y = 192
        max_value_x = IOTF_axes[(IOTF_axes['age_months'] == placement_y)][level].iloc[0]
        fig.add_annotation(x=placement_y, y=max_value_x, text=label, showarrow=False, font=dict(size=8), bgcolor="white",
                       bordercolor = IOTF_color, borderwidth=1)
#CDC
    for level in reversed(CDC):
        fig.add_trace(go.Scatter(x=CDC_axes['age_months'], y=CDC_axes[level], mode='lines', name=level,
                                 line=dict(color=CDC_color),showlegend=False))
        
        label = f'CDC-{level}'
        placement_y =  144.5
        max_value_x = CDC_axes[(CDC_axes['age_months'] == placement_y)][level].iloc[0]
        fig.add_annotation(x=placement_y, y=max_value_x, text=label, showarrow=False, font=dict(size=8), bgcolor="white",
                            bordercolor=CDC_color, borderwidth=1)
#CDCP95      
    for level in reversed(CDC95P):
        fig.add_trace(go.Scatter(x=CDC95P_axes['age_months'], y=CDC95P_axes[level], mode='lines', name=level,
                                 line=dict(color=CDCpct_color),showlegend=False))
        label = f'CDC-{level}'
        placement_y =  168.5
        max_value_x = CDC95P_axes[(CDC95P_axes['age_months'] == placement_y)][level].iloc[0]
        fig.add_annotation(x=placement_y, y=max_value_x, text=label, showarrow=False, font=dict(size=8), bgcolor="white",
                           bordercolor=CDCpct_color, borderwidth=1)
        
# GIRL/BOY in graph        
    fig.add_annotation( x=1,    y=1,    xref='paper',    yref='paper',    text=text , showarrow=False,     font=dict(size=24, color = 'darkgrey' ),    align='left',    bordercolor='white',    borderwidth=1,
    borderpad=4,    bgcolor='white',    opacity=0.8,    xanchor='right',    yanchor='bottom', xshift=0, yshift = 0)

    # fig.update_yaxes(range=[10, 65])
    fig.update_xaxes(range=[0, 240])

    x = range(0, 241)
    x_ticks = [month for i, month in enumerate(x) if month % 12 == 0 and i % 2 == 0]  
    x_labels = [str(i) for i in range(len(x_ticks))]
    
# A4 LAYOUT 
    a4_aspect_ratio = 1 / 1.414
    size = 380
    if layout == []:
         
        
        fig.update_layout(legend=dict(x=0),
                autosize=True, 
                plot_bgcolor='white',
                xaxis=dict(
                    tickmode='array',
                    tickvals=x_ticks[::2],
                    ticktext=x_labels[::2],gridcolor='lightgrey'
                ),
                yaxis=dict(title=ylabel, titlefont=dict(size=fs_label),gridcolor='lightgrey'),
                xaxis_title=xlabel,
                yaxis_title=ylabel, 

    )

    else:  

        fig.update_layout(
            legend=dict(x=0),
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor='white',
            xaxis=dict(
                tickmode='array',
                tickvals=x_ticks[::2],
                ticktext=x_labels[::2],gridcolor='lightgrey'
                ),
            yaxis=dict(title=ylabel, titlefont=dict(size=fs_label),gridcolor='lightgrey'),
            xaxis_title=xlabel,
            yaxis_title=ylabel, 
            autosize=False, 
            width=size,  # Set width to any desired value
            height=int(size / a4_aspect_ratio)
        )
      

# plot child
    no_sbmi = False   
    if age_years is None and age_months is None:
        no_sbmi = True   
        sbmi_result = "s-BMI will display here" 
    if age_years ==0 and age_months == 0:
        age_total_months = 0
    if bmi is None:
        sbmi_result = "s-BMI will display here" 
    if age_years is None and age_months is not None:
        age_total_months = age_months
    if age_years is not None and age_months is None:
        age_total_months =  age_years*12 
    if age_years is not None and age_months is not None and bmi is not None:
        age_total_months = age_years*12 + age_months


    if no_sbmi == False and bmi is not None:

        sbmi_number, sbmi_result = sbmi_zscore(age_total_months, sex_nr, bmi)    


        fig.add_trace(go.Scatter(
                        x=[age_total_months],
                        y= [bmi],
                        mode='markers',
                        marker=dict(color='black', size=6)
                        ,showlegend=False,
                        name='Child'
                    ))
    return fig, sbmi_result


if __name__ == '__main__':
    app.run_server(debug=False)
