var gulp = require('gulp');
var imagemin = require('gulp-imagemin');
var pngcrush = require('imagemin-pngcrush');
var config = require('../config').images;

var ImagesTask = function () {

	/*
			Development
	*/
  gulp.src(config.src)
    .pipe(imagemin({
      progressive: true,
      svgoPlugins: [{removeViewBox: false}],
      use: [pngcrush()]
    }))
    .pipe(gulp.dest(config.dev));


	/*
			Release
	*/
  gulp.src(config.src)
    .pipe(imagemin({
      progressive: true,
      svgoPlugins: [{removeViewBox: false}],
      use: [pngcrush()]
    }))
    .pipe(gulp.dest(config.release));
};
module.exports = ImagesTask;