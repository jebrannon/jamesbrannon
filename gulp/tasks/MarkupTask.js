var gulp = require('gulp');
var minifyhtml = require('gulp-minify-html');
var rename = require('gulp-rename');
var config = require('../config').markup;

var MarkupTask = function () {

	/*
			Development
	*/
  gulp.src(config.index.src)
  	.pipe(minifyhtml({comments: false}))
    .pipe(gulp.dest(config.index.dev));

  gulp.src(config.views.src)
  	.pipe(minifyhtml({comments: false}))
    .pipe(gulp.dest(config.views.dev));


	/*
			Release
	*/
  gulp.src(config.index.src)
    .pipe(minifyhtml({comments: false}))
    .pipe(gulp.dest(config.index.release));

  gulp.src(config.views.src)
    .pipe(minifyhtml({comments: false}))
    .pipe(gulp.dest(config.views.release));
};
module.exports = MarkupTask;