import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html


#---------------------------------------------------
WHO = pd.read_csv('assets/Child_BMI_references_clean/WHO_2024_03_25.csv')
IOTF = pd.read_csv('assets/Child_BMI_references_clean/IOTF_2024_03_25.csv')
CDC_pct = pd.read_csv('assetsChild_BMI_references_clean/CDC_2023_pct_P95_2024_03_25.csv')
CDC = pd.read_csv('assets/Child_BMI_references_clean/CDC_2023_zscore_2024_03_25.csv')

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

app = dash.Dash(__name__)

app.layout = html.Div([
            html.H1("Child BMI references for children with overweight and obesity"),

   
    html.Div([
        dcc.Graph(id='graph-container')
    ]),
    html.Div([dcc.RadioItems(id = 'radio_item_sex', options = ['girl', 'boy'], value = 'girl', inline=True)],
             ),
     html.Div([
        html.Div(
            style={'width': '20%', 'height': '100%', 'float': 'left'},
            children=[
                html.H6("World Health Organisation"),
                dcc.Checklist(
                    id='checkbox-container_WHO',
                    options=[
                        {'label': 'SD0', 'value': 'SD0'},
                        {'label': 'SD1', 'value': 'SD1'},
                        {'label': 'SD2', 'value': 'SD2'},
                        {'label': 'SD3', 'value': 'SD3'},
                        {'label': 'SD4', 'value': 'SD4'},
                        {'label': 'SD5', 'value': 'SD5'},
                        {'label': 'SD6', 'value': 'SD6'},
                        {'label': 'SD7', 'value': 'SD7'},
                        {'label': 'SD8', 'value': 'SD8'},
                    ],value =['SD0'],
                  
                ),
            ]
        ),
        html.Div(
            style={'width': '20%', 'height': '100%', 'float': 'left', 'display': 'inline-block'},
            children=[
                html.H6("International Obesity Taskforce"),
                dcc.Checklist(
                    id='checkbox-container_IOTF',
                    options=[
                        {'label': 'BMI25', 'value': 'BMI_25'},
                        {'label': 'BMI30', 'value': 'BMI_30'},
                        {'label': 'BMI35', 'value': 'BMI_35'},
                        {'label': 'BMI40', 'value': 'BMI_40'},
                        {'label': 'BMI45', 'value': 'BMI_45'},
                        {'label': 'BMI50', 'value': 'BMI_50'},
                        {'label': 'BMI55', 'value': 'BMI_55'},
                        {'label': 'BMI60', 'value': 'BMI_60'},
                    ],
                 
                )
            ]
        ),
        html.Div(
            style={'width': '20%', 'height': '100%', 'float': 'left', 'display': 'inline-block'},
            children=[
                html.H6("CDC zscore (extended)"),
                dcc.Checklist(
                    id='checkbox-container_CDC',
                    options=[
                        {'label': 'SD0', 'value': 'SD0'},
                        {'label': 'SD1', 'value': 'SD1'},
                        {'label': 'SD2', 'value': 'SD2'},
                        {'label': 'SD3', 'value': 'SD3'},
                        {'label': 'SD4', 'value': 'SD4'},
                        {'label': 'SD5', 'value': 'SD5'},
         
                    ], value =['SD0'],
                  
                )
            ]
        ),
        html.Div(
            style={'width': '20%', 'height': '100%', 'float': 'left', 'display': 'inline-block'},
            children=[
                html.H6("CDC % above 95 percentile"),
                dcc.Checklist(
                    id='checkbox-container_CDC95P',
                    options=[
                        {'label': '85P', 'value': 'P85'},
                        {'label': '95P', 'value': 'P95'},
                        {'label': '120%', 'value': 'pct120ofP95'},
                        {'label': '140%', 'value': 'pct140ofP95'},
                        {'label': '150%', 'value': 'pct150ofP95'},
                        {'label': '160%', 'value': 'pct160ofP95'},
                        {'label': '180%', 'value': 'pct180ofP95'},
                        {'label': '200%', 'value': 'pct200ofP95'}
                    ],value =['P85'],
                    
                )
            ]
        ),
    ]),
])
@app.callback(
    Output(component_id='graph-container', component_property='figure'),
    
    [Input(component_id = 'radio_item_sex', component_property = 'value'),
     
    Input(component_id = 'checkbox-container_WHO', component_property='value'), 
    Input(component_id = 'checkbox-container_IOTF', component_property = 'value'),
    Input(component_id = 'checkbox-container_CDC', component_property='value'), 
    Input(component_id = 'checkbox-container_CDC95P', component_property = 'value'),
    ]
)
def update_graph(sex, WHO, IOTF, CDC, CDC95P):
    print(sex, WHO, IOTF, CDC, CDC95P)
    if sex  == 'girl':
        WHO_axes = girls['WHO']
#         IOTF = girls['IOTF']
        CDC_axes = girls['CDC']
        CDC95P_axes = girls['CDC_pct']  

    else:
        WHO_axes = boys['WHO']
#         IOTF = boys['IOTF']
        CDC_axes = boys['CDC']
        CDC_95P = boys['CDC_pct']
    colors = ['blue', 'red']

    fig = go.Figure()

    for level in reversed(WHO):
        fig.add_trace(go.Scatter(x=WHO_axes['age_months'], y=WHO_axes[level], mode='lines', name=level,
                                 line=dict(color='#009CDE'), showlegend=False))
        
        label = f'WHO-{level}'
        placement_y = 119
        max_value_x = WHO_axes[(WHO_axes['age_months'] == placement_y)][level].iloc[0]
        fig.add_annotation(x=placement_y, y=max_value_x, text=label, showarrow=False, font=dict(size=8), bgcolor="white",
                           bordercolor = '#009CDE', borderwidth=1)
#     for level in reversed(IOTF):
#         print(level)


    for level in reversed(CDC):
        fig.add_trace(go.Scatter(x=CDC_axes['age_months'], y=CDC_axes[level], mode='lines', name=level,
                                 line=dict(color='red'),showlegend=False))
        
        label = f'CDC-{level}'
        placement_y =  144.5
        max_value_x = CDC_axes[(CDC_axes['age_months'] == placement_y)][level].iloc[0]
        fig.add_annotation(x=placement_y, y=max_value_x, text=label, showarrow=False, font=dict(size=8), bgcolor="white",
                            bordercolor="red", borderwidth=1)
        
    for level in reversed(CDC95P):
        fig.add_trace(go.Scatter(x=CDC95P_axes['age_months'], y=CDC95P_axes[level], mode='lines', name=level,
                                 line=dict(color='maroon'),showlegend=False))
        label = f'CDC-{level}'
        placement_y =  168.5
        max_value_x = CDC95P_axes[(CDC95P_axes['age_months'] == placement_y)][level].iloc[0]
        fig.add_annotation(x=placement_y, y=max_value_x, text=label, showarrow=False, font=dict(size=8), bgcolor="white",
                           bordercolor="maroon", borderwidth=1)
        
    
    fig.update_yaxes(range=[10, 70])
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
    
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)