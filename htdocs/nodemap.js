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
    }),
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

map.on('click', function(evt) {
    var feature = map.forEachFeatureAtPixel(evt.pixel, function(feature, layer) { return feature; });
    if (feature) {
        var c = feature.get("info");
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
        $('#infobox').popover('dispose');
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
