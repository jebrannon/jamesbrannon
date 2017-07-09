var gulp = require('gulp');
var config = require('../config');
var bs1 = require('browser-sync').create('one');

var ServerTask = {
	reload: function () {
		bs1.reload();
	},
	develop: function () {
		bs1.init({
			port: 3000,
			server: {
				baseDir: config.build.develop,
				middleware: function (req, res, next) {
			        res.setHeader('Access-Control-Allow-Origin', '*');
			        next();
			    }
			}
		});
	}
};
module.exports = ServerTask;