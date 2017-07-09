var gulp = require('gulp');
var config = require('../config');
var del = require('del');

var CleanTask = {
	develop: function () {
	    return del([
	        config.build.develop + '**/*'
	    ]);
	},
	release: function () {
	    return del([
	        config.build.release + '**/*'
	    ]);
	}
};
module.exports = CleanTask;