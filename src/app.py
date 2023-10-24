import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
from PIL import Image
import numpy as np

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

introduction = html.Div([html.H1("Utah’s Degree Decision: Major Choices, Major Futures"),
                         html.P("""Deciding on which university to attend, and what to study once you're there can be stressful.
                                One question that many ask themselves may be \"Is this going to be worth it?\""""),
                        html.P("""Using data from the College Scorecard, we've created a tool to gain a better understanding
                                of the short-term earnings potential for various majors across the predominent universities in Utah.""")])

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
        value='Highest'
    ),
    
    # Scatter plot for displaying median earnings
    dcc.Graph(id='earnings-scatter')])

# App layout
app.layout = html.Div([introduction, visualization])

# Callback function to update the scatter plot based on user selections
@app.callback(
    Output('earnings-scatter', 'figure'),
    [Input('university-dropdown', 'value'),
     Input('major-dropdown', 'value')]
)
def update_scatter(selected_universities, selected_majors):
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
        hover_data={'mdcost_all': ':$,.0f', 'cipdesc': True, 'tot_mdn_earn_4yr': ':$,.0f', 'earn_mdn_4yr': ':$,.0f'},
        labels={'cipdesc': 'Major', 'earn_mdn_4yr': 'University Level Median Earnings 4yr', 
                'tot_mdn_earn_4yr': 'Median Earnings by Major Across Universities', 
                'instnm': 'University', 'mdcost_all': 'Median Cost of Attendance'}
    )
    fig.update_traces(marker_color="rgba(0,0,0,0)")

    maxDim = filtered_data[["tot_mdn_earn_4yr", "earn_mdn_4yr"]].max().idxmax()
    maxi = filtered_data[maxDim].max()
    for i, row in filtered_data.iterrows():
        name = row['instnm'].replace(' ', '-')
        fig.add_layout_image(
            dict(
                source=Image.open(f"logos/{name}.png"),
                xref="x",
                yref="y",
                xanchor="center",
                yanchor="middle",
                x=row["tot_mdn_earn_4yr"],
                y=row["earn_mdn_4yr"],
                sizex=maxi * .02,
                sizey=maxi * .02,
                sizing="contain",
                opacity=1,
                layer="above"
            )
        )

    # Update Appearance
    fig.update_layout(height=800, width=1500, plot_bgcolor="#FFFFFF", hovermode="closest",
                      title=dict(text="4 Year Median Earnings by Major and University", font=dict(size=25), xanchor='center', yanchor='top',
                                 y=1, x=.5),
                      xaxis_title=dict(text="Major Median Earnings Across Selected Universities", font=dict(size=18)),
                      yaxis_title=dict(text="Major Median Earnings by University", font=dict(size=18)))
    fig.update_xaxes(tickprefix="$")
    fig.update_yaxes(tickprefix="$")

    # Add labels for the majors
    # txt_y = filtered_data['earn_mdn_4yr'].min() - 5000
    # placed_xs = []
    # for major in filtered_data['cipdesc'].unique():
    #     filtered_major = filtered_data[filtered_data['cipdesc'] == major]
    #     txt_x = filtered_major['tot_mdn_earn_4yr'].mean()
    #     cipcode = filtered_major['cipcode'].iloc[0]
    #     if any(abs(txt_x - item) <= 900 for item in placed_xs):
    #         txt_y += 1000
    #     fig.add_annotation(x=txt_x, y=txt_y, text=cipcode, showarrow=False, font=dict(size=12), hovertext=f'{major}\n${txt_x:.0f}', borderpad=10)
    #     placed_xs.append(txt_x)

    
    # Return the figure to be displayed
    return fig

if __name__ == '__main__':
    app.run_server(debug=False)
