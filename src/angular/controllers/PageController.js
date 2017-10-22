'use strict';

var PageController = function ($rootScope, $scope, $timeout, $window, $location, FeedService) {

	/*
	 *	Parameters
	 */
	$scope.isIE = (navigator.userAgent.indexOf('MSIE') !== -1 || navigator.appVersion.indexOf('Trident/') > 0);
	$scope.isFF = navigator.userAgent.toLowerCase().indexOf('firefox/') > -1;
    $scope.blogger = [];
    $scope.theme = 'blue';
  

    $scope.$on('$locationChangeSuccess', function (event, next, current) {
        var arr = $location.path().split('/');
        arr.shift();
        // console.log(arr);
    });


    /*
     *  Event Handler
     */
    var handleEvent = function (e, attr) {
        var eventType = e.type ? e.type : e.name;

        console.log('eventType', eventType);

        switch(eventType) {
            case 'header.on':
                $scope.theme = 'blue';
            break;
            case 'work.on':
                $scope.theme = 'white';
            break;
            case 'me.on':
                $scope.theme = 'red';
            break;
        }

        console.log('$scope.theme', $scope.theme);

        $timeout(function () {
            $scope.$apply();
        });
    };


    /*
     *  Methods
     */
    var _handleDataResponse = function (data) {
        $scope.blogger = data.items;
    };


    var init = function () {


        $scope.$on('header.on', handleEvent);
        // $scope.$on('header.off', handleEvent);
        $scope.$on('work.on', handleEvent);
        // $scope.$on('work.off', handleEvent);
        $scope.$on('me.on', handleEvent);
        // $scope.$on('me.off', handleEvent);
    };

    init();
};
module.exports = PageController;
