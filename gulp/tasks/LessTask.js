var gulp = require('gulp');
var less = require('gulp-less');
var lesssource = require('gulp-less-sourcemap');
var cleanCSS = require('gulp-clean-css');
var config = require('../config');

var LessTask = {

	develop: function () {
        return gulp.src(config.less.src)
                .pipe(lesssource({
                    sourceMapURL: 'styles.css.map',
                    sourceMapFileInline: false
                }))
                .pipe(gulp.dest(config.build.develop));
    },
    release: function () {
        return gulp.src(config.less.src)
                .pipe(less())
                .pipe(cleanCSS())
                .pipe(gulp.dest(config.build.release));

    }
};
module.exports = LessTask;