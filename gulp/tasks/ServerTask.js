var browserSync = require('browser-sync');
var config = require('../config').server;

var ServerTask = {
	reload: function () {
		browserSync.reload();
	},
	develop: function () {
		browserSync({
			port: config.dev.port,
			server: {
				baseDir: config.dev.dir
			}
		});
	},
	release: function () {
		browserSync({
			port: config.release.port,
			server: {
				baseDir: config.release.dir
			}
		});
	}
};
module.exports = ServerTask;