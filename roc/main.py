"""
This file demonstrates a bokeh applet, which can be viewed directly
on a bokeh-server. See the README.md file in this directory for
instructions on running.

ROC Curve example
=================

This example is a ROC curve where the data is generated to show
AUC (Area Under the Curve). The threshold may be set, and the
impact of the resultant confustion matrix will display in the
lower right corner.

Author: Brian Ray <brianhray@gmail.com>

"""

# this will not be needed in Bokeh 0.12
from os.path import dirname
import sys
sys.path.insert(0, dirname(__file__))

from pyroc import random_mixture_model, ROCData

from bokeh.io import curdoc
from bokeh.plotting.figure import Figure
from bokeh.models import ColumnDataSource, HBox, Slider, TextInput, VBoxForm

CACHED_DATA = {}


def random_roc_data(auc=.7, std_dev=.2, size=300):
    args = dict(
        pos_mu=auc,
        pos_sigma=std_dev,
        neg_mu=1-auc,
        neg_sigma=std_dev,
        size=size)
    arg_hash = hash(frozenset(args.items()))
    if arg_hash in CACHED_DATA:
        random_sample = CACHED_DATA[arg_hash]
    else:
        random_sample = random_mixture_model(**args)
    CACHED_DATA[arg_hash] = random_sample
    roc = ROCData(random_sample)
    roc.auc()
    roc_x = [x[0] for x in roc.derived_points]
    roc_y = [y[1] for y in roc.derived_points]
    return dict(x=roc_x, y=roc_y)


def get_collide():
    """Finds the point that collides in the 'x' direction with threshold"""
    data = zip(source.data['x'], source.data['y'])
    return min(data, key=lambda x: abs(x[0] - float(threshold.value)/100.0))


def conf_matrix():
    """Calculate the confusion Matrix"""
    P = len(source.data['x'])
    N = len(source.data['y'])
    TPR = point_source.data['y'][0]  # y axis sensitivity
    TNR = point_source.data['x'][0]  # x axis specificity
    TP = TPR * P  # True Positive
    TN = TNR * N  # True Negative
    FP = P - TP
    FN = N - TN
    return dict(TP=[int(TP)], FP=[int(FP)], FN=[int(FN)], TN=[int(TN)])


def input_change(attr, old, new):
    """Executes whenever the input form changes.

    It is responsible for updating the plot, or anything else you want.

    Args:
        obj : the object that changed
        attrname : the attr that changed
        old : old value of attr
        new : new value of attr
    """
    update_data()
    plot.title = text.value


def update_data():
    """Called each time that any watched property changes.

    This updates the roc curve with the most recent values of the
    sliders. This is stored as two numpy arrays in a dict into the app's
    data source property.
    """
    size = int(sample_size.value) / 2
    source.data = random_roc_data(auc=float(auc.value)/100.0, size=size)
    x, y = get_collide()
    point_source.data = dict(x=[x], y=[y])
    conf_source.data = conf_matrix()


source = ColumnDataSource(data=random_roc_data(size=200))

text = TextInput(title="title", name='title', value='ROC Curve')

sample_size = Slider(title="Sample Size (splits 50/50)", name='threshold',
                     value=400, start=50, end=800, step=2)

threshold = Slider(title="Threshold", name='threshold',
                   value=50.0, start=0.0, end=100.0, step=0.1)

auc = Slider(title="Area Under Curve (AUC)", name='auc',
             value=70.0, start=0.0, end=100.0, step=0.1)

# Generate a figure container
plot = Figure(title_text_font_size="12pt",
              plot_height=400,
              plot_width=400,
              tools="crosshair,pan,reset,resize,save,wheel_zoom",
              title=text.value,
              x_range=[0, 1],
              y_range=[0, 1])

# Plot the line by the x,y values in the source property
plot.line('x', 'y', source=source, line_width=3, line_alpha=0.6)

# Plot the line by the x,y values in the source property
plot.line('xr', 'yr', source=ColumnDataSource(data=dict(xr=[0, 1], yr=[0, 1])),
          line_width=3, line_alpha=0.6, color="red")

x, y = get_collide()
point_source = ColumnDataSource(data=dict(x=[x], y=[y]))
plot.circle_cross('x', 'y', source=point_source, color="blue")

conf_source = ColumnDataSource(data=conf_matrix())

text_props = {"source": conf_source,
              "angle": 0,
              "text_font": "Courier",
              "text_font_size": "8pt",
              "color": "grey",
              "text_align": "left",
              "text_baseline": "middle"}

label_props = dict(text_props)
del label_props['source']
label_props['text_font_size'] = "5pt"

# the confusion matrix
plot.text(x=0.825, y=0.21, text=["True"], **label_props)
plot.text(x=0.925, y=0.21, text=["False"], **label_props)
plot.text(x=0.825, y=0.15, text="TP", **text_props)
plot.text(x=0.925, y=0.15, text="FP", **text_props)
plot.text(x=0.725, y=0.15, text=["True"], **label_props)
plot.text(x=0.725, y=0.05, text=["False"], **label_props)
plot.text(x=0.825, y=0.05, text="FN", **text_props)
plot.text(x=0.925, y=0.05, text="TN", **text_props)

update_data()

text.on_change('value', input_change)

for w in [threshold, text, auc, sample_size]:
    w.on_change('value', input_change)

inputs = VBoxForm(children=[text, sample_size, threshold, auc])

curdoc().add_root(HBox(children=[inputs, plot], width=800))
