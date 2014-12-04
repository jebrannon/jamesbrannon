'use strict';

var Truncate = function ($sce) {

    return function (text, length, end) {
      if (isNaN(length)) {
        length = 10;
      }

      if (end === undefined) {
        end = '...';
      }

      //  Strip HTML
      text = text.replace(/(<([^>]+)>)/ig, '');

      if (text.length <= length || text.length - end.length <= length) {
        text = text;
      }
      else {
        for (var i = length-end.length; i < text.length; i++) {
          if (String(text)[i] === '.') {
            text = String(text).substring(0, (i - 1)) + end;
            break;
          }
          else if (String(text)[i] === ' ') {
            text = String(text).substring(0, i) + end;
            break;
          }
        }
      }
      return $sce.trustAsHtml(text);
    };
};
module.exports = Truncate;