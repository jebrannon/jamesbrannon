'use strict';

var FeedDirective = function ($window, $sce) {
	return {
		templateUrl: '/html/FeedView.html',
		restrict: 'AE',
		link: function(scope, elem, attrs) {
			var _$window = angular.element($window);
			var _$body = (scope.isIE || scope.isFF) ? $('html') : $('body');   //  This needs to be 'HTML' for IE.
			var _transEndEventNames = 'transitionend webkitTransitionEnd';
			var _animsEndEventNames = 'animationend webkitAnimationEnd';

			/*
			  Event Handler
			*/
			var _handleEvent = function (e, data) {
				var eventType = e.type ? e.type : e.name;
				switch(eventType) {
					case 'debouncedresize':
						break;
				}
			};
			var _handleDataResponse = function() {
				console.log('_handleDataResponse');
			};


			

			/*
			  Methods
			*/

		  /*
		  	Event Listeners
		  */
			// scope.$on('ng_update', _handleEvent);
		}
  };
};
module.exports = FeedDirective;