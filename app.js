
/**
 * Module dependencies.
 */

var express = require('express');
var fs = require('fs');

var app = module.exports = express.createServer();
var port;

// Configuration

app.configure(function(){
  app.use(express.logger());
  app.set('views', __dirname + '/views');
  app.set('view engine', 'jade');
  app.use(express.bodyParser());
  app.use(express.methodOverride());
  app.use(app.router);
  app.use(express.static(__dirname + '/public'));
});

app.configure('development', function(){
  app.use(express.errorHandler({ dumpExceptions: true, showStack: true })); 
  port = 8888;
});

app.configure('production', function(){
  app.use(express.errorHandler()); 
  port = 8080;
});

// Routes

var attributes = [
    {name:'instance-type', label:'Instance Type', values:{m1small:'m1.small', m1large:'m1.large', m1xlarge:'m1.xlarge', c1xlarge:'c1.xlarge'}}, 
    {name:'file-system', label:'File System', values:{ext3:'ext3', ext4:'ext4', xfs:'xfs'}}, 
    {name:'mount-options', label:'Mount Options', values:{none:'none', noatime:'noatime'}}, 
    {name:'storage-type', label:'Storage Type', values:{ebs:'ebs', ephemeral:'ephemeral'}},
    {name:'instance-tenancy', label:'Instance Tenancy', values:{dedicated:'dedicated', default:'default'}},
    {name:'encryption-layer', label:'Encryption Layer', values:{domU:'domU', dom0:'dom0'}}
];

app.get('/', function(req, res){
    res.render('index', {
        title: 'EBS Benchmarking',
        attributes: attributes
    });
});

var fileRegex = /.*-(.*)\.txt/;
app.post('/q', function(req, res) {
    console.log(req.body);
    var arr = [];
    for (var i in req.body) {
        arr.push(req.body[i]);
    }
    console.log(arr);
    var prefix = arr.join('-');
    var path = './public/results';
    fs.readdir(path, function(err, files) {
        files = files.filter(function(e) {
            return e.indexOf(prefix) == 0;
        });
        console.log(files)
        // sort the files based on execution time
        files.sort(function(l, r) {
            return parseInt(fileRegex.exec(r)[1]) - parseInt(fileRegex.exec(l)[1]); 
        });
        res.send({req:req.body, files:files});
    });
});

app.listen(port);
console.log("Express server listening on port %d", app.address().port);
