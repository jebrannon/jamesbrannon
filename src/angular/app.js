'use strict';

var ng = require('angular');
var sanitize = require('angular-module-sanitize');

var PageController = require('./controllers/PageController');
var UtilsService = require('./services/UtilsService');
var BodyDirective = require('./directives/BodyDirective');
// var RingsDirective = require('./directives/RingsDirective');
var HeaderDirective = require('./directives/HeaderDirective');
var WorkDirective = require('./directives/WorkDirective');
var MeDirective = require('./directives/MeDirective');
// var FeedService = require('./services/FeedService');
// var TruncateFilter = require('./filters/TruncateFilter');

var app = ng.module('ngApp', ['ngSanitize']);

app.config(['$locationProvider',
	function($locationProvider) {
		$locationProvider.html5Mode(false);
	}
]);

app.directive('ngBody', ['$window', '$sce', '$timeout', BodyDirective]);
// app.directive('ngRings', ['$timeout', RingsDirective]);
app.directive('ngHeader', ['$rootScope', '$timeout', HeaderDirective]);
app.directive('ngWork', ['$rootScope', '$timeout', WorkDirective]);
app.directive('ngMe', ['$rootScope', '$timeout', MeDirective]);
// app.filter('truncate', ['$sce', TruncateFilter]);
app.service('Utils', UtilsService);
// app.service('FeedService', ['$http', '$q', 'Utils', FeedService]);
app.controller('PageController', ['$rootScope', '$scope', '$timeout', '$window', '$location', PageController]);