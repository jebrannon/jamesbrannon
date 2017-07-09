var gulp = require('gulp');
var awspublish = require('gulp-awspublish');
var aws = require('../config').aws;
var AWSSDK = require('aws-sdk');
var publisher = awspublish.create({
    params: {
        Bucket: aws.bucket
    },
    region: aws.region,
    credentials: new AWSSDK.SharedIniFileCredentials({profile: 'jamesbrannon.co.uk'})
});
var headers = {
  'Cache-Control': 'public, no-transform'
};


var PublishTask = function () {
    return gulp.src('./release/**/*')
      
      //  Gzip, Set Content-Encoding headers and add .gz extension 
      .pipe(awspublish.gzip())
     
      //  Publisher will add Content-Length, Content-Type and headers specified above 
      //  If not specified it will set x-amz-acl to public-read by default 
      .pipe(publisher.publish(headers))
     
      //  Create a cache file to speed up consecutive uploads 
      .pipe(publisher.cache())
     
      //  Print upload updates to console 
      .pipe(awspublish.reporter());
};
module.exports = PublishTask;