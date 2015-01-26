// Global variables of the script

/* Adjacency matrix dipicting the graph
 * Value legend: 00    -> no edge
 *               -1    -> undiscovered edge
 				 >0    -> weight of a discovered edge
 */									 
var adjMtx = [[00, -1, 00, -1, 00, 00, 00, 00, 00, 00, 00],
			  [-1, 00, 00, -1, 00, 00, 00, 00, 00, 00, 00], 
			  [00, 00, 00, 00, -1, 00, -1, -1, 00, 00, 00],
			  [-1, -1, 00, 00, -1, 00, 00, -1, 00, 00, 00], 
			  [00, 00, -1, -1, 00, 00, -1, 00, -1, 00, 00],
			  [00, 00, 00, 00, 00, -1, 00, -1, -1, 00, 00], 
			  [00, 00, -1, 00, -1, 00, 00, 00, -1, 00, 00],
			  [00, 00, -1, -1, 00, -1, 00, 00, 00, -1, -1], 
			  [00, 00, 00, 00, 00, -1, -1, 00, 00, 00, 00],
			  [00, 00, 00, 00, 00, -1, 00, 00, -1, 00, -1],
			  [00, 00, 00, 00, 00, 00, 00, -1, 00, -1, 00]];
				
// Node Attributes: 2D position, color and label
var nodeAttrs = [{x:5, y:50, color:"#FF0000", label:"Red"},
				 {x:8, y:9, color:"#FFFF00", label:"Yellow"},
				 {x:60, y:60, color:"#00FF12", label:"Green"},
				 {x:44, y:12, color:"#FF00BA", label:"Magenta"},
				 {x:32, y:50, color:"#FDFF66", label:"Sad Yellow"},
				 {x:70, y:80, color:"#1E420D", label:"Dark Green"},
				 {x:22, y:80, color:"#FF9000", label:"Orange"},
				 {x:100, y:60, color:"#51510B", label:"Sad Brown"},
				 {x:10, y:100, color:"#A20000", label:"Dark Red"},
				 {x:50, y:110, color:"#6EB75F", label:"Sad Green"},
				 {x:75, y:100, color:"#46C993", label:"Cyan"}];
// Discovered Node Colors
var nodeColors = ["#ccc","#ccc","#ccc","#ccc","#ccc","#ccc","#ccc","#ccc","#ccc","#ccc","#ccc"];
// Undiscovered and Discovered Edge Colors
var edgeColors = [["#ccc", "#888"], ["#bfa", "#56f"]];
// Unweighted Edge Label
var noDistanceLabel = '?';
// DOM Div ID wherein rendering the graph
var graphWindow = 'graph_window';
// Default width and height of the graph window
var width = 800;
var height = 600;
// Render function for the nodes
var render = function (r, n) {
	/* the Raphael set is obligatory, containing all you want to display */
	var ellipse = r.ellipse(0, 0, 30, 20).attr({ fill: nodeColors[n.id-1], stroke: nodeColors[n.id-1], "stroke-width": 2 });
	
	/* set DOM node ID */
	ellipse.node.id = n.label || n.id;
	shape = r.set().
	push(ellipse).
	push(r.text(0, 30, n.label || n.id));
	
	return shape;
};
// URL of the current discovered graph coded as JSON Object
var discoverJSONGraphURL = 'graph';
// Delay of the request to check updates on the current graph in milliseconds
var updateDelay = 1000;

// Routines of the script

// Draws the graph according the current adjacency matrix applying styles of undiscovered/discovered nodes, edges and weights.
function drawGraph() {
	// Rendering of the graph
	//var width = $("#"+graphWindow).width();
    //var height = $("#"+graphWindow).height();
    var g = new Graph();
	
    g.edgeFactory.template.style.directed = false;
	
	// Builds the graph structure according the current   
	for (i = 0; i < adjMtx.length; i++) {	
		for (j = 0; j < i; j++) {
			if (adjMtx[i][j] != 0) {
				var edgeColor = edgeColors[0];
				var distanceLabel = noDistanceLabel;
				
				if (adjMtx[i][j] > 0) {
					nodeColors[i] = nodeAttrs[i]["color"];
					nodeColors[j] = nodeAttrs[j]["color"];
					edgeColor = edgeColors[1];
					distanceLabel = adjMtx[i][j];
				}
				
				g.addNode(i+1, {x:nodeAttrs[i]["x"], y:nodeAttrs[i]["y"], render:render, label:nodeAttrs[i]["label"]});
				g.addNode(j+1, {x:nodeAttrs[j]["x"], y:nodeAttrs[j]["y"], render:render, label:nodeAttrs[j]["label"]});
				g.addEdge(i+1, j+1, {stroke:edgeColor[0] , fill:edgeColor[1], label:distanceLabel, "label-style" : {
"font-size": 12, "text-shadow": "0 0 2px #fff"
}});
			}
		}
	}
    
    //var layouter = new Graph.Layout.Ordered(g, topological_sort(g));
	//var layouter = new Graph.Layout.Spring(g);
    var layouter = new Graph.Layout.Fixed(g);
	layouter.layout();
	
	$("#"+graphWindow).empty();
    var renderer = new Graph.Renderer.Raphael(graphWindow, g, width, height);
	
	return;
}

/*
	Main function of the viewer which shows in realtime the discovered parts of the graph.
*/
function startViewer() {
	drawGraph(); // Draws the initial version of the graph
	
	(
		/*
		 *	The function calls periodically the source discoverJSONGraphURL 
		 *	which returns a JSON depiction of the current discovered graph;
		 *	after that updates the adjacency matrix with the new information (discovered endges and weights)
		 *  and redraw on the graphWindow the new status of the graph.
		*/
		function graphUpdater() {
			$.ajax({
			dataType: "json",
			url: discoverJSONGraphURL, 
			success: function(data) {
				$.each( data, function( fromeNodeId, toNodeIds ) {
					for (i = 0; i < toNodeIds.length; i++) {
						adjMtx[fromeNodeId][toNodeIds[i][0]] = toNodeIds[i][1];
					}
					
				});
				drawGraph();
			},
			complete: function() {
				setTimeout(graphUpdater, updateDelay);
			}
		  });
		}
	)(); // Call of graphUpdater function
	
	return;	
}

// Starts the viewer script
$(document).ready(function() {
	width = $("#"+graphWindow).width();
	height = $("#"+graphWindow).height();
	startViewer();
});