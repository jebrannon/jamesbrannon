var gulp = require('gulp');
var jshint = require('gulp-jshint');
var config = require('../config').angular;

var LintTask = function () {
	
	return gulp.src(config.watch)
			.pipe(jshint())
			.pipe(jshint.reporter('default'));
			// .pipe(jshint.reporter('fail'));
};
module.exports = LintTask;