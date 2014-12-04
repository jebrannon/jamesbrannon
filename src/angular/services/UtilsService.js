'use strict';

var UtilsService = function() {
	var that = {};
	that.formatString = function(value, obj) {
		var rformat = /\{(\w+)\}/g;
		if (typeof value === 'undefined' || typeof value !== 'string') {
			return '';
		}
		if (typeof obj === 'undefined') {
			return value;
		}

		var formatter = function(m, p1, p2, p3, o, s) {
			return obj[p1] || m;
		};

		return value.replace(rformat, formatter);
	};
	that.stripHTML = function(str) {
		var newStr = str.replace(/(<([^>]+)>)/ig, '');
		newStr = newStr.replace(/\n/g, '§');
		newStr = newStr.replace(/\r/g, '§');
		var matches = newStr.match(/§/g);

		//  Fix erroneous new line characters
		if (matches && (matches.length === newStr.length)) {
			return false;
		} else {
			newStr = newStr.replace(/§/g, ' ');
		}

		//  Return string if it has length
		if (newStr.length) {
			return newStr;
		}
		else {
			return false;
		}
	};
	that.getImagesFromString = function(str) {
		var imgSearch = document.createElement('div');
		imgSearch.innerHTML = str;
		imgSearch = imgSearch.getElementsByTagName('img');
		var len = imgSearch.length;
		var inc = 0;
		var arr = [];
		while (len--) {
			arr.push(imgSearch[inc].src);
			inc++;
		}
		return arr;
	};
	that.formatDateString = function(str) {
		var d = new Date(str);
		return d.toDateString();
	};

	return that;
};
module.exports = UtilsService;