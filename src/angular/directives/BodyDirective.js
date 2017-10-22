'use strict';

var BodyDirective = function ($window, $sce, $timeout) {
	return {
		restrict: 'AE',
		link: function(scope, elem, attrs) {

			var handleEvent = function (e) {
				var eventType = e.type ? e.type : e.name;
				switch(eventType) {
					case 'click':
						scope.$broadcast('onClick', e);
						break;
					case 'window.get.scroll':
					case 'scroll':
						
						scope.$broadcast('window.scroll', {
							event: e,
							top: $window.scrollY
						});

						break;
				}
			};

			
			var init = function () {


				elem.on('click', handleEvent);
				$window.addEventListener('scroll', handleEvent);


        		scope.$on('window.get.scroll', handleEvent);

			};

			$timeout(init);
		}
	};
};
module.exports = BodyDirective;