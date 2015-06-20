'use strict';

var BodyDirective = function ($window, $sce) {
	return {
		restrict: 'AE',
		link: function(scope, elem, attrs) {
			var transitionEnd = 'webkitTransitionEnd transitionend msTransitionEnd oTransitionEnd';

			var handleEvent = function (e, data) {
				var eventType = e.type ? e.type : e.name;
				switch(eventType) {
					case 'click':
						handleClickEvents(e);
						break;
					case 'webkitTransitionEnd':
					case 'transitionend':
					case 'msTransitionEnd':
					case 'oTransitionEnd':
						handleAnimationEvents(e);
						break;
				}
			};
			var handleClickEvents = function(e) {
				var action = $(e.target).attr('data-jb-action');
				switch(action) {
					case 'OpenSiteNav':
						if (!elem.hasClass('site-nav-open')) {
							elem.addClass('prevent-scroll');
						}
						elem.toggleClass('site-nav-open');
						break;
				}
			}
			var handleAnimationEvents = function (e) {
				var transition = $(e.target).attr('data-jb-transition');
				switch(transition) {
					case 'SiteNav':
						if (!elem.hasClass('site-nav-open')) {
							elem.removeClass('prevent-scroll');
						}
						break;
				}
			}

			
			var init = function () {
				elem.on('click', handleEvent);
				elem.on(transitionEnd, handleEvent);
			}

			init();
		}
  };
};
module.exports = BodyDirective;