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

import logging

logging.basicConfig(level=logging.DEBUG)

import copy
import numpy as np
from pyroc import random_mixture_model, ROCData

from bokeh.plotting import figure, show, output_notebook
from bokeh.models import Plot, ColumnDataSource
from bokeh.properties import Instance
from bokeh.server.app import bokeh_app
from bokeh.server.utils.plugins import object_page
from bokeh.models.widgets import HBox, Slider, TextInput, VBoxForm


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


class RocPlot(HBox):
    """An example of a browser-based, interactive plot with slider controls."""

    extra_generated_classes = [["RocPlot", "RocPlot", "HBox"]]

    inputs = Instance(VBoxForm)

    text = Instance(TextInput)

    sample_size = Instance(Slider)

    threshold = Instance(Slider)

    auc = Instance(Slider)

    plot = Instance(Plot)
    source = Instance(ColumnDataSource)
    point_source = Instance(ColumnDataSource)
    conf_source = Instance(ColumnDataSource)

    @classmethod
    def create(cls):
        """One-time creation of app's objects.

        This function is called once, and is responsible for
        creating all objects (plots, datasources, etc)
        """
        obj = cls()

        obj.source = ColumnDataSource(data=random_roc_data(size=200))

        obj.text = TextInput(
            title="title", name='title', value='ROC Curve'
        )
        obj.sample_size = Slider(
            title="Sample Size (splits 50/50)", name='threshold',
            value=400, start=50, end=800, step=2
        )
        obj.threshold = Slider(
            title="Threshold", name='threshold',
            value=50.0, start=0.0, end=100.0, step=0.1
        )
        obj.auc = Slider(
            title="Area Under Curve (AUC)", name='auc',
            value=70.0, start=0.0, end=100.0, step=0.1
        )
        
        #        threshold=widgets.FloatSliderWidget(min=0.0, max=100.0, step=0.1, value=50.0),
        #        auc=widgets.FloatSliderWidget(min=0.0, max=100.0, step=0.1, value=0.0))
        toolset = "crosshair,pan,reset,resize,save,wheel_zoom"

        # Generate a figure container
        plot = figure(title_text_font_size="12pt",
                      plot_height=400,
                      plot_width=400,
                      tools=toolset,
                      title=obj.text.value,
                      x_range=[0, 1],
                      y_range=[0, 1])

        # Plot the line by the x,y values in the source property
        plot.line('x', 'y', source=obj.source,
                  line_width=3,
                  line_alpha=0.6)
        # Plot the line by the x,y values in the source property
        plot.line('xr', 'yr', source=ColumnDataSource(data=dict(xr=[0, 1], yr=[0, 1])),
                  line_width=3,
                  line_alpha=0.6, color="red")
        obj.plot = plot

        x, y = obj.get_collide()
        obj.point_source = ColumnDataSource(data=dict(x=[x], y=[y]))
        plot.circle_cross('x', 'y', source=obj.point_source, color="blue")

        obj.conf_source = ColumnDataSource(data=obj.conf_matrix())
        text_props = {"source": obj.conf_source,
                      "angle": 0,
                      "text_font": "Courier",
                      "text_font_size": "8pt",
                      "color": "grey",
                      "text_align": "left",
                      "text_baseline": "middle"}
        label_props = copy.copy(text_props)
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

        obj.update_data()
        obj.inputs = VBoxForm(
            children=[
                obj.text,
                obj.sample_size,
                obj.threshold,
                obj.auc
            ]
        )

        obj.children.append(obj.inputs)
        obj.children.append(obj.plot)

        return obj

    def setup_events(self):
        """Attaches the on_change event to the value property of the widget.

        The callback is set to the input_change method of this app.
        """
        super(RocPlot, self).setup_events()
        if not self.text:
            return

        # Text box event registration
        self.text.on_change('value', self, 'input_change')

        # Slider event registration
        for w in ["threshold", "text", "auc", "sample_size"]:
            getattr(self, w).on_change('value', self, 'input_change')

    def get_collide(self):
        """Finds the point that collides in the 'x' direction with threshold"""
        threshold = self.threshold.value
        data = zip(self.source.data['x'], self.source.data['y'])
        return min(data, key=lambda x: abs(x[0] - float(threshold)/100.0))

    def conf_matrix(self):
        """Calculate the confusion Matrix"""
        P = len(self.source.data['x'])
        N = len(self.source.data['y'])
        TPR = self.point_source.data['y'][0]  # y axis sensitivity
        TNR = self.point_source.data['x'][0]  # x axis specificity
        TP = TPR * P  # True Possitive
        TN = TNR * N  # True Negative
        FP = P - TP
        FN = N - TN
        return dict(TP=[int(TP)], FP=[int(FP)], FN=[int(FN)], TN=[int(TN)])

    def input_change(self, obj, attrname, old, new):
        """Executes whenever the input form changes.

        It is responsible for updating the plot, or anything else you want.

        Args:
            obj : the object that changed
            attrname : the attr that changed
            old : old value of attr
            new : new value of attr
        """
        self.update_data()
        self.plot.title = self.text.value

    def update_data(self):
        """Called each time that any watched property changes.

        This updates the roc curve with the most recent values of the
        sliders. This is stored as two numpy arrays in a dict into the app's
        data source property.
        """
        auc = self.auc.value
        size = int(self.sample_size.value) / 2
        self.source.data = random_roc_data(auc=float(auc)/100.0, size=size)
        x, y = self.get_collide()
        self.point_source.data = dict(x=[x], y=[y])
        self.conf_source.data = self.conf_matrix()


class RocPlotNotebook(object):
    ''' proxy for RocPlot for embeding in Jupyter notebooks '''


    def __init__(self, data=None, args=None):  
        ''' if no `data` provided, will run in demo mode'''
        output_notebook()
        roc_obj = RocPlot()
        self.demo = True
        if data:
            roc_obj.source = ColumnDataSource(data=data)
            self.demo = False
        self.app = roc_obj.create()
        show(self.app.plot)


    def interact_callback(self, **kwargs): #sample_size, threshold, auc):
        ''' callback from interact_widgets '''
        self.app.threshold.value = kwargs.get('threshold')  
        if self.demo:
            self.app.sample_size.value = kwargs.get('sample_size')
            self.app.auc.value = kwargs.get('auc')
            self.app.update_data()
            self.app.source.push_notebook()
        else:
            # just handle updates to threshold
            x, y = self.app.get_collide()
            self.app.point_source.data = dict(x=[x], y=[y])
            self.app.conf_source.data = self.app.conf_matrix()
        # always update point and confusion matrix
        self.app.point_source.push_notebook()
        self.app.conf_source.push_notebook()
        
    def interact_widgets(self, args=None):
        ''' shows widgets in Jupyter notebook'''
        import warnings
        warnings.simplefilter(action = "ignore", category = FutureWarning)
        from IPython.html import widgets
        if not args:
            args = dict(threshold=widgets.FloatSlider(min=0.0, max=100.0, step=0.1, value=50.0))
        if self.demo:
            args['auc'] = widgets.FloatSlider(min=0.0, max=100.0, step=0.1, value=70.0)
            args['sample_size'] = widgets.IntSlider(min=0, max=800, step=2, value=400)
        widgets.interact(self.interact_callback, **args)
    
    
        
# The following code adds a "/bokeh/roc_slider/" url to the bokeh-server. This
# URL will render this sine wave sliders app. If you don't want to serve this
# applet from a Bokeh server (for instance if you are embedding in a separate
# Flask application), then just remove this block of code.
@bokeh_app.route("/bokeh/roc_slider/")
@object_page("sin")
def make_sliders():
    app = RocPlot.create()
    return app
