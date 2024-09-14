"""
Author: Casey Zandbergen III
Date: 7/20/2023
Description: This program creates a Dash app that reads
in data from a csv file and displays it in a plotly graph.
The UI allows the user to overlay various dyno runs along,
any changes made to the files in the data directory will automatically
update in the UI.
"""
import datetime
import os
from dash import Dash, html, dcc, Input, Output, no_update, State
import pandas as pd
import plotly.graph_objects as go


def plot_data(file: str) -> go.Figure:
    """
    Takes in a csv file and returns a plotly figure of the data.
    Parameters: file (str): path to csv file
    Returns: fig (go.Figure): plotly figure
    """

    # read in data
    dyno_df = pd.read_csv(file)

    # get rpm dataframe
    rpm_df = dyno_df["RPM"]
    # get torque dataframe
    torque_df = dyno_df["Torque (ft-lbs)"]
    # get horsepower dataframe
    hp_df = dyno_df["Horsepower"]
    # create figure
    fig = go.Figure()

    # plot torque curve
    fig.add_trace(
        go.Scatter(x=rpm_df, y=torque_df, mode="lines", name="Torque (ft-lbs)")
    )

    # plot horsepower curve
    fig.add_trace(go.Scatter(x=rpm_df, y=hp_df, mode="lines", name="HP"))

    return fig


def get_current_datetime() -> str:
    """
    Get the current date and time
    Returns: formatted_date (str): formatted date and time
    """
    now = datetime.datetime.now()
    formatted_date = now.strftime("%m/%d/%Y")
    formatted_time = now.strftime("%H:%M:%S")

    return f"{formatted_date} {formatted_time}"


def get_files_in_directory(path) -> list:
    """
    Get list of files within directory, filtered by .csv extension
    Parameters: path (str): path to directory
    Returns: csv_files (list): list of files with .csv extension
    """

    # get the list of files in the specified directory
    files_list = os.listdir(path)

    # filter only the files with ".csv" extension
    csv_files = [file for file in files_list if file.endswith(".csv")]

    # return the list of files with .csv extension
    return csv_files


# initialize the directory path where your files are located
directory_path = "dyno-interface\dyno-interface\data"

# get the list of files from the specified directory (dyno runs)
files = get_files_in_directory(directory_path)

# load data
dyno_graph = plot_data(directory_path + "/" + files[0])

# initialize Dash app
app = Dash(__name__)

# format app layout
app.layout = html.Div(
    [
        # header
        html.Div(
            [
                html.H1(
                    "Dyno Interface",
                    style={
                        "color": "snow",
                        "text-align": "center",
                        "margin-bottom": 0,
                        "font-family": "open sans",
                    },
                ),
            ]
        ),
        # date and time
        html.Div(
            [
                dcc.Interval(id="interval-component", interval=1000, n_intervals=0),
                html.H2(
                    id="live-datetime",
                    style={
                        "color": "snow",
                        "text-align": "center",
                        "font-family": "open sans",
                    },
                ),
            ]
        ),
        # dyno graph
        html.Div(
            dcc.Graph(
                id="dyno-graph",
                figure=dyno_graph,
                style={
                    "height": "60vh",
                    "margin-top": 0,
                },
            )
        ),
        # timing method
        html.Div(
            html.H3(
                "Timing Method",
                style={
                    "color": "snow",
                    "text-align": "left",
                    "margin-bottom": 0,
                    "text-decoration": "underline",
                    "font-family": "open sans",
                },
            )
        ),
        # timing method radio buttons
        html.Div(
            dcc.RadioItems(
                [
                    # cam position sensor radio button
                    {
                        "label": [
                            html.Span(
                                "Cam Position Sensor",
                                style={
                                    "color": "snow",
                                    "padding-left": 10,
                                    "font-family": "open sans",
                                },
                            ),
                        ],
                        "value": "cam-position-sensor",
                    },
                    # wasted spark radio button
                    {
                        "label": [
                            html.Span(
                                "Wasted Spark",
                                style={
                                    "color": "snow",
                                    "padding-left": 10,
                                    "font-family": "open sans",
                                },
                            )
                        ],
                        "value": "wasted-spark",
                    },
                ],
                labelStyle={
                    "display": "flex",
                    "align-items": "center",
                    "padding-top": 10,
                },
                value="cam-position-sensor",
            )
        ),
        # dyno controls
        html.Div(
            [
                # run button
                html.Button(
                    "Record",
                    id="record-button",
                    className="button-primary",
                ),
            ],
            style={
                "position": "absolute",
                "bottom": "11.5%",
                "left": "30%",
                "font-family": "open sans",
            },
        ),
        # files dropdown
        html.Div(
            [
                dcc.Dropdown(
                    files,
                    id="files-dropdown",
                    multi=True,
                    placeholder="Select a file",
                ),
                html.Div(id="dd-output-container"),
            ],
            style={
                "position": "absolute",
                "bottom": "12%",
                "left": "37%",
                "width": "20%",
                "font-family": "open sans",
            },
        ),
    ],
)


# callback to update the date and time
@app.callback(
    Output("live-datetime", "children"), [Input("interval-component", "n_intervals")]
)
def update_datetime(*_):
    """
    Get the current date and time and Display it in the app
    Returns: current_datetime (str): formatted date and time
    """
    current_datetime = get_current_datetime()
    return current_datetime


# callback to update the graph based on the selected files from the files-dropdown
@app.callback(Output("dyno-graph", "figure"), [Input("files-dropdown", "value")])
def update_graph(selected_files):
    """
    Update the graph based on the selected files from the files-dropdown
    Parameters: selected_files (list): list of selected files
    Returns: fig (go.Figure): plotly figure
    """

    # if no files are selected, return no_update
    if selected_files is None:
        return no_update

    # create a new figure
    fig = go.Figure()

    # for each selected file, generate the plot and add the data traces to the main figure
    for selected_file in selected_files:
        # construct the full path to the selected file
        file_path = os.path.join(directory_path, selected_file)

        # generate the plot for the selected file using the plot_data function
        file_fig = plot_data(file_path)

        # add the data traces of the current file to the main figure
        for trace in file_fig["data"]:
            # Add the file name as a suffix to the trace name
            trace_name = f"{trace['name']} - {selected_file}"
            trace["name"] = trace_name
            fig.add_trace(trace)

    # update the layout to retain the original formatting
    fig.update_layout(
        # format x-axis
        xaxis_title="RPM",
        xaxis_dtick=1000,
        xaxis_tickformat=",.0f",
        xaxis_tickangle=45,
        xaxis_gridcolor="gray",
        xaxis_color="snow",
        # format y-axis
        yaxis_title="HP/Torque",
        yaxis_dtick=10,
        yaxis_color="snow",
        yaxis_gridcolor="gray",
        # format template
        template="plotly_dark",
        # format legend
        legend_borderwidth=1.5,
        legend_bordercolor="snow",
        # format plot and paper background
        plot_bgcolor="rgb(50, 50, 50)",
        paper_bgcolor="rgb(50, 50, 50)",
    )

    # check the number of selected files
    num_files_selected = len(selected_files)

    # if only one file is selected, add annotations for max horsepower and max torque
    if num_files_selected == 1:
        # read in the selected file
        df = pd.read_csv(os.path.join(directory_path, selected_files[0]))
        # get the max horsepower
        max_hp = df["Horsepower"].max()
        # get the rpm value for the max horsepower
        max_hp_rpm = df.loc[df["Horsepower"].idxmax(), "RPM"]

        # get the max torque
        max_torque = df["Torque (ft-lbs)"].max()
        # get the rpm value for the max torque
        max_torque_rpm = df.loc[df["Torque (ft-lbs)"].idxmax(), "RPM"]

        # add annotations for max horsepower
        fig.add_annotation(
            x=max_hp_rpm,
            y=max_hp,
            text=f"Max HP: {round(max_hp, 1)}<br>RPM: " + "{:,}".format(max_hp_rpm),
            showarrow=True,
            arrowhead=2,
            bordercolor="snow",
            borderwidth=1.5,
            borderpad=4,
        )

        # add annotations for max torque
        fig.add_annotation(
            x=max_torque_rpm,
            y=max_torque,
            text=f"Max Torque: {round(max_torque, 1)} ft/lbs<br>RPM: "
            + "{:,}".format(max_torque_rpm),
            showarrow=True,
            arrowhead=2,
            bordercolor="snow",
            borderwidth=1.5,
            borderpad=4,
        )
    else:
        # if more than one file is selected, remove existing annotations
        fig.update_layout(annotations=[])

    # return the updated figure
    return fig


# callback to update the record button label when it's clicked
@app.callback(
    Output("record-button", "children"),
    [Input("record-button", "n_clicks")],
    [State("record-button", "children")],
)
def update_record_button_label(n_clicks, current_label):
    """
    Update the record button label when the record/stop button is clicked.
    Parameters:
        n_clicks (int): number of times the button is clicked.
        current_label (str): current button label.
    Returns:
        label (str): Updated button label.
    """
    if n_clicks is None:
        # default label
        return "Record"

    # check button state
    is_recording = current_label == "Stop"

    if is_recording:
        # if stop button was clicked, display "Record"
        return "Record"
    else:
        # if record button was clicked, display "Stop"
        return "Stop"


@app.callback(
    Output("files-dropdown", "options"), [Input("interval-component", "n_intervals")]
)
def update_dropdown_options(*_):
    """
    Update the files-dropdown when any change in the data directory
    occurs.
    """
    # check the current last modification time of the directory
    current_modification_time = os.path.getmtime(directory_path)

    # if the modification time is different from the last known one, update the options
    if current_modification_time != update_dropdown_options.last_modification_time:
        update_dropdown_options.last_modification_time = current_modification_time
        updated_files = get_files_in_directory(directory_path)
        dropdown_options = [{"label": file, "value": file} for file in updated_files]
        return dropdown_options

    # if the modification time is the same, return no_update to prevent unnecessary updates
    return no_update


# initialize the attribute to store the last modification time
update_dropdown_options.last_modification_time = os.path.getmtime(directory_path)


if __name__ == "__main__":
    app.run_server(debug=True)
