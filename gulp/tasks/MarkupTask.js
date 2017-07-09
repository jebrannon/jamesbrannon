var gulp = require('gulp');
var config = require('../config');
var minifyhtml = require('gulp-minify-html');

var MarkupTask = {
    develop: function () {
        
        return gulp.src(config.markup.src)
            .pipe(gulp.dest(config.build.develop + 'html/'));
    },
    release: function () {

        return gulp.src(config.markup.src)
            .pipe(minifyhtml({comments: false}))
            .pipe(gulp.dest(config.build.release + 'html/'));
    }
};
module.exports = MarkupTask;