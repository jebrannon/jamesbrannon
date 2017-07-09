var gulp = require('gulp');
var concat = require('gulp-concat');
var uglify = require('gulp-uglify');
var config = require('../config');

var LibsTask = {
    develop: function() {
        return gulp.src(config.libs.src)
                .pipe(concat('libs-min.js'))
                .pipe(uglify())
                .pipe(gulp.dest(config.build.develop + 'js/'));

    },
    release: function() {
        return gulp.src(config.libs.src)
                .pipe(concat('libs-min.js'))
                .pipe(uglify())
                .pipe(gulp.dest(config.build.release + 'js/'));
    }
};
module.exports = LibsTask;