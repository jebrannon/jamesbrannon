var gulp = require('gulp');
var config = require('../config').fonts;

var FontsTask = function () {

	/*
			Development
	*/
  	gulp.src(config.src)
    	.pipe(gulp.dest(config.dev));


	/*
			Release
	*/
 	 gulp.src(config.src)
    	.pipe(gulp.dest(config.release));
};
module.exports = FontsTask;