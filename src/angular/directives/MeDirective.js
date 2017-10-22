'use strict';

var MeDirective = function ($rootScope, $timeout) {
	return {
		templateUrl: '/html/directives/Me.html',
		restrict: 'AE',
		link: function(scope, elem, attrs) {
			var isActive = false;

			var handleEvent = function (e, params) {
				var eventType = e.type ? e.type : e.name;
				switch(eventType) {
					case 'onClick':


						break;
					case 'window.scroll':


						whenWindowHasScrolled(params);


						break;
				}
			};

			var whenWindowHasScrolled = function (params) {


				if (params.top > (elem.position().top + elem.height()) - 100 ||
					params.top < (elem.position().top - 100)) {

					if (isActive) {

						$rootScope.$broadcast('me.off');
						isActive = false;
					}
				}
				else if (params.top > (elem.position().top - 100)) {

					if (!isActive) {
						
						$rootScope.$broadcast('me.on');
						isActive = true;
					}
				}
			};

			
			var init = function () {

				// console.log('MeDirective');

				//  Add listeners
				scope.$on('window.scroll', handleEvent);
				scope.$on('onClick', handleEvent);

				$rootScope.$broadcast('window.get.scroll');
			};

			$timeout(init);
		}
	};
};
module.exports = MeDirective;