import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from app import app

#ganlib Imports
from .ganlib.processing import Processing
from .ganlib.dcgan import Generator

#AWS Imports
import boto3
from botocore.client import Config

s3 = boto3.resource("s3")
client_s3 = boto3.client('s3')
client_db = boto3.client('dynamodb')
config = Config(connect_timeout=5, read_timeout=5)


def update_model_selection():

    models = []
    objs = client_s3.list_objects_v2(Bucket="gan-dashboard", Prefix="models/generator/")

    for i in objs["Contents"]:
        tags = client_s3.get_object_tagging(Bucket='gan-dashboard',Key=i["Key"])["TagSet"]
        for tag in tags:
            if(tag["Key"] == "name"):
                models.append({"label": tag["Value"], "value": tag["Value"]})

    return models


def get_input_output(model):

    tags = client_s3.get_object_tagging(Bucket='gan-dashboard',Key="models/generator/{0}.pth".format(model))["TagSet"]
    for tag in tags:
        if(tag["Key"] == "z_dim"):
            z_dim = tag["Value"]
        elif(tag["Key"] == "data_dim"):
            data_dim = tag["Value"]

    return int(z_dim),int(data_dim)


layout = html.Div([

    # navbar
    dbc.Navbar(
        dbc.Container([

            dbc.NavbarToggler(id="navbar-toggler"),
            dbc.Collapse(
                dbc.Nav([
                    dbc.NavItem(dbc.NavLink("Home", href="/")),
                    dbc.NavItem(dbc.NavLink("Training", href="/training")),
                    dbc.NavItem(dbc.NavLink("Results", href="/results"), active=True),
                ], navbar=True),
                id="navbar-collapse",
                navbar=True,
            ),
        ],style={'max-width':'98%'}),
        color="light",
    ),

    html.Div([
        # page title
        dbc.Row(dbc.Col([html.H3('Generated Data Insights')],style={'padding':'35px 0 0px 0','margin-left':'-20px'},width=12)),
        
        # Page Content
        dbc.Row([
            dbc.Col([
                html.P('Name:',style={'align-items':'center','padding-top':'20px'})
            ],width=1),
            dbc.Col([
                dcc.Dropdown(
                    options=update_model_selection(),
                    value='default_gan',
                    id='choose_model',
                    clearable=False,
                    style={'margin':'15px 0'}
                ) 
            ],style={'margin-left':'-2vh'},width=2),

            dbc.Col([
                html.P('Epoch:',style={'padding':'20px 0 0 0'})
            ],style={"margin-left":"75px"},width=1),
            dbc.Col(id="epoch_display",style={'margin-left':'-2vh'},width=1),  

            dbc.Col([
                html.P('Generate:',style={'padding-top':'20px'})
            ],style={"margin-left":"75px"},width=1),

            dbc.Col([
                dbc.Button('Random',id='random_sample',className='success')
            ],style={'align-items':'center','padding-top':'15px'},width=2)
            
        ],style={'padding':'25px 0 50px 0'}),
            
        dbc.Row([
            dbc.Col([],id="epoch_image_name",width=5),
            dbc.Col([
                html.H5('Randomly Generated Image:',style={'align-items':'center','padding':'0 0 25px 0'})
            ],width=4)
        ]),
        dbc.Row([
            dbc.Col([
                html.Div([],id='data_insight',style={'margin-left': '100px'})                
            ],width=7),
            dbc.Col([
                html.Div([],id='generated_image',style={'margin-left': '50px'})                
            ],width=4)
        ]),
    ],style={'margin':'0 auto','width':'90%'}),    
])


# ======================================================================================================================
# =================================================== CALLBACKS ========================================================
# ======================================================================================================================
@app.callback(
    Output(component_id='data_insight', component_property='children'),
    [Input(component_id='choose_model',component_property='value'),
    Input(component_id='choose_epoch',component_property='value')],
    # [State(component_id='choose-dataset-value',component_property='value')]
)
def return_dataframe_random(model_name, epoch):
    
    return dbc.Container([
            dbc.Col(html.Img(src="https://gan-dashboard.s3.amazonaws.com/generated-images/{0}/{1}.jpeg".format(model_name,epoch)))
        ])


@app.callback(
    Output(component_id='epoch_display',component_property='children'),
    [Input(component_id='choose_model',component_property='value')]
)
def return_epoch_list(dataset):

    objs = client_s3.list_objects_v2(Bucket="gan-dashboard", Prefix="generated-images/{0}/".format(dataset))
    epochs = []

    for i in range(1,len(objs["Contents"])+1):
        epochs.append({"label": i, "value": i})

    return dcc.Dropdown(
            options=epochs,
            value=1,
            id='choose_epoch',
            clearable=False,
            style={'margin':'15px 0'}
        )


@app.callback(
    Output(component_id='epoch_image_name',component_property='children'),
    [Input(component_id='choose_epoch',component_property='value')]
)
def return_epoch_image_name(epoch):

    return html.H5('Epoch {0}:'.format(epoch),style={'align-items':'center','padding':'0 0 25px 0'})


@app.callback(
    Output(component_id='generated_image', component_property='children'),
    [Input(component_id='random_sample',component_property='n_clicks'),
    Input(component_id='choose_model',component_property='value'),
    ]
)
def return_image_random(n,model_name):
    
    if n and model_name:

        input_dim, output_dim = get_input_output(model_name)
        model = Generator(input_dim,output_dim)
        model.load_state_dict(model_name)
        model.generate(100,model_name,save=True,temp=True)
            
        return dbc.Container([
            dbc.Col(html.Img(src="https://gan-dashboard.s3.amazonaws.com/temp/{0}.jpeg".format(model_name)))
        ])
    
    return dbc.Container([
            dbc.Col(html.Img(src="https://gan-dashboard.s3.amazonaws.com/temp/{0}.jpeg".format(model_name)))
        ])

