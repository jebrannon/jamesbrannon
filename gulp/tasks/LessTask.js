var gulp = require('gulp');
var less = require('gulp-less-sourcemap');
var minifycss = require('gulp-minify-css');
var config = require('../config').less;

var LessTask = function () {

	/*
			Development
	*/
  gulp.src(config.src)
    .pipe(less({
      sourceMap: true,
      sourceMapBasepath: './'
    }))
    .pipe(gulp.dest(config.dev));


	/*
			Release
	*/
  gulp.src(config.src)
    .pipe(less({
      sourceMap: false
    }))
    .pipe(minifycss())
    .pipe(gulp.dest(config.release));
};
module.exports = LessTask;