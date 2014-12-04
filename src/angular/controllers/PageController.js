'use strict';

var PageController = function ($rootElement, $scope, $window, $location, FeedService) {

	/*
		Parameters
	*/
	$scope.isIE = (navigator.userAgent.indexOf('MSIE') !== -1 || navigator.appVersion.indexOf('Trident/') > 0);
	$scope.isFF = navigator.userAgent.toLowerCase().indexOf('firefox/') > -1;
  $scope.blogger = [];
  

  $scope.init = function () {

    //  Blogger feed
    FeedService.load({
      type: 'blogger',
      user: '5901719195104369005',
      key: 'AIzaSyDovySMd-tp2QpSKmQQDf3j43GbS5Pjip4',
      limit: 6
    })
    .then(_handleDataResponse)
    .catch (function (response) {
      console.log('CATCH: ', response);
    });
  };

  $scope.$on('$locationChangeSuccess', function (event, next, current) {
    var arr = $location.path().split('/');
    arr.shift();
    console.log(arr);
  });


  /*
  		Event Handler
  */
  var _handleEvent = function (e, attr) {
  	var eventType = e.type ? e.type : e.name;
  	var _$el = attr && attr.item ? attr.item : attr;
		switch(eventType) {
			case 'ng_Story_ready':
			break;
		}
  };


  /*
  		Methods
  */
  var _handleDataResponse = function (data) {
    $scope.blogger = data.items;
  };
};
module.exports = PageController;
