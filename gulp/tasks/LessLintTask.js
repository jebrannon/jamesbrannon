var gulp = require('gulp');
var lesshint = require('gulp-lesshint');
var config = require('../config').less;

var LessLintTask = function () {

	return gulp.src(config.watch)
			.pipe(lesshint())
			.pipe(lesshint.reporter());
};
module.exports = LessLintTask;