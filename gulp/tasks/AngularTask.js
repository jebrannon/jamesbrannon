var gulp = require('gulp');
var browserify = require('browserify');
var source = require('vinyl-source-stream');
var buffer = require('vinyl-buffer');
var uglify = require('gulp-uglify');
var sourcemaps = require('gulp-sourcemaps');
var config = require('../config');

var AngularTask = {

    develop: function () {
        return browserify({
                entries: [config.angular.src],
                debug: true
            })
            .bundle()
            .pipe(source('app-min.js'))
            .pipe(buffer())
            .pipe(sourcemaps.init({loadMaps: true}))
            .pipe(uglify())
            .pipe(sourcemaps.write('./'))
            .pipe(gulp.dest(config.build.develop + 'js/'));
    },
    release: function () {

        return browserify({
                entries: [config.angular.src],
                debug: false
            })
            .bundle()
            .pipe(source('app-min.js'))
            .pipe(buffer())
            .pipe(uglify())
            .pipe(gulp.dest(config.build.release + 'js/'));
    }
};
module.exports = AngularTask;
