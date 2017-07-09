var gulp = require('gulp');
var lesshint = require('gulp-lesshint');
var config = require('../config');

var LessLintTask = {

    develop: function () {

        return gulp.src(config.less.src)
            .pipe(lesshint())
            .pipe(lesshint.reporter());
	},
	release: function () {

        return gulp.src(config.less.src)
            .pipe(lesshint())
            .pipe(lesshint.reporter())
            .pipe(lesshint.failOnError());
	}
};
module.exports = LessLintTask;