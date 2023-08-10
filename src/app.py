from dash import dash, dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
import plotly.express as px

df = pd.read_csv('./data/plotdata24.csv')
pvals = pd.read_csv('./data/fdr24.csv')

#df.head()

predictor_dict = {'donorparity': 'Donor parity','idbloodgroupcat': 'ABO identical transfusion','meandonationtime': 'Time of donation','meandonorage': 'Age of Donor','meandonorhb': 'Donor Hb','meandonorsex': 'Donor sex','meanstoragetime': 'Storage time (days)','meanweekday': 'Weekday of donation','numdoncat': 'Donors prior number of donations','timesincecat': 'Time since donors previous donation'}
label_dict = {'ALAT': 'ALT','ALB': 'Albumin','ALP': 'ALP','APTT': 'aPTT','ASAT': 'AST','BASOF': 'Basophiles','BE': 'Base Excess','BILI': 'Bilirubin','EVF':'EVF', 'BILI_K': 'Conjugated bilirubin','BLAST': 'Blast cells','CA': 'Calcium','CA_F': 'Free Calcium','CL': 'Chloride','CO2': 'Carbon Dioxide','COHB': 'CO-Hb','CRP': 'CRP','EGFR': 'eGFR','EOSINO': 'Eosinophile count','ERYTRO': 'Erythrocyte count','ERYTROBL': 'Erythroblasts','FE': 'Iron','FERRITIN': 'Ferritin','FIB': 'Fibrinogen','GLUKOS': 'Glucose','GT': 'Glutamyl transferase','HAPTO': 'Haptoglobin','HB': 'Hemoglobin','HBA1C': 'HbA1c','HCT': 'Hematocrit','INR': 'INR','K': 'Potassium','KREA': 'Creatinine','LAKTAT': 'Lactate','LD': 'Lactate dehydrogenase','LPK': 'Leukocyte count','LYMF': 'Lymphocyte count','MCH': 'Mean corpuscular  hemoglobin','MCHC': 'Mean corpuscular  hemoglobin concentration','MCV': 'Mean corpuscular volume','META': 'Metamyelocyte count','METHB': 'Methemoglobin','MONO': 'Monocyte count','MYELO': 'Myelocyte count','NA': 'Sodium','NEUTRO': 'Neutrophile count','NTPROBNP': 'NT-ProBNP','OSMO': 'Osmolality','PCO2': 'PaCO2','PH': 'pH','PO2': 'PaO2','RET': 'Reticulocyte count','STDBIK': 'Standard bicarbonate','TPK': 'Platelet count','TRI': 'Triglycerides','TROP_I': 'Troponin I','TROP_T': 'Troponin T'}

df=df.dropna()

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    dcc.Dropdown(
        id="label-dropdown",
        options=[{"label": label_dict[x], "value": x} for x in df['label'].unique()],
        value='HB',
        clearable=False,
    ),
    dcc.Dropdown(
        id="predictor-dropdown",
        options=[{"label": predictor_dict[x], "value": x} for x in df['predictor'].unique()],
        value='meandonorhb',
        clearable=False,
    ),
    dcc.Graph(id="line-graph"),
], style={'padding': '20px'})
@app.callback(
    Output("line-graph", "figure"),
    [Input("label-dropdown", "value"), Input("predictor-dropdown", "value")]
)
def update_graph(selected_label, selected_predictor):
    dff = df[(df['label'] == selected_label) & (df['predictor'] == selected_predictor)]
    current_fpval = float(pvals[(pvals['label'] == selected_label) & (pvals['predictor'] == selected_predictor)]['ProbF'].iloc[0])
    current_fdrp = float(pvals[(pvals['label'] == selected_label) & (pvals['predictor'] == selected_predictor)]['fdr_p'].iloc[0])
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
    if selected_predictor in ['donorparity', 'idbloodgroupcat', 'meandonorsex', 'meanweekday', 'numdoncat', 'timesincecat']:
        # No fill for error bars plots
        data = [trace]
        layout = go.Layout(
            yaxis=dict(title="Delta %s (95%% CI)" % label_dict[selected_label]),
            xaxis=dict(title=predictor_dict[selected_predictor], dtick=1), # Adding dtick=1 forces integer ticks
            title="Association between %s and delta %s Raw p-value = %s, FDR-adjusted p-value = %s" % (predictor_dict[selected_predictor], label_dict[selected_label], np.format_float_scientific(current_fpval,precision=2),np.format_float_scientific(current_fdrp,precision=2)),
            showlegend = False
        )
    else:
        # Create a trace for the confidence band
        data = [upper_band, lower_band, line_trace]
        layout = go.Layout(
            yaxis=dict(title="Delta %s (95%% CI)" % label_dict[selected_label]),
            xaxis=dict(title=predictor_dict[selected_predictor]),
            title="Association between %s and delta %s Raw p-value = %s, FDR-adjusted p-value = %s" % (predictor_dict[selected_predictor], label_dict[selected_label], np.format_float_scientific(current_fpval,precision=2),np.format_float_scientific(current_fdrp,precision=2)),
            showlegend = False
        )
    layout.update(height=600, width=800)
    layout.template = "ggplot2"
    fig = go.Figure(data=data, layout=layout)
    return fig
if __name__ == "__main__":
    app.run_server(debug=True)