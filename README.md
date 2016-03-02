# bokeh_roc_slider
Receiver operating characteristic chart in Bokeh

This example shows how to create a simple applet in Bokeh, which can
be viewed directly on a bokeh-server.


![screen shot](https://github.com/brianray/bokeh_roc_slider/screenshot.png "Screenshot")


Running
=======

To view this applet directly from a bokeh server, you simply need to
run a bokeh-server and point it at the stock example script:

    bokeh-server --script src/slider_roc_app.py

Now navigate to the following URL in a browser:

    http://localhost:5006/bokeh/roc_slider
