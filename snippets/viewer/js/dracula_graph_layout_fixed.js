Graph.Layout.Fixed = function(graph) {
  this.graph = graph;
  this.layout();
};

Graph.Layout.Fixed.prototype = {
  layout: function() {
    this.layoutPrepare();
    this.layoutCalcBounds();
  },
  
  layoutPrepare: function() {
    for (i in this.graph.nodes) {
      var node = this.graph.nodes[i];
      if (node.x) {
        node.layoutPosX = node.x;
      } else {
        node.layoutPosX = 0;
      }
      if (node.y) {
        node.layoutPosY = node.y;
      } else {
        node.layoutPosY = 0;
      }
    }
  },
  
  layoutCalcBounds: function() {
    var minx = Infinity, maxx = -Infinity, miny = Infinity, maxy = -Infinity;
    
    for (i in this.graph.nodes) {
      var x = this.graph.nodes[i].layoutPosX;
      var y = this.graph.nodes[i].layoutPosY;
      
      if(x > maxx) maxx = x;
      if(x < minx) minx = x;
      if(y < miny) miny = y;
      if(y > maxy) maxy = y;
    }
    
    this.graph.layoutMinX = minx;
    this.graph.layoutMaxX = maxx;
      
    this.graph.layoutMinY = miny;
    this.graph.layoutMaxY = maxy;
  }
};