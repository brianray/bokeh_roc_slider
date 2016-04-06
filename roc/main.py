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

Author(s): Brian Ray <brianhray@gmail.com>, 
           Bryan Van de Ven <bryanv@continuum.io>

"""

# this will not be needed in 0.12
from os.path import dirname
import sys
sys.path.insert(0, dirname(__file__))

import logging

from pyroc import random_mixture_model, ROCData

from bokeh.io import curdoc
from bokeh.plotting.figure import Figure
from bokeh.models import (ColumnDataSource,
                          HBox,
                          Slider,
                          TextInput,
                          VBoxForm,
                          CustomJS)

HAS_REQUESTS = False
try:
    import requests
    HAS_REQUESTS = True
except:
    logging.warn("install 'requests' package for json fetching")

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
    P = len(source.data['x']) / 2.0
    N = len(source.data['y']) / 2.0
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
        attr : the name of the attr that changed
        old : old value of attr
        new : new value of attr
    """
    update_data()
    plot.title = text.value

source_url = ColumnDataSource()

def dataurl_change(attr, old, new):
    if new != "DEMO":
        try:
            source_url.data = requests.get(new).json()
            inputs = VBoxForm(text, threshold, dataurl)
            curdoc().remove_root(plot)
            curdoc().add_root(HBox(inputs, plot, width=800))
        except:
            logging.warn("unable to fetch {}".format(new))
    update_data()


def update_data():
    """Called each time that any watched property changes.

    This updates the roc curve with the most recent values of the
    sliders. This is stored as two numpy arrays in a dict into the app's
    data source property.
    """
    size = int(sample_size.value) / 2
    if source_url.data == {}:
        source.data = random_roc_data(auc=float(auc.value)/100.0, size=size)
    else:
        source.data = source_url.data
        for w in [threshold, text, auc, sample_size]:
            w.disabled = True
    x, y = get_collide()
    point_source.data = dict(x=[x], y=[y])
    conf_source.data = conf_matrix()


source = ColumnDataSource(data=random_roc_data(size=200))

text = TextInput(title="title", name='title', value='ROC Curve')
sample_size = Slider(title="Sample Size (splits 50/50)", value=400, start=50, end=800, step=2)
threshold = Slider(title="Threshold", value=50.0, start=0.0, end=100.0, step=0.1)
auc = Slider(title="Area Under Curve (AUC)", value=70.0, start=0.0, end=100.0, step=0.1)
dataurl = TextInput(title="Data Url", name='data', value='DEMO')

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

text_props = {"text_font": "Courier",
              "text_align": "left",
              "text_baseline": "middle"}

# the confusion matrix
text_props['text_font_size'] = "5pt"
plot.text(x=0.825, y=0.21, text=["True"], **text_props)
plot.text(x=0.925, y=0.21, text=["False"], **text_props)
plot.text(x=0.725, y=0.15, text=["True"], **text_props)
plot.text(x=0.725, y=0.05, text=["False"], **text_props)

text_props['text_font_size'] = "8pt"
plot.text(x=0.825, y=0.15, text="TP", source=conf_source, **text_props)
plot.text(x=0.925, y=0.15, text="FP", source=conf_source, **text_props)
plot.text(x=0.825, y=0.05, text="FN", source=conf_source, **text_props)
plot.text(x=0.925, y=0.05, text="TN", source=conf_source, **text_props)

update_data()

text.on_change('value', input_change)
dataurl.on_change('value', dataurl_change)

# There must be a better way:
dataurl.callback = CustomJS(args=dict(auc=auc,
                                      sample_size=sample_size),
                            code="""
         // $("label[for='"+auc.id+"']").parentNode.remove();
         document.getElementById(auc.id).parentNode.hidden = true;
         // $("label[for='"+sample_size.id+"']").parentNode.remove();
         document.getElementById(sample_size.id).parentNode.hidden = true;
    """)

for w in (threshold, text, auc, sample_size):
    w.on_change('value', input_change)

vbox_items = [text, sample_size, threshold, auc]
if HAS_REQUESTS:
    vbox_items.append(dataurl)
inputs = VBoxForm(*vbox_items)

curdoc().add_root(HBox(inputs, plot, width=800))
