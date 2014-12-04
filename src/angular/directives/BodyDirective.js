'use strict';

var BodyDirective = function ($window, $sce) {
	return {
		restrict: 'AE',
		link: function(scope, elem, attrs) {

			/*
			  Event Handler
			*/
			var _handleEvent = function (e, data) {
				var eventType = e.type ? e.type : e.name;
				switch(eventType) {
					case 'ng_menuExpanded':
						console.log('hg ng_menuExpanded',elem[0]);
						elem.toggleClass('collapse');
						break;
				}
			};

			/*
			  Methods
			*/

		  /*
		  	Event Listeners
		  */
			scope.$on('ng_menuExpanded', _handleEvent);
		}
  };
};
module.exports = BodyDirective;