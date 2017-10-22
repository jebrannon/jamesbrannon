'use strict';

var RingsDirective = function ($timeout) {
	return {
		restrict: 'AE',
		link: function(scope, elem, attrs) {
			var AnimationEnd = 'animationend webkitAnimationEnd oanimationend MSAnimationEnd';
			var AnimationStart = 'animationstart webkitAnimationStart oanimationstart MSAnimationStart';
			var rings = {};

			var handleEvent = function (e, data) {
				var eventType = e.type ? e.type : e.name;
				switch(eventType) {
					case 'window.scroll':

						willSizeRingsBasedwindow.scroll();
						break;
					case 'animationstart':
					case 'webkitAnimationStart':
					case 'oanimationstart':
					case 'MSAnimationStart':
						
						break;
					case 'animationend':
					case 'webkitAnimationEnd':
					case 'oanimationend':
					case 'MSAnimationEnd':

						handleAnimationEvents(e);
						break;
				}
			};
			
			var handleAnimationEvents = function (e) {
				var transition = $(e.target).attr('data-transition');

				switch(transition) {
					case 'StartOfPulse':

						//  Animate in outer rings
						elem.addClass('animate');
						break;
				}
			};

			var willSizeRingsBasedwindow.scroll = function () {
				var limit = window.innerHeight / 2;
				var ratio;
				var scale1;
				var scale2;
				var scale3;
				var scale4;
				var top;

				//  Ratio of scroll postion to max size of ring
				ratio = Number( (document.body.scrollTop/limit).toFixed(2));

				//  Ensre the ring never disppears completely
				if (ratio <= 1) {

					//  Calculate top position
					top = 6.4 - Math.round(22 * ratio);

					//  Calculate dynamic scales for rings
					scale1 = ((1 - ratio) >= 0.15) ? (1 - ratio) : 0.15;
					scale2 = ((2 - (ratio * 2)) >= 0.15) ? (2 - (ratio * 2)) : 0.15;
					scale3 = ((4 - (ratio * 4)) >= 0.15) ? (4 - (ratio * 4)) : 0.15;
					scale4 = ((6 - (ratio * 6)) >= 0.15) ? (6 - (ratio * 6)) : 0.15;

					//  Add scale transforms
					rings.one.style.transform = 'translateX(-50%) scale(' + scale1 + ')';
					rings.two.style.transform = 'translateX(-50%) scale(' + scale2 + ')';
					rings.three.style.transform = 'translateX(-50%) scale(' + scale3 + ')';
					rings.four.style.transform = 'translateX(-50%) scale(' + scale4 + ')';


					//  Position elements vertically
					rings.one.style.top = top + '%';
					rings.two.style.top = top + '%';
					rings.three.style.top = top + '%';
					rings.four.style.top = top + '%';
				}
			};

			var init = function () {

				//  Define ring elements
				rings.one = elem.find('.ring-1')[0]; 
				rings.two = elem.find('.ring-2')[0]; 
				rings.three = elem.find('.ring-3')[0]; 
				rings.four = elem.find('.ring-4')[0]; 

				//  Start the pulse animation
				elem.addClass('pulse');

				//  Add listeners
				scope.$on('window.scroll', handleEvent);
				elem.on(AnimationEnd, handleEvent);
				elem.on(AnimationStart, handleEvent);
			};

			$timeout(init);
		}
	};
};
module.exports = RingsDirective;