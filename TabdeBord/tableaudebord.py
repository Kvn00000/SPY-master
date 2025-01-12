import requests
from requests.auth import HTTPBasicAuth
import json
from datetime import datetime
from urllib.parse import urljoin
from datetime import datetime

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import numpy as np 
import ast

# LRS Configuration
LRS_ENDPOINT = "https://lrsels.lip6.fr/data/xAPI"
LRS_USERNAME = "9fe9fa9a494f2b34b3cf355dcf20219d7be35b14"
LRS_PASSWORD ="b547a66817be9c2dbad2a5f583e704397c9db809"
XAPI_VERSION = "1.0.3"

# Headers
headers = {
    "X-Experience-API-Version": XAPI_VERSION,
    "Content-Type": "application/json"
}

# Streaming asset path
streaming_asset_path = "Assets/StreamingAssets/"

# Store session data
launched_data = []
completed_data = []
inserted_data = []
scores = []

with open("scores_file.txt") as f:
    scores_per_level = f.read().splitlines()
    nb_of_levels = len(scores_per_level)

dico_scores = dict()
for line in scores_per_level:

    level, score = line.split(' : ')
    level = level.replace("\\\\","\\")

    dico_scores[level.replace('\\','/')] = ast.literal_eval(score)

# Function to process the LRS response
def process_lrs_response(response_json, data_store):
    statements = response_json.get("statements", [])
    data_store.extend(statements)

    # Check for pagination
    more_url = response_json.get("more", None)
    if more_url:
        print("Fetching more data...")
        full_more_url = urljoin(LRS_ENDPOINT, more_url)
        more_response = requests.get(
            full_more_url,
            auth=HTTPBasicAuth(LRS_USERNAME, LRS_PASSWORD),
            headers=headers
        )
        if more_response.status_code == 200:
            process_lrs_response(more_response.json(), data_store)
        else:
            print(f"Error fetching more data: {more_response.status_code} - {more_response.text}")

# Fetch data based on a specific verb
def fetch_data(verb, session_name):
    query_params = {
    "agent": json.dumps({
        "account": {
            "homePage": "https://www.lip6.fr/mocah/",
            "name":session_name
            #"name":"3D37C851"
        }
    }),
    # check vocabulary lrs
    "verb": verb,
    #"limit": 200
}
    response = requests.get(
        f"{LRS_ENDPOINT}/statements",
        auth=HTTPBasicAuth(LRS_USERNAME, LRS_PASSWORD),
        params=query_params,
        headers=headers
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to query LRS: {response.status_code} - {response.text}")
        return None

def update_temps_mini_to_user(user_id):

    """
    Va récupérer pour chaque niveau, le temps minimal effectué à ce niveau
    """
    a = fetch_data('http://adlnet.gov/expapi/verbs/launched', user_id)
    b = fetch_data('http://adlnet.gov/expapi/verbs/completed', user_id)

    process_lrs_response(a, launched_data)
    process_lrs_response(b, completed_data)

    temps_mini = dict()
    all_times_per_level = dict()
    obtained_scores = dict()

    format_str = "%Y-%m-%dT%H:%M:%S.%fZ"

    for i in range(len(launched_data)): 
        niveau = launched_data[i]['object']['definition']['extensions']['https://spy.lip6.fr/xapi/extensions/value'][0]
        t1 = launched_data[i]['timestamp'][:-2] + "Z"
        t2 = completed_data[i]['timestamp'][:-2] + "Z"
        dt1 = datetime.strptime(t1, format_str)
        dt2 = datetime.strptime(t2, format_str)
        delta = dt2 - dt1
        diff = str(delta).split(".")[0]
        delta_secs = delta.total_seconds()

        if niveau not in temps_mini.keys():
            temps_mini[niveau] = delta_secs
            all_times_per_level[niveau] = [delta_secs]
            obtained_scores[niveau] = [int(completed_data[i]["result"]["extensions"]["https://spy.lip6.fr/xapi/extensions/score"][0])]


        else:
            if delta_secs < temps_mini[niveau]:
                temps_mini[niveau] = delta_secs
            all_times_per_level[niveau].append(delta_secs)
            obtained_scores[niveau].append(int(completed_data[i]["result"]["extensions"]["https://spy.lip6.fr/xapi/extensions/score"][0]))

    return temps_mini, all_times_per_level, obtained_scores

def update_inserted_to_user(user_id):

    """
    Récupère tous les blocs insérés de l'utilisateur pour en déterminer le "bloc le plus joué" et le "bloc le moins joué"
    """
    a = fetch_data('https://spy.lip6.fr/xapi/verbs/inserted', user_id)

    process_lrs_response(a, inserted_data)

    inserted = dict()


    for i in range(len(inserted_data)): 
        block = inserted_data[i]['object']['definition']['extensions']['https://spy.lip6.fr/xapi/extensions/content'][0].rstrip(';')
        if block not in inserted.keys():
            inserted[block] = 0

        else:
            inserted[block] += 1

    return inserted



learners_ids = ['6DFE62E7']

# Récupère les données de l'utilisateur
lid = learners_ids[0]
temps_mini, all_times_per_level, scores = update_temps_mini_to_user(lid)
all_times_per_level = dict([(k, v[::-1]) for (k,v) in all_times_per_level.items()])

inserted = update_inserted_to_user(lid)
selected_level = ''
max_key = max(inserted, key=inserted.get)
min_key = min(inserted, key=inserted.get)



nb_of_stars = 0
for level in dico_scores.keys():
    if level in scores.keys():
        twoStars, threeStars = dico_scores[level].values()
        maxScore = max(scores[level])
        if maxScore >= int(threeStars):
            nb_of_stars += 3
        elif maxScore >= int(twoStars):
            nb_of_stars += 2
        else:
            nb_of_stars += 1


# Exemple de données pour les 20 derniers niveaux joués (à adapter en fonction des vraies données)
last_played_levels = []

for level in list(scores.keys())[-20:]:
    twoStars, threeStars = dico_scores[level].values()
    maxScore = max(scores[level])
    if maxScore >= int(threeStars):
        last_played_levels.append({"Nom du niveau": level, "Nombre d'étoiles": 3, "Score max": max(scores[level])})
    elif maxScore >= int(twoStars):
        last_played_levels.append({"Nom du niveau": level, "Nombre d'étoiles": 2, "Score max": max(scores[level])})
    else:
        last_played_levels.append({"Nom du niveau": level, "Nombre d'étoiles": 1, "Score max": max(scores[level])})





# Ajout du calcul du nombre de niveaux avec 3 étoiles
def count_levels_with_three_stars():
    three_stars_count = 0
    for level in dico_scores.keys():
        if level in scores.keys():
            _, threeStars = dico_scores[level].values()
            maxScore = max(scores[level])
            if maxScore >= int(threeStars):
                three_stars_count += 1
    return three_stars_count

    # Compter le nombre de niveaux avec 3 étoiles
three_stars_count = count_levels_with_three_stars()


# Fonction pour compter les tentatives réussies et ratées pour un niveau
def count_attempts(level):
    successful_attempts = 0
    failed_attempts = 0

    if level in scores.keys():
        _, threeStars = dico_scores[level].values()
        for score in scores[level]:
            if score >= int(threeStars):  # Si le score atteint 3 étoiles, c'est une réussite
                successful_attempts += 1
            else:  # Sinon, c'est un échec
                failed_attempts += 1

    return successful_attempts, failed_attempts







app = dash.Dash(__name__)

app.layout = html.Div([
    
    # La barre en haut pour changer d'apprenant (non fonctionnelle, il nous faudrait quelque chose pour gérer dynamiquement les données), ou, tout "fetch"
    # à chaque fois, mais ça serait trop gourmand en ressources
    html.Div([
        html.H4("Sélection de l'apprenant"),
        dcc.Dropdown(
            id="learner-id-selector",
            options=learners_ids,
            value=''
        ),
        html.Div(id='selected-learner', style={"marginTop": "20px", "fontSize": "20px"})
    ]),


    html.Div([
        html.Div([
            html.Div([
                html.Div([
                    # Sur la fenêtre avec le graphique, permet de sélectionner un niveau déjà effectué à analyser
                    html.H4("Sélecteur de niveau"),
                        dcc.Dropdown(
                        id="level-selector",
                        options=[{"label": key, "value": key} for key in temps_mini.keys()],
                        value="",  # Valeur par défaut
                        ),
                        html.Div(id="selected-value", style={"marginTop": "20px", "fontSize": "20px"}),
                        html.Div(id="attempt-stats", style={"margin-top": "20px"}),
                        ],
                        style={"width":"70%"}),

                # Score moyen obtenu pour un niveau répété plusieurs fois
                html.Div([
                    
                    html.Div(id="displayed-stars", style={
                        "margin-bottom":"20px"
                    }),
                    html.Div(id="displayed-score-div")
                    ],
                id="stars-div",
                style={
                    "display":"flex",
                    "flex-direction":"column",
                    "align-items":"center",
                    "width":"30%"
                })


        ], style={
            "display": "flex",
            "flex-direction": "row",
        }),  # Sélecteur à droite
        html.Div(id="times-graph-level")
            ] , style={
            "width": "50%",
            "display": "flex",
            "flex-direction": "column",
            "verticalAlign": "top",
            "padding": "20px",
            "border": "1px solid #ccc",
            "borderRadius": "5px",
        }),

        

        # Partie droite du tableau de bord
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                    # Statistiques "fun" (bloc le plus joué / bloc le moins joué / nombre d'étoiles obtenus sur nombre d'étoiles total)
                    html.P("Bloc le plus joué"),
                    html.Img(
                        src=f"assets/blocs/{max_key}.png",
                        style={"width":"25%"}
                    )
                ],
                style={"border":"1px solid #ccc", "border-radius":"20px", "padding-bottom":"5px", "display":"flex", "flex-direction":"column", "align-items":"center", "margin-bottom": "10px"}),

                html.Div([
                    html.P("Bloc le moins joué"),
                    html.Img(
                        src=f"assets/blocs/{min_key}.png",
                        style={"width":"25%"}

                    )
                ],
            style={"border":"1px solid #ccc", "border-radius":"20px", "padding-bottom":"5px", "display":"flex", "flex-direction":"column", "align-items":"center"})
            ],
            style={"margin-left": "20px", "height":"100%"}),
            html.Div([
                html.P("Nombre total d'étoiles obtenues : "),
                html.P(f"{nb_of_stars} ⭐/ {nb_of_levels * 3} ⭐", style={"font-size": "30px"})
            ],
            style={"display":"flex","flex-direction":"column","align-items":"center", "width": "80%","border":"1px solid #ccc", "margin-left": "10px", "border-radius": "20px"})], id="right-part-up", style={"display":"flex","flex-direction":"row","width":"100%"}),
            
            
            html.Div([
                html.P("Liste des 20 derniers niveaux joués"),
            dash_table.DataTable(
                id="last-played-table",
                columns=[
                    {"name": "Nom du niveau", "id": "Nom du niveau", "type": "text"},
                    {"name": "Nombre d'étoiles", "id": "Nombre d'étoiles", "type": "numeric"},
                    {"name": "Score max", "id": "Score max", "type": "numeric"}
                ],
                data=last_played_levels,  # Charger les données
                sort_action="native",  # Permettre le tri interactif
                style_cell={"textAlign": "center"},  # Centrer le texte
                style_table={"margin-top": "20px", "width": "100%", "margin-left" : "0px", "margin-right": "0px"},
                style_header={
                    "backgroundColor": "lightgrey",
                    "fontWeight": "bold",
                    "textAlign": "center"
                },
                style_data={
                    "whiteSpace": "normal",
                    "height": "auto"
                }
            )],
                
                id="right-part-bottom",
                style={
                    "display": "flex",
                    "flex-direction": "column",
                    "align-items": "center",
                    "border": "1px solid #ccc",
                    "margin-top": "20px",
                    "border-radius": "20px",
                    "padding": "10px"
                })], 
                id="right-part",
                style={
                    "width": "50%",
                    "margin-left": "auto",
                    "margin-right": "auto",
                    "padding": "20px"
                        
            })],
        style={"display":"flex", "flex-direction":"row"})]),

#


# Callback pour changer le temps minimal effectué pour un niveau lorsque l'on sélectionne un nouveau niveau
@app.callback(
    Output("selected-value", "children"),
    [Input("level-selector", "value")]
)
def display_selected_value(selected_level):
    if selected_level:
        
        return f"Temps minimum effectué pour ce niveau : {temps_mini[selected_level]} secondes"
    else:
        return f"N/A"

# Callback pour changer le nombre d'étoiles effectué pour un niveau lorsque l'on sélectionne un nouveau niveau
@app.callback(
    Output("displayed-stars", "children"),
    [Input("level-selector", "value")]
)
def update_stars(selected_level):
    if selected_level:
        twoStars, threeStars = dico_scores[selected_level].values()
        scoresForLevel = np.array(scores[selected_level])
        mean_score = scoresForLevel.mean()
        max_score = scoresForLevel.max()

        if max_score >= int(threeStars):
            nb_etoiles_max = 3
        elif max_score >= int(twoStars):
            nb_etoiles_max = 2
        else:
            nb_etoiles_max = 1 

        star_style = {"font-size": "30px", "color": "gold"}
        box_style = {"display":"flex","flex-direction":"column","align-items":"center"}
        if mean_score >= int(threeStars):
            return html.Div([
                html.H4("Score moyen obtenu pour ce niveau"),
                html.Div('⭐⭐⭐', style=star_style),
                html.P(f"{scoresForLevel.mean()}"),
                html.H4("Meilleur score obtenu pour ce niveau"),
                html.Div('⭐' * nb_etoiles_max, style=star_style),
                html.P(f"{scoresForLevel.max()}")

            ], style=box_style)

        elif mean_score >= int(twoStars):
            return html.Div([
                html.H4("Score moyen obtenu pour ce niveau"),
                html.Div('⭐⭐', style=star_style),
                html.P(f"{scoresForLevel.mean()}"),
                html.H4("Meilleur score obtenu pour ce niveau"),
                html.Div('⭐' * nb_etoiles_max, style=star_style),
                html.P(f"{scoresForLevel.max()}"),

            ], style=box_style)

        else:
            return html.Div([
                html.H4("Score moyen obtenu pour ce niveau"),
                html.Div('⭐', style=star_style),
                html.P(f"{scoresForLevel.mean()}"),
                html.H4("Meilleur score obtenu pour ce niveau"),
                html.Div('⭐' * nb_etoiles_max, style=star_style),
                html.P(f"{scoresForLevel.max()}"),
            ], style=box_style)

    else:
        return html.Div("")

@app.callback(
    Output("times-graph-level", "children"),
    [Input("level-selector", "value")]
)
def update_graph(selected_level):
    if selected_level:
        times = all_times_per_level[selected_level]
        g = dcc.Graph(
            figure={
                'data' : [
                    {'x': list(range(1, len(times) + 1)), 'y': times, 'type': 'bar'}
                ],
                'layout':{
                    'xaxis': {
                        'title': 'Numéro de tentative',
                        'tickmode' : 'linear',
                        'tick0' : 1,
                        'dtick' : 1,
                    },
                    'yaxis': {
                        'title': 'Temps (s)'
                    },
                    
                    'title' : f"Temps effectués pour le niveau {selected_level}"
                }
            }
        
        )
        return g
    
    else:
        fig = go.Figure()
        return dcc.Graph(figure=fig)







# Lancer l'application
if __name__ == "__main__":
    app.run_server(debug=True)
