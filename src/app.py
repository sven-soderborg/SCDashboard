import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import dash_loading_spinners as dls
from PIL import Image

# Load data
data = pd.read_feather('data/ut_data.feather')
data.dropna(subset=['earn_mdn_4yr'], inplace=True) # Drop rows with missing earnings data


# Create a Dash app instance
app = dash.Dash(__name__)
server = app.server

# Unique universities and majors
unique_universities = data['instnm'].unique().tolist()
unique_majors = data['cipdesc'].unique().tolist()
top_10_majors = data.groupby('cipdesc')['tot_mdn_earn_4yr'].mean().nlargest(10).index.tolist()
bottom_10_majors = data.groupby('cipdesc')['tot_mdn_earn_4yr'].mean().nsmallest(10).index.tolist()


# App layout
app.layout = html.Div([
    html.H1("Earnings Outcomes by Major and University", style={'textAlign': 'center'}),

    html.Div([
        html.Div([
            # Dropdown for selecting universities
            html.Label("Select Universities:"),
            dcc.Dropdown(
                id='university-dropdown',
                options=[{'label': university, 'value': university} for university in unique_universities],
                multi=True, 
                value=unique_universities  # Default to all universities
            ),

            # Dropdown for selecting majors
            html.Label("Select Majors:"),
            dcc.Dropdown(
                id='major-dropdown',
                options=[{'label': 'All Majors', 'value': 'All Majors'}, 
                         {'value': 'Highest', 'label': 'Top 10 Earning Majors'}, 
                         {'value': 'Lowest', 'label': 'Bottom 10 Earning Majors'}] + 
                         [{'label': major, 'value': major} for major in unique_majors],
                multi=True,
                value='Highest'
                
    )], className='four columns'),

    html.Div([
        dls.Hash(
            html.Div(dcc.Graph(id='earnings-scatter')))
    ], className='eight columns')
    
    ], className='row')
], className='container')

# Callback function to update the scatter plot based on user selections
@app.callback(
    Output('earnings-scatter', 'figure'),
    [Input('university-dropdown', 'value'),
     Input('major-dropdown', 'value')]
)
def update_scatter(selected_universities, selected_majors):
    if selected_majors:
        # Add predefined lists of majors to the list of majors to be displayed
        majors = []
        if 'Highest' in selected_majors:
            majors += top_10_majors
            if type(selected_majors) is list:
                selected_majors.remove('Highest')
        if 'Lowest' in selected_majors:
            majors += bottom_10_majors
            if type(selected_majors) is list:
                selected_majors.remove('Lowest')
        if 'All Majors' in selected_majors:
            majors += unique_majors
            if type(selected_majors) is list:
                selected_majors.remove('All Majors')
        
        # Add rest of selections to the list of majors to be displayed
        majors += selected_majors
    else: # Nothing selected
        return {"layout": {
                    "xaxis": {
                        "visible": False
                    },
                    "yaxis": {
                        "visible": False
                    },
                    "annotations": [
                        {
                            "text": "No matching data found",
                            "xref": "paper",
                            "yref": "paper",
                            "showarrow": False,
                            "font": {
                                "size": 28
                            }
                        }
                    ]
                }
            }
    
    # Filter data based on selected universities and majors
    filtered_data = data[(data['instnm'].isin(selected_universities)) & 
                         (data['cipdesc'].isin(majors))]
    
    # Sort data based on university agnostic median earnings
    filtered_data = filtered_data.sort_values('tot_mdn_earn_4yr', ascending=True)
    
    # Create scatter plot
    fig = px.scatter(
        filtered_data, 
        x='tot_mdn_earn_4yr', 
        y='earn_mdn_4yr', 
        hover_name='cipdesc',
        hover_data={'net_price': ':$,.0f', 'instnm': True, 'tot_mdn_earn_4yr': ':$,.0f', 'earn_mdn_4yr': ':$,.0f'},
        labels={'cipdesc': 'Major', 'earn_mdn_4yr': 'University Level Median Earnings 4yr', 
                'tot_mdn_earn_4yr': 'Median Earnings by Major Across Universities', 
                'instnm': 'University', 'net_price': 'Net Price'}
    )
    fig.update_traces(marker_color="rgba(0,0,0,0)")
    
    # Access preloaded logos and add them to the figure
    for row in filtered_data.values:
        name = row[1].replace(' ', '-')
        fig.add_layout_image(
                dict(
                    source=f"https://raw.githubusercontent.com/sven-soderborg/SCDashboard/main/src/logos/{name}.png",
                    xref="x",
                    yref="y",
                    xanchor="center",
                    yanchor="middle",
                    x=row[13],
                    y=row[8],
                    sizex=3000,
                    sizey=3000,
                    sizing="contain",
                    opacity=1,
                    layer="above"
                )
            )
        
    # Update Appearance
    fig.update_layout(autosize=True, plot_bgcolor="#FFFFFF", 
                      xaxis_title=dict(text="Major Median Earnings Across Selected Universities", font=dict(size=18)),
                      yaxis_title=dict(text="Major Median Earnings by University", font=dict(size=18)),
                      dragmode="pan")
    fig.update_xaxes(tickprefix="$", automargin=True)
    fig.update_yaxes(tickprefix="$", automargin=True)

    
    # Return the figure to be displayed
    return fig

if __name__ == '__main__':
    app.run_server(debug=False)
