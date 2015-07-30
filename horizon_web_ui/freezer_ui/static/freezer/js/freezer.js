(function () {
    'use strict';
    angular.module('hz').controller('DestinationCtrl', function ($scope, $http, $location) {
        $scope.query = '';

        $http.get($location.protocol() + "://" + $location.host() + ":" + $location.port() + "/freezer_ui/api/clients").
            success(function(data, status, headers, config) {
                $scope.clients = data
            });
        $scope.searchComparator = function (actual, expected) {
            return actual.description.indexOf(expected) > 0
        };
    });
}());
