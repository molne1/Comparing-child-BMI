import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import Dash, dcc, html, Input, Output, callback
import flask
import dash_bootstrap_components as dbc

#---------------------------------------------------
WHO = pd.read_csv('assets/WHO_2024_03_25.csv')
IOTF = pd.read_csv('assets/IOTF_2024_03_25.csv')
CDC_pct = pd.read_csv('assets/CDC_2023_pct_P95_2024_03_25.csv')
CDC = pd.read_csv('assets/CDC_2023_zscore_2024_03_25.csv')

IOTF.name = 'IOTF'
WHO.name = 'WHO'
CDC_pct.name = 'CDC_pct'
CDC.name = 'CDC'


ALL_references = [IOTF, WHO, CDC_pct, CDC]

boys = {}
girls = {}
ALL_references = [IOTF, WHO, CDC_pct, CDC]
for reference in ALL_references:
    boys[f'{reference.name}'] = reference[reference['sex'] == 1]
    girls[f'{reference.name}'] = reference[reference['sex'] == 2]

#-----------------------------------------
server = flask.Flask(__name__)
#-----------------------------------------

WHO_color = '#009CDE'
IOTF_color = 'green'
CDC_color = 'red'
CDCpct_color = 'maroon'


ylabel = 'Body Mass Index (kg/m^2)'
xlabel = 'Age (Years)'
fs_label = 18


#-----------------------------------

app = dash.Dash(__name__,
                server=server,
                title="Child BMI references for children with overweight and obesity.",
                suppress_callback_exceptions=True,
                external_stylesheets=[dbc.themes.SANDSTONE])

app.layout = dbc.Container([
    dbc.Row([html.H1("Child BMI references for children with overweight and obesity")],className=" mt-5"),
    
    dbc.Row([dbc.Col([
                html.H3("About"),
                html.P("This app was built with the purpose of visually comparing different child BMI references for children with overweight or obesity. The app relies on public data from a set of publications and official websites. More information is presented beneath the graph. ")
                ], className = "p-3" ),
             dbc.Col([html.H3("How-to"), 
                        html.P("First choose sex by clicking the buttons on the left of the graph. Then, under the graph you find the different references, you can choose what curves to display by clicking the small sliders. The graph is interactive so you can also zoom in and out get exact values by hovering above a specific line.  OPTIONAL: If you would like to display a child's data point on the graph you can add age in years and body mass index in kg divided my meter squared (kg/m^2)")
                        ], 
                        className = 'p-3')
            ]),

   
    dbc.Row([dbc.Col(dcc.Graph(id='graph-container'), width=10),
            dbc.Col([
                dbc.Row(
                [html.H5("Choose sex"),
                 dbc.RadioItems(
                      className="btn-group",
                        id="sex",
                            inputClassName="btn-check",
                            labelClassName="btn btn-primary",
                            labelCheckedClassName="active",
                            options=[
                                    {"label": "Girl", "value": 1},
                                    {"label": "Boy", "value": 2},
                                    ],
                            value = [1]                
                            ), 
                ]), 
                dbc.Row([
                     
                        html.H6("Display a child's point by entering age and BMI"),
                        dbc.Input(id = 'age', placeholder='Enter age in years', type='number', value='',min=0, max=20,),
                        dbc.Input(id = 'BMI', placeholder='Enter BMI', type='number', value='', min=10, max=70)
                        ],
                        className = "mt-5 p-2"
                    ),],
                    className = "mt-3"
                )],
        className ="border"
    ),

dbc.Row([
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
                html.H6("CDC zscore (Extended)",style={"color": CDC_color}),
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
                html.H6("CDC % above 95 percentile",style={"color": CDCpct_color}),
                dbc.Checklist(
                    id='checkbox-container_CDC95P',
                    options=[
                        {'label': '85 percentile - overweight', 'value': 'P85'},
                        {'label': '95 percentile - obesity class I', 'value': 'P95'},
                        {'label': '120% - obesity class II', 'value': 'pct120ofP95'},
                        {'label': '140% - obesity class III', 'value': 'pct140ofP95'},
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
    dbc.Accordion(
            [
                dbc.AccordionItem(
                    [ html.P("References:"),
                     html.P("https://www.who.int/toolkits/child-growth-standards/standards/body-mass-index-for-age-bmi-for-age "),
                     ],
                    title="World Health Organisation(WHO)",
                ),
                dbc.AccordionItem(
                    [html.P("References"),
                     

                    ],
                    title="International Obesity Task Force (IOTF)",
                ),
                dbc.AccordionItem(
                    "References",
                    title="Center for Disease Control and Prevention(CDC)",
                ),

            ],),
            
        ],
    className ="mt-5"),
dbc.Row(html.P("This app was created by Maja Engsner, the code is openly available at GitHub, and together with the graph is free to use under creative commons licence (CC). No funding was received for creating this app."
            ),
    className ="mt-5")
])

@app.callback(
    Output(component_id='graph-container', component_property='figure'),
    
    [Input(component_id = 'sex', component_property = 'value'),
     Input(component_id = 'age', component_property = 'value'),
    Input(component_id = 'BMI', component_property = 'value'),
    Input(component_id = 'checkbox-container_WHO', component_property='value'), 
    Input(component_id = 'checkbox-container_IOTF', component_property = 'value'),
    Input(component_id = 'checkbox-container_CDC', component_property='value'), 
    Input(component_id = 'checkbox-container_CDC95P', component_property = 'value'),
    ]
)
def update_graph(sex, age, bmi, WHO, IOTF, CDC, CDC95P):
    if sex == 1:
        WHO_axes = girls['WHO']
        IOTF_axes = girls['IOTF']
        CDC_axes = girls['CDC']
        CDC95P_axes = girls['CDC_pct']  

    if sex == 2:
        WHO_axes = boys['WHO']
        IOTF_axes = boys['IOTF']
        CDC_axes = boys['CDC']
        CDC95P_axes = boys['CDC_pct']
    colors = ['blue', 'red']

    fig = go.Figure()

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
        
    
    # fig.update_yaxes(range=[10, 65])
    fig.update_xaxes(range=[0, 240])

    x = range(0, 241)
    x_ticks = [month for i, month in enumerate(x) if month % 12 == 0 and i % 2 == 0]  
    x_labels = [str(i) for i in range(len(x_ticks))]

    fig.update_layout(legend=dict(x=0),
        plot_bgcolor='white',
        
        xaxis=dict(
            tickmode='array',
            tickvals=x_ticks[::2],
            ticktext=x_labels[::2],gridcolor='lightgrey'
        ),
        yaxis=dict(title=ylabel, titlefont=dict(size=fs_label),gridcolor='lightgrey'),
        xaxis_title=xlabel,
        yaxis_title=ylabel)
# plot child
    if age is not None and bmi is not None:
            fig.add_trace(go.Scatter(
                x=[age*12],
                y=[bmi],
                mode='markers',
                marker=dict(color='black', size=6)
                ,showlegend=False,
                name='Child'
            ))
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=False)
