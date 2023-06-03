function jsClock() {
    var current = new Date().getTime() / 1000;
    $('.jsClock').each(function(i,obj) {
        var now = parseInt( $(obj).find('.now').html() );
        var start = parseInt( $(obj).find('.start').html() );
        var s = Math.floor( current - now + start );
        var d = Math.floor(s / (24 * 60 * 60));
        s = s % (24 * 60 * 60);
        var h = Math.floor(s / (60 * 60));
        s = s % (60 * 60);
        var m = Math.floor(s / 60);
        s = s % 60;
        var l = [];
        if ( d > 0 ) { l.push( d + "d"); }
        if ( h > 0 ) { l.push( h + "h"); }
        if ( m > 0 ) { l.push( m + "m"); }
        if ( s > 0 ) { l.push( s + "s"); }
        $(this).find('.value').html( l.join(" ") );
    });
}
setInterval( jsClock, 1000 );
