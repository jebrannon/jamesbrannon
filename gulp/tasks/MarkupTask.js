var gulp = require('gulp');
var config = require('../config').markup;
var configsvg = require('../config').svg;
var inject = require('gulp-inject');
var minifyhtml = require('gulp-minify-html');
var svgmin = require('gulp-svgmin');
var svgstore = require('gulp-svgstore');

var MarkupTask = function () {
    var svgs = gulp
        .src(configsvg.src)
        .pipe(svgmin())
        .pipe(svgstore({ inlineSvg: true }));
        
    function fileContents (filePath, file) {
        return file.contents.toString();
    }


    //  Develop
    gulp.src(config.index.src)
        .pipe(inject(svgs, { transform: fileContents }))
        .pipe(minifyhtml({comments: false}))
        .pipe(gulp.dest(config.index.dev));

    gulp.src(config.views.src)
        .pipe(minifyhtml({comments: false}))
        .pipe(gulp.dest(config.views.dev));


    //  Release
    gulp.src(config.index.src)
        .pipe(inject(svgs, { transform: fileContents }))
        .pipe(minifyhtml({comments: false}))
        .pipe(gulp.dest(config.index.release));

    gulp.src(config.views.src)
        .pipe(minifyhtml({comments: false}))
        .pipe(gulp.dest(config.views.release));
};
module.exports = MarkupTask;