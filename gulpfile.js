var gulp = require('gulp');
var Sequence = require('run-sequence');
var watch = require('gulp-watch');


/*
		Import task modules
*/
var config = require('./gulp/config');
var Images = require('./gulp/tasks/ImagesTask');
var Fonts = require('./gulp/tasks/FontsTask');
var Markup = require('./gulp/tasks/MarkupTask');
var LessLint = require('./gulp/tasks/LessLintTask');
var Less = require('./gulp/tasks/LessTask');
var Libs = require('./gulp/tasks/LibsTask');
var Lint = require('./gulp/tasks/LintTask');
var Angular = require('./gulp/tasks/AngularTask');
var Server = require('./gulp/tasks/ServerTask');
var Deployment = require('./gulp/tasks/DeploymentTask');


/*
		Define individual tasks
*/
gulp.task('images', Images);
gulp.task('fonts', Fonts);
gulp.task('markup', Markup);
gulp.task('lesslint', LessLint);
gulp.task('less', Less);
gulp.task('libs', Libs);
gulp.task('lint', Lint);
gulp.task('angular', Angular);
gulp.task('run-dev-server', Server.develop);
gulp.task('run-release-server', Server.release);
gulp.task('reload', Server.reload);
gulp.task('release', Deployment);


/**
 *  Watcher function.
 */
var watcher = function (env) {
    
	watch(config.markup.watch, function () {
		Sequence('markup', 'server:reload');
    });
	watch(config.less.watch, function () {
		Sequence('lesslint', 'less', 'reload');
 	});
	watch(config.angular.watch, function () {
		Sequence('lint', 'angular', 'reload');
 	});
};


/**
 *  Task groups.
 */
gulp.task('default', function () {

    Sequence('images', 'fonts', 'markup', 'lesslint', 'less', 'libs', 'lint', 'angular', 'run-dev-server', function () {

        //  Call watcher function.
        watcher();
    });
});