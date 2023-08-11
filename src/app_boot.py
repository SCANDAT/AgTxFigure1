from dash import dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import plotly.express as px
import numpy as np
import dash_bootstrap_components as dbc

from config import predictor_dict, label_dict
from functions import format_pvalue

df = pd.read_csv('./data/plotdata24.csv')
pvals = pd.read_csv('./data/fdr24.csv')

df=df.dropna()

#app = dash.Dash(__name__)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

server = app.server

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                id="label-dropdown",
                options=[{"label": label_dict[x], "value": x} for x in df.iloc[df['label'].map(label_dict).argsort()]['label'].unique()],
                value='HB',
                clearable=False,
            )
        ]),
        dbc.Col([
            dcc.Dropdown(
                id="predictor-dropdown",
                options=[{"label": predictor_dict[x], "value": x} for x in df.iloc[df['predictor'].map(predictor_dict).argsort()]['predictor'].unique()],
                value='meandonorhb',
                clearable=False,
            )
        ]),
        dbc.Col([
            dcc.Checklist(
                id="adjustment-checklist",
                options=[{'label': "Adjusted for donor hemoglobin", 'value': 'adjusted'}],
                value=[]
            )
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id="line-graph")
        ], align="center")
    ])
], fluid=True)

@app.callback(
   Output("line-graph", "figure"),
   [Input("label-dropdown", "value"), 
   Input("predictor-dropdown", "value"),
   Input("adjustment-checklist", "value")]
)
def update_graph(selected_label, selected_predictor, adjustment_values):
    dff = df[(df['label'] == selected_label) & (df['predictor'] == selected_predictor)]
    filtered_pvals = pvals[(pvals['label'] == selected_label) & (pvals['predictor'] == selected_predictor)]
    if 'adjusted' in adjustment_values:
        dff = dff[dff['adjusted'] == 1]
    else:
        dff = dff[dff['adjusted'] == 0]
    if dff.empty | filtered_pvals.empty:
        return {
            'data': [],
            'layout': {
                'title': 'Combination not possible',
                'xaxis': {
                    'visible': False
                },
                'yaxis': {
                    'visible': False
                },
                'annotations': [
                    {
                        'text': 'No data available for the selected combination',
                        'xref': 'paper',
                        'yref': 'paper',
                        'showarrow': False,
                        'font': {
                            'size': 20
                        }
                    }
                ]
            }
        }
    current_fpval = float(filtered_pvals['ProbF'].iloc[0])
    current_fdrp = float(filtered_pvals['fdr_p'].iloc[0])
    # Create a trace for a dot plot with error bars
    trace = go.Scatter(
        x=dff['predictorvalue'],
        y=dff['predicted'],
        mode='markers',
        error_y=dict(
            type='data',
            symmetric=False,
            array=dff['upper'] - dff['predicted'],
            arrayminus=dff['predicted'] - dff['lower']
        ),
        name='Prediction'
    )
    # Create the line trace
    line_trace = go.Scatter(
        x=dff['predictorvalue'],
        y=dff['predicted'],
        mode='lines',
        name='Prediction',
        line=dict(color='rgb(31, 119, 180)')
    )
    # Create a trace for the lower confidence interval
    upper_band = go.Scatter(
        x=dff['predictorvalue'],
        y=dff['upper'],
        mode='lines',
        name='Upper Bound',
        marker=dict(color="#444"),
        line=dict(width=0)
    )

    # Create a trace for the lower confidence interval with fill to the upper_band
    lower_band = go.Scatter(
        x=dff['predictorvalue'],
        y=dff['lower'],
        mode='lines',
        name='Lower Bound',
        marker=dict(color="#444"),
        line=dict(width=0),
        fillcolor='rgba(68, 68, 68, 0.3)',
        fill='tonexty'
    )
    
    title_template = ("Association between {predictor} and Δ{label}:<br>Raw p={raw_p}, FDR-p={fdr_p}")
    formatted_title = title_template.format(
        predictor=predictor_dict[selected_predictor],
        label=label_dict[selected_label],
        raw_p=format_pvalue(current_fpval),
        fdr_p=format_pvalue(current_fdrp)
    )
    xaxislabel=predictor_dict[selected_predictor]
    yaxislabel="Delta %s (95%% CI)" % label_dict[selected_label]

    if selected_predictor in ['donorparity', 'idbloodgroupcat', 'meandonorsex', 'meanweekday', 'numdoncat']:
        # No fill for error bars plots
        data = [trace]
        layout = go.Layout(
            yaxis=dict(title=yaxislabel),
            xaxis=dict(title=xaxislabel, dtick=1), # Adding dtick=1 forces integer ticks
            title=formatted_title,
            showlegend = False
        )
    elif selected_predictor == 'timesincecat':
        # No fill for error bars plots
        data = [trace]
        layout = go.Layout(
            yaxis=dict(title=yaxislabel),
            xaxis=dict(title=xaxislabel, tickvals=list(range(0, 1000, 100))), # Adding dtick=1 forces integer ticks
            title=formatted_title,
            showlegend = False
        )
    else:
        # Create a trace for the confidence band
        data = [upper_band, lower_band, line_trace]
        layout = go.Layout(
            yaxis=dict(title=yaxislabel),
            xaxis=dict(title=xaxislabel),
            title=formatted_title,
            showlegend = False
        )
    #layout.update(height=800, width=1100)
    layout.template = "ggplot2"
    fig = go.Figure(data=data, layout=layout)
    return fig
if __name__ == "__main__":
    app.run_server(debug=True)