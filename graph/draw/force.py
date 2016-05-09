"""Example of writing JSON format graph data and using the D3 Javascript library to produce an HTML/Javascript drawing.
"""
# Author: Aric Hagberg <aric.hagberg@gmail.com>

#    Copyright (C) 2011-2016 by
#    Aric Hagberg <hagberg@lanl.gov>
#    Dan Schult <dschult@colgate.edu>
#    Pieter Swart <swart@lanl.gov>
#    All rights reserved.
#    BSD license.
import os
import sys
import json
import networkx as nx
from networkx.readwrite import json_graph
import flask

# Serve the file over http to allow for cross origin requests
app = flask.Flask(__name__, static_folder="force")

@app.route("/")
def root():
    return app.send_static_file("force.html")
    
@app.route('/<path:path>')
def static_proxy(path):
  return app.send_static_file(path)
  
def draw_in_browser(G=None, p_port=8000):
    if G == None:
        G = nx.barbell_graph(6,3)
    elif type(G)==type('str'):
        G = nx.read_dot(G)
    else:
        assert isinstance(G, nx.Graph)
    # this d3 example uses the name attribute for the mouse-hover value,
    # so add a name to each node
    for n in G:
        G.node[n]['name'] = n
    # write json formatted data
    d = json_graph.node_link_data(G) # node-link format to serialize
    # write json
    json.dump(d, open(os.path.join(os.path.dirname(__file__), 'force/force.json'),'w'), indent=4)
    print('Wrote node-link JSON data to force/force.json')
    print('\nGo to http://localhost:8000/force.html to see the example\n')
    app.run(host="0.0.0.0", port=p_port)

if __name__ == "__main__":
    draw_in_browser()
