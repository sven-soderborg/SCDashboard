import dash
import time
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from PIL import Image
import dash_loading_spinners as dls

# Load data
data = pd.read_feather('data/ut_data.feather')
data.dropna(subset=['earn_mdn_4yr'], inplace=True) # Drop rows with missing earnings data


# Create a Dash app instance
app = dash.Dash(__name__)
server = app.server

# Unique universities and majors
unique_universities = data['instnm'].unique().tolist()
unique_majors = data['cipdesc'].unique().tolist()
top_10_majors = data.groupby('cipdesc')['earn_mdn_4yr'].mean().nlargest(10).index.tolist()
bottom_10_majors = data.groupby('cipdesc')['earn_mdn_4yr'].mean().nsmallest(10).index.tolist()


# Preload all university logos
logo_directory = "logos/"
university_logos = {university.replace(' ', '-'): Image.open(logo_directory + university.replace(' ', '-') + ".png") for university in unique_universities}

visualization = html.Div([html.H1("Median Earnings by Major and University"),
    
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
        options=[{'label': 'All Majors', 'value': 'All Majors'}, {'value': 'Highest', 'label': 'Top Earning Majors'}, 
                 {'value': 'Lowest', 'label': 'Bottom Earning Majors'}] + [{'label': major, 'value': major} for major in unique_majors],
        multi=True,
        value='All Majors'
    )])


# App layout
app.layout = html.Div([visualization, dls.Hash(html.Div(dcc.Graph(id='earnings-scatter')))])

# Callback function to update the scatter plot based on user selections
@app.callback(
    Output('earnings-scatter', 'figure'),
    [Input('university-dropdown', 'value'),
     Input('major-dropdown', 'value')]
)
def update_scatter(selected_universities, selected_majors):
    t0 = time.time()
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
        hover_name='instnm',
        hover_data={'net_price': ':$,.0f', 'cipdesc': True, 'tot_mdn_earn_4yr': ':$,.0f', 'earn_mdn_4yr': ':$,.0f'},
        labels={'cipdesc': 'Major', 'earn_mdn_4yr': 'University Level Median Earnings 4yr', 
                'tot_mdn_earn_4yr': 'Median Earnings by Major Across Universities', 
                'instnm': 'University', 'net_price': 'Net Price'}
    )
    fig.update_traces(marker_color="rgba(0,0,0,0)")
    
    # Access preloaded logos and add them to the figure
    t1 = time.time()
    for _, row in filtered_data.iterrows():
        name = row['instnm'].replace(' ', '-')
        logo = university_logos[name]
        if logo:
            fig.add_layout_image(
                dict(
                    source=logo,
                    xref="x",
                    yref="y",
                    xanchor="center",
                    yanchor="middle",
                    x=row["tot_mdn_earn_4yr"],
                    y=row["earn_mdn_4yr"],
                    sizex=2000,
                    sizey=2000,
                    sizing="contain",
                    opacity=1,
                    layer="above"
                )
            )
    print(f"Took {time.time() - t1} seconds to add logos")


    # Update Appearance
    fig.update_layout(height=800, width=1500, plot_bgcolor="#FFFFFF", hovermode="closest",
                      title=dict(text="4 Year Median Earnings by Major and University", font=dict(size=25), xanchor='center', yanchor='top',
                                 y=1, x=.5),
                      xaxis_title=dict(text="Major Median Earnings Across Selected Universities", font=dict(size=18)),
                      yaxis_title=dict(text="Major Median Earnings by University", font=dict(size=18)))
    fig.update_xaxes(tickprefix="$")
    fig.update_yaxes(tickprefix="$")

    print(f"Took {time.time() - t0} seconds to update scatter")
    
    # Return the figure to be displayed
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
