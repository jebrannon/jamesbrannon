var gulp = require('gulp');
var jshint = require('gulp-jshint');
var config = require('../config').lint;

var LintTask = function () {
  gulp.src(config.src)
    .pipe(jshint())
    .pipe(jshint.reporter('default'));
};
module.exports = LintTask;