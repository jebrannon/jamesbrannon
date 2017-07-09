var gulp = require('gulp');
var Sequence = require('run-sequence');
var watch = require('gulp-watch');


/*
		Import task modules
*/
var config = require('./gulp/config');
var Clean = require('./gulp/tasks/CleanTask');
var Index = require('./gulp/tasks/IndexTask');
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
// gulp.task('images', Images);
// gulp.task('fonts', Fonts);
gulp.task('clean:develop', Clean.develop);
gulp.task('clean:release', Clean.release);
gulp.task('index:develop', Index.develop);
gulp.task('index:release', Index.release);
gulp.task('markup:develop', Markup.develop);
gulp.task('markup:release', Markup.release);
gulp.task('lesslint:develop', LessLint.develop);
gulp.task('lesslint:release', LessLint.release);
gulp.task('less:develop', Less.develop);
gulp.task('less:release', Less.release);
gulp.task('lint:strict', Lint.strict);
gulp.task('lint:watch', Lint.release);
gulp.task('angular:develop', Angular.develop);
gulp.task('angular:release', Angular.release);
gulp.task('libs:develop', Libs.develop);
gulp.task('libs:release', Libs.release);
gulp.task('server:reload', Server.reload);
gulp.task('server:develop', Server.develop);
gulp.task('deploy', Deployment);

/**
 *  Watcher function.
 */
var watcher = function (env) {
    
	watch(config.markup.watch, function () {
		Sequence('index:develop', 'markup:develop', 'server:reload');
    });
	watch(config.less.watch, function () {
		Sequence('lesslint:develop', 'less:develop', 'server:reload');
 	});
    watch(config.libs.watch, function () {
        Sequence('libs:develop', 'server:reload');
    });
	watch(config.angular.watch, function () {
		Sequence('lint:develop', 'angular:develop', 'server:reload');
 	});
};


/**
 *  Task groups.
 */
gulp.task('default', function () {

    Sequence('clean:develop', 'index:develop', 'markup:develop', 'lesslint:develop', 'less:develop', 'libs:develop', 'lint:watch', 'angular:develop', 'server:develop', function () {

        //  Call watcher function.
        watcher();
    });
});

gulp.task('release', function () {

    Sequence('clean:release', 'index:release', 'markup:release', 'lesslint:release', 'less:release', 'libs:release', 'lint:strict', 'angular:release', 'deploy', function () {

        //  Call watcher function.
        // watcher();
    });
});