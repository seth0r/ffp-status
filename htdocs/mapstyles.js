const node_colors = {
    green : [   0, 238,  0, 1.0 ],
    yellow: [ 255, 255,  0, 1.0 ],
    red   : [ 255,   0,  0, 1.0 ],
    grey  : [  55,  55, 55, 0.5 ],
}

function icolor( value, colors ){
    if (value <= colors[0][0]) {
        return colors[0].slice(1);
    } else if (value >= colors[colors.length-1][0]) {
        return colors[colors.length-1].slice(1);
    }
    for (i=0; i<colors.length-1; i++) {
        if (value >= colors[i][0] && value <= colors[i+1][0]) {
            f = (value - colors[i][0]) / (colors[i+1][0] - colors[i][0]);
            c = [];
            for (j=1; j<5; j++){
                c.push( colors[i][j] + (colors[i+1][j] - colors[i][j]) * f );
            }
            return c;
        }
    }
};

function style_node(feature,resolution) {
    var props = feature.getProperties();
    var colors = [];
    for ( [cn, offline] of _.sortBy( _.pairs(props['offline_limits']), function(a){ return a[1]} ) ) {
        colors.push( [offline].concat(node_colors[cn]) );
    }
    var r = Math.max( 3, Math.min( 10 / Math.sqrt(resolution), 10 )) * (props['offline'] > 2 * colors[colors.length-1][0] ? 0.5 : 1.0);
    if (props['uplink']) {
        var img = new ol.style.RegularShape({ points: 3, radius: r * 1.33 });
    } else {
        var img = new ol.style.Circle({ radius: r });
    }
    img.setFill( new ol.style.Fill({ color: "rgba(" + icolor( props['offline'], colors ).join() + ")" }) );
    img.setStroke( new ol.style.Stroke({ color: '#222222' }) );
    return new ol.style.Style({ image: img });
};

