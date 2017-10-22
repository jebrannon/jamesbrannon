'use strict';

var WorkDirective = function ($rootScope, $timeout) {
	return {
		templateUrl: '/html/directives/Work.html',
		restrict: 'AE',
		link: function(scope, elem, attrs) {
			var isActive = false;

			var handleEvent = function (e, params) {
				var eventType = e.type ? e.type : e.name;
				switch(eventType) {
					case 'element.click':


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

						$rootScope.$broadcast('work.off');
						isActive = false;
					}
				}
				else if (params.top > (elem.position().top - 100)) {

					if (!isActive) {
						
						$rootScope.$broadcast('work.on');
						isActive = true;
					}
				}
			};
			
			var init = function () {

				//  Add listeners
				scope.$on('window.scroll', handleEvent);
				scope.$on('element.click', handleEvent);
			};

			$timeout(init);
		}
	};
};
module.exports = WorkDirective;