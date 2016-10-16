'use strict';

var HeaderDirective = function ($timeout) {
	return {
		templateUrl: '/html/directives/Header.html',
		restrict: 'AE',
		link: function(scope, elem, attrs) {


			var handleEvent = function (e) {
				var eventType = e.type ? e.type : e.name;
				switch(eventType) {
					case 'onClick':
						break;
					case 'onScroll':
						break;
				}
			};

			
			var init = function () {

				console.log('HeaderDirective');

				//  Add listeners
				scope.$on('onScroll', handleEvent);
				scope.$on('onClick', handleEvent);
			}

			$timeout(init);
		}
	};
};
module.exports = HeaderDirective;