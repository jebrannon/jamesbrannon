var gulp = require('gulp');
var concat = require('gulp-concat');
var uglify = require('gulp-uglify');
var config = require('../config').libs;

var LibsTask = function () {

	/*
			Development
	*/
  gulp.src(config.src)
  	.pipe(concat('libs-min.js'))
  	.pipe(uglify())
    .pipe(gulp.dest(config.dev));


	/*
			Release
	*/
  gulp.src(config.src)
  	.pipe(concat('libs-min.js'))
  	.pipe(uglify())
    .pipe(gulp.dest(config.release));
};
module.exports = LibsTask;