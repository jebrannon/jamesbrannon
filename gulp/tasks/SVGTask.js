var gulp = require('gulp');
var svgstore = require('gulp-svgstore');
var svgmin = require('gulp-svgmin');
var rename = require('gulp-rename');
var config = require('../config').svg;
 

var SVGTask = function () {

	/*
			Development
	*/
	gulp.src(config.src)
        .pipe(svgmin())
        .pipe(svgstore())
        .pipe(rename("icons.svg"))
        .pipe(gulp.dest(config.dev));

	/*
			Release
	*/
	gulp.src(config.src)
        .pipe(svgmin())
        .pipe(svgstore())
        .pipe(rename("icons.svg"))
        .pipe(gulp.dest(config.release));
};
module.exports = SVGTask;