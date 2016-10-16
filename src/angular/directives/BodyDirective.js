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
					case 'scroll':
						scope.$broadcast('onScroll', e);
						break;
				}
			};

			
			var init = function () {

				elem.on('click', handleEvent);
				$window.addEventListener('scroll', handleEvent);
			};

			$timeout(init);
		}
	};
};
module.exports = BodyDirective;