var gulp = require('gulp');
var config = require('../config');
var minifyhtml = require('gulp-minify-html');
var svgstore = require('gulp-svgstore');
var inject = require('gulp-inject');

var IndexTask = {
    develop: function () {
        var svgs = gulp
            .src(config.svg.src)
            .pipe(svgstore({ inlineSvg: true }));
     
        function fileContents (filePath, file) {
            return file.contents.toString();
        }
     
        return gulp
            .src(config.svg.markup)
            .pipe(inject(svgs, { transform: fileContents }))
            .pipe(gulp.dest(config.build.develop));
    },
    release: function () {
        var svgs = gulp
            .src(config.svg.src)
            .pipe(svgstore({ inlineSvg: true }));
     
        function fileContents (filePath, file) {
            return file.contents.toString();
        }
     
        return gulp
            .src(config.svg.markup)
            .pipe(inject(svgs, { transform: fileContents }))
            .pipe(minifyhtml({comments: false}))
            .pipe(gulp.dest(config.build.release));
    }
};
module.exports = IndexTask;