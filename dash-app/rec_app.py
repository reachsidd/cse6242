import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import recco
from dash import dash_table as dt
from dash import dcc
from dash import html
from dash.dependencies import Input, Output

#initialising dash app
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

server = app.server

CONTENT_STYLE = {
    "marginLeft": "0rem",
    "marginRight": "0rem",
    "padding": "1rem 1rem",
    "color": 'white',
    "backgroundImage": "url('assets/back-ground.jpg')",
    "backgroundSize":"cover",
    "fontFamily":"Arial Narrow, sans-serif",
    "height": "100vh",
    "width": "100vw",
    }

empty_fig = go.Figure()
empty_fig.update_layout(
    xaxis={"visible": False},
    yaxis={"visible": False},
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    annotations=[
        {
            "text": " ",
            "xref": "paper",
            "yref": "paper",
            "showarrow": False,
            "font": {
                "size": 32
            }
        }
    ]
)

content = html.Div([
            html.H2("Music Recommendation Engine - Collaborative Approach", className="display-3", id="page-content"),
            html.Br(),
            html.Div(id="hidden_div_for_redirect_callback"),
            html.Div([daq.BooleanSwitch(id='my-boolean-switch', on=False, label={'label':'Use Deep Content Based Recommendation','style':{'font-size':'24px'}}),]),
            html.Label('Search for a song: Artist Year Title',style={'font-size': '32px', 'font-weight': 'bold'}),
            html.Div([
                dcc.Input(
                    id='search_text_input',
                    type='text',
                    value='',
                    style={'width': '50%', 'height': 50, 'font-size': '28px'},
                    placeholder='Type at least 4 characters words ...',
                ),
            ]),
            html.Br(),
            html.Div(id='search-select-content'),
            html.Br(),
            html.Label('Recommended Songs:',style={'fontSize': '32px', 'font-weight': 'bold'}),
            html.Label('[ * 2-cs=cosine similarity, 1-mf=matrix factorization ]', style={'fontSize': '18px'}),
            dbc.Row(
                [
                 dbc.Col(
                     html.Div(id='output-container'
                ), width=6),
                dbc.Col(html.Div([
                    dcc.Graph(
                        id='side-fig1-container', figure=empty_fig,
                    ),
                    html.Div('Original', style={'color': 'white', 'fontSize': '32px', 'text-align': 'center','font-weight': 'bold'}),
                ]), width=3),
                dbc.Col(html.Div([
                    dcc.Graph(
                        id='side-fig2-container', figure=empty_fig,
                    ),
                    html.Div('Recommended', style={'color': 'white', 'fontSize': '32px', 'text-align': 'center','font-weight': 'bold'}),
                ]), width=3),
             ],className="g-0",
            ),
     ])

app.layout = html.Div([dcc.Location(id="url"), content], style=CONTENT_STYLE)

def figure_reco_songs(list_m):
    df = pd.DataFrame(list_m)
    df.rename(columns={"song_id": "id", "rating": "Score", "title": "Title", "artist_name": "Artist", "year": "Year", "score_type": "Method"},inplace=True)
    #df['id']=df['song_id']
    #print(df)
    ordered_cols_for_display=[ "Title", "Artist", "Year","Method", "Score"]
    fig3 = dt.DataTable(
        id='table',
        row_selectable='single',
        columns=[{"name": i, "id": i} for i in ordered_cols_for_display if i not in ["id"]],
        data=df.to_dict('records'),
        style_cell={'textAlign': 'left'},
        style_as_list_view=True,
        style_table={'overflowX': 'auto'},
        style_header={
            'backgroundColor': 'rgba(0,0,0,0)',
            'fontWeight': 'bold',
            "fontFamily":"Arial Narrow, sans-serif",
            "fontSize":"28px",
        },
        style_data={
            'backgroundColor': 'rgba(0,0,0,0)',
            "fontFamily":"Arial Narrow, sans-serif",
            "fontSize": "26px",
        },
    )
    return fig3

@app.callback(
    Output("table", "style_data_conditional"),
    Input("table", "derived_viewport_selected_row_ids"),
)
def style_selected_rows(selRows):
    #print('I am called',selRows)
    if selRows is None:
        return dash.no_update

    return [{"if": {"filter_query": "{{id}} ={}".format(i)}, "backgroundColor": "blue",} for i in selRows]


@app.callback(Output('search-select-content', 'children'),[Input(component_id='search_text_input', component_property= 'value')])
def generate_layout(value):
    if len(value) >= 4:
        songs_df = recco.get_song_list(value)
        #print('response_dic songs=',songs_df)
        #print('LENGTH response_dic songs=',len(songs_df))

        return html.Div([
            html.Label('Search and Select for a song: Artist Year Title',style={'font-size': '32px', 'font-weight': 'bold'}),
            dcc.Dropdown(
                options=[
                        {'label': row['artist_name']+ ' ' +row['year']+ ' ' +row['title'], 'value': row['song_id']} for index, row in songs_df.iterrows()
                ],
                placeholder="Select a song ... ",
                multi=False,
                style={'width': '71%', 'height': 50, 'font-size': '28px','top':5},
                id='search-select-input'
            ),
            html.Div(id='search-select-output')
        ],)


@app.callback(Output(component_id='output-container', component_property= 'children'), [Input('search-select-input', 'value')])
def display_output(original_song_id):
    #print('You have selected "{}"'.format(original_song_id))
    if original_song_id is not None:
        #print('sidd-test-1')
        getl = recco.get_recommendations_by_song_id(original_song_id)
        #print('sidd-test-2')
        return figure_reco_songs(getl)



@app.callback([Output(component_id='side-fig1-container', component_property= 'figure'),Output(component_id='side-fig2-container', component_property= 'figure'),],
    [Input("table", "derived_viewport_selected_row_ids"),Input('search-select-input', 'value'),]
)
def update_side_fig1(selected_reco_song_ids, original_song_id):
    if((selected_reco_song_ids is not None) and (len(selected_reco_song_ids) > 0)):
        selected_reco_song_id=selected_reco_song_ids[0]
    else:
        return empty_fig, empty_fig
    attrs = ["key_confidence_norm", "tempo_norm", "time_signature_norm", "time_signature_confidence_norm",
             "song_hotttnesss_norm"]
    labels = ["Key Confidence", "Tempo", "Time Signature", "Time Signature Confidence", "Song Hotttnesss"]
    #fig1- original
    orig_song_details = recco.get_song_details_by_song_id(original_song_id)
    vals1 = [abs(float(orig_song_details.get(k,0.0))) for k in attrs]
    layout_options = {"title": orig_song_details["title"],
                      "title_font_size": 32,
                      "title_x": 0.5,
                      "legend_x": 0.9,
                      "legend_y": 1.1,
                      "polar_radialaxis_ticks": "",
                      "polar_radialaxis_showticklabels": False,
                      "polar_radialaxis_range": [0, max(vals1)],
                      "polar_angularaxis_ticks": "",
                      "polar_angularaxis_showticklabels": False,
                        "paper_bgcolor":"rgba(0,0,0,0)",
                        "plot_bgcolor":"rgba(0,0,0,0)",
                      "font_color": "white",
                      "title_font_color": "white",
                      "font_family": "Arial Narrow, sans-serif",
                      "font_size": 14,
                        }

    fig1 = make_barpolar(vals1, labels, layout_options=layout_options, opacity=0.7)

    #fig2-reco
    reco_song_details = recco.get_song_details_by_song_id(selected_reco_song_id)

    vals2 = [abs(float(reco_song_details.get(k,0.0))) for k in attrs]

    layout_options = {"title": reco_song_details["title"],
                        "title_font_size": 32,
                        "title_x": 0.5,
                        "polar_radialaxis_ticks": "",
                        "polar_radialaxis_showticklabels": False,
                        "polar_radialaxis_range": [0, max(vals2)],
                        "polar_angularaxis_ticks": "",
                        "polar_angularaxis_showticklabels": False,
                        "paper_bgcolor": "rgba(0,0,0,0)",
                        "plot_bgcolor": "rgba(0,0,0,0)",
                        "font_color": "white",
                        "title_font_color": "white",
                        "showlegend": False,
                      "font_family": "Arial Narrow, sans-serif",
                    }

    fig2 = make_barpolar(vals2, labels, layout_options=layout_options, opacity=0.7)
    return fig1,fig2


def make_barpolar(vals, labels=None, colors=None, layout_options=None, **fig_kwargs):
    # infer slice angles
    num_slices = len(vals)
    theta = [(i + 1.5) * 360 / num_slices for i in range(num_slices)]
    width = [(360 - num_slices*40) / num_slices for _ in range(num_slices)]


    # optionally infer colors
    if colors is None:
        color_seq = px.colors.qualitative.Dark24
        color_indices = range(0, len(color_seq), len(color_seq) // num_slices)
        colors = [color_seq[i] for i in color_indices]

    if layout_options is None:
        layout_options = {}

    if labels is None:
        labels = ["" for _ in range(num_slices)]
        layout_options["showlegend"] = False

    # make figure
    barpolar_plots = [go.Barpolar(r=[r], theta=[t], width=[w], name=n, marker_color=[c], **fig_kwargs)
                      for r, t, w, n, c in zip(vals, theta, width, labels, colors)]

    fig = go.Figure(barpolar_plots)

    # align background
    angular_tickvals = [(i + 1) * 360 / num_slices for i in range(num_slices)]
    fig.update_layout(polar_angularaxis_tickvals=angular_tickvals)

    # additional layout parameters
    fig.update_layout(**layout_options)

    return fig

@app.callback(
    Output("hidden_div_for_redirect_callback", "children"),
    Input('my-boolean-switch', 'on')
)
def update_output(on):
    #print('The switch is {}.'.format(on))
    if on:
        return dcc.Location(href="http://3.85.240.70:5000", id="noone_cares")




if __name__ == "__main__":
    app.run_server(host= "0.0.0.0",debug=True)
