var gulp = require('gulp');
var config = require('../config');
var jshint = require('gulp-jshint');

var LintTask = {
    watch: function() {
        return gulp.src(config.angular.src)
                .pipe(jshint())
                .pipe(jshint.reporter('default'));

    },
    strict: function() {
        return gulp.src(config.angular.src)
                .pipe(jshint())
                .pipe(jshint.reporter('default'))
                .pipe(jshint.reporter('fail'));
    }
};
module.exports = LintTask;