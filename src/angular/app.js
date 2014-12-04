'use strict';

var ng = require('angular');
var sanitize = require('angular-module-sanitize');

var PageController = require('./controllers/PageController');
var FeedDirective = require('./directives/FeedDirective');
var UtilsService = require('./services/UtilsService');
var MenuDirective = require('./directives/MenuDirective');
var BodyDirective = require('./directives/BodyDirective');
var FeedService = require('./services/FeedService');
var TruncateFilter = require('./filters/TruncateFilter');

var app = ng.module('ngApp', ['ngSanitize']);

app.config(['$locationProvider',
	function($locationProvider) {
		$locationProvider.html5Mode(false);
	}
]);

app.directive('ngFeed', ['$window', '$sce', FeedDirective]);
app.directive('ngMenu', ['$window', '$sce', MenuDirective]);
app.directive('ngBody', ['$window', '$sce', BodyDirective]);
app.filter('truncate', ['$sce', TruncateFilter]);
app.service('Utils', UtilsService);
app.service('FeedService', ['$http', '$q', 'Utils', FeedService]);
app.controller('PageController', ['$rootElement', '$scope', '$window', '$location', 'FeedService', PageController]);