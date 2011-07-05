(function($){

    var methods = {
        init: function(o) {
            var myOpts = $.extend(true, {}, options, o);
            data[this.selector] = {};
            data[this.selector]['opts'] = myOpts;

            // initialize the ticks
            var ticks = [];
            for (var i = 0; i < ticks_l.length; i++) {
                ticks.push([myOpts.xaxis.t[i], ticks_l[i]]);
            }
            myOpts.xaxis.ticks = ticks;
            return this;
        },
        _update: function(rawData, encData) {
            data[0]['data'] = rawData;
            data[1]['data'] = encData;
            return this;
        },
        update: function(cells) {
            data_p = []; data_e = [];
            if (cells) {
                var myOpts = data[this.selector]['opts'];
                for (var i = 0; i < cells.length/2; i++) {
                    data_p.push([myOpts.xaxis.p[i], cells[i]]);
                    data_e.push([myOpts.xaxis.e[i], cells[i+cells.length/2]]);
                }
            }
            return this.myGraph('_update', data_p, data_e);
        },
        clear: function() {
            return this.myGraph('update').myGraph('plot');        
        },
        plot: function() {
            console.log("plotting...");
            console.log(this.selector);
            var myOpts = data[this.selector]['opts'];
            $.plot($(this.selector), data, myOpts);
            return this;
        }
    };

    var data = {};

    // table cars
    var headers = ['Pattern', 'Plain', 'Encrypted'];
    var ioPatterns = ['Seq Read', 'Seq Write', 'Seq R/W', 'Rand Read', 'Rand Write', 'Rand R/W'];

    // flot vars
    var data_p = [], data_e = [];
    var ticks_l = ["Seq Read", "Seq Write", "Seq R/W", "Rand Read", "Rand Write", "Rand R/W"];
    var ticks = [];

    var data = [
    {
        label: "Plain",
        data: data_p
    },
    {
        label: "Encrypted",
        data: data_e
    }
    ];

    var options = { 
        xaxis: {
                   min: 0,
               },
        yaxis: {
                   min: 0,
                   labelWidth: 50
               },
        bars: {
                  show: true,
                  barWidth: 1
              }
    };
    
    $.fn.myGraph = function(method) {
        if ( methods[method] ) {
            return methods[method].apply( this, Array.prototype.slice.call( arguments, 1 ));
        } else if ( typeof method === 'object' || ! method ) {
            return methods.init.apply( this, arguments );
        } else {
            $.error( 'Method ' +  method + ' does not exist on jQuery.tooltip' );
        }    
    };
})(jQuery);


