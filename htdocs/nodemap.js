const layer_links = new ol.layer.Vector({
    title: 'Links',
    source: new ol.source.Vector({
        projection : 'EPSG:3857',
        format: new ol.format.GeoJSON(),
        url: '/links.geojson',
    }),
    style: style_link,
});
const layer_nodes = new ol.layer.Vector({
    title: 'Nodes',
    source: new ol.source.Vector({
        projection : 'EPSG:3857',
        format: new ol.format.GeoJSON(),
        url: '/nodes.geojson',
    }),
    style: style_node,
});
const map = new ol.Map({
    target: 'map',
    layers: [
        new ol.layer.Tile({
            source: new ol.source.OSM(),
        }),
        layer_links,
        layer_nodes,
    ],
    view: new ol.View({
        center: ol.proj.fromLonLat([13.0642644, 52.3948361]),
        zoom: 14,
        maxZoom: 22,
    }),
});

window.addEventListener('hashchange', function () {
    update_map();
});

function get_url_params() {
    var url_hash = window.location.hash.substr(1);
    var url_params = url_hash.split('&').reduce(function (res, item) {
        var parts = item.split('=');
        res[parts[0]] = parts[1];
        return res;
    }, {});
    return url_params;
}

function update_map() {
    var url_params = get_url_params();
    var zoom = parseFloat(url_params.zoom);
    if (!Number.isNaN(zoom)) {
        map.getView().setZoom(zoom);
    }
    var lat = parseFloat(url_params.lat);
    var lon = parseFloat(url_params.lon);
    if (!Number.isNaN(lat) && !Number.isNaN(lon)) {
        map.getView().setCenter( ol.proj.fromLonLat([url_params.lon,url_params.lat]) );
    }
}
update_map();
map.on('moveend', function(evt){
    var c = ol.proj.toLonLat(map.getView().getCenter());
    window.location.hash = '#zoom=' + map.getView().getZoom().toFixed(3) + '&lon=' + c[0].toFixed(6) + '&lat=' + c[1].toFixed(6)
});

const infobox = new ol.Overlay({
    element: document.getElementById('infobox'),
    positioning: 'bottom-center',
    offset: [0,-5],
    stopEvent: true,
    autoPan: true,
    autoPanAnimation : {
        duration : 250
    }
});
map.addOverlay(infobox);

var last_id = null;
map.on('click', function(evt) {
    var feature = map.forEachFeatureAtPixel(evt.pixel, function(feature, layer) { return feature; });
    if (feature) {
        var c = feature.get("info");
        last_id = [feature.get("type"),feature.get("id")];
        if (c) {
            $('#infobox').popover('dispose');
            $('#infobox').popover({
                'placement': 'bottom',
                'html': true,
                'content': c,
                'animation': false,
            });
            if (feature.getGeometry().getType() == "Point") {
                infobox.setPosition(feature.getGeometry().getCoordinates());
            } else {
                infobox.setPosition(evt.coordinate);
            }
            $('#infobox').popover('show');
        }
    } else {
        last_id = null;
        $('#infobox').popover('dispose');
    }
});
function update_infobox( features ) {
    for (f of features) {
        if (last_id[1] == f.get("id")) {
            var c = f.get("info");
            if (c) {
                $('#'+last_id[1]).replaceWith(c);
            }
            return;
        }
    }
    last_id = null;
    $('#infobox').popover('dispose');
}
layer_nodes.getSource().on('featuresloadend', function( evt ) {
    if (last_id && last_id[0] == "node") {
        update_infobox( evt.features );
    }
});
layer_links.getSource().on('featuresloadend', function( evt ) {
    if (last_id && last_id[0] == "link") {
        update_infobox( evt.features );
    }
});

const popup = new ol.Overlay({
    element: document.getElementById('popup'),
    positioning: 'top-center',
    offset: [0,-5],
    stopEvent: false,
});
map.addOverlay(popup);

map.on('pointermove', function (evt) {
    var feature = map.forEachFeatureAtPixel(evt.pixel, function(feature, layer) { return feature; });
    if (feature) {
        var c = feature.get("popup");
        if (c) {
            $('#popup').popover('dispose');
            $('#popup').popover({
                'placement': 'top',
                'html': true,
                'content': c,
                'animation': false,
            });
            popup.setPosition(feature.getGeometry().getCoordinates());
            $('#popup').popover('show');
        }
    } else {
        $('#popup').popover('dispose');
    }
});

window.setInterval(function () {
    for ( layer of map.getAllLayers()) {
        layer_nodes.getSource().refresh();
        layer_links.getSource().refresh();
    }
}, 60000);
