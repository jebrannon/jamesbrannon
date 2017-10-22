'use strict';

var HeaderDirective = function ($rootScope, $timeout) {
	return {
		templateUrl: '/html/directives/Header.html',
		restrict: 'AE',
		link: function(scope, elem, attrs) {
			var isActive = false;

			var handleEvent = function (e, params) {
				var eventType = e.type ? e.type : e.name;
				switch(eventType) {
					case 'element.click':


						break;
					case 'window.scroll':


						if (params.top > (elem.position().top + elem.height()) - 100 ) {

							if (isActive) {

								$rootScope.$broadcast('header.off');
								isActive = false;
							}
						}
						else {

							if (!isActive) {

								$rootScope.$broadcast('header.on');
								isActive = true;
							}
						}

						break;
				}
			};

			
			var init = function () {

				// console.log('HeaderDirective');

				//  Add listeners
				scope.$on('window.scroll', handleEvent);
				scope.$on('element.click', handleEvent);
				
				$rootScope.$broadcast('window.get.scroll');
			};

			$timeout(init);
		}
	};
};
module.exports = HeaderDirective;