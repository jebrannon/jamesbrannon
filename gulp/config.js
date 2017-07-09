var develop = './develop/';
var release = './release/';
var src = './src/';

module.exports = {
	aws: {
		path: '//jamesbrannon.co.uk.s3-website.eu-west-2.amazonaws.com',
		bucket: 'jamesbrannon.co.uk',
		region: 'eu-west-2'
	},
	build: {
		develop: develop,
		release: release,
	},
	markup: {
		src: src + 'markup/html/**/*',
		watch: src + 'markup/**/*.html'
	},
	less: {
		src: src + 'less/*.less',
		watch: src + 'less/**/*.less'
	},
	libs: {
		src: src + 'libs/**/*',
		watch: src + 'libs/**/*.js'
	},
	angular: {
		src: src + 'angular/app.js',
		watch: src + 'angular/**/*.js'
	},
	images: {
		dev: develop + '/images',
		release: release + '/images',
		src: src + 'images/*'
	},
	svg: {
		markup: src + 'markup/index.html',
		src: src + 'images/svg/*.svg'
	},
	fonts: {
		dev: develop + '/fonts',
		release: release + '/fonts',
		src: src + 'fonts/**'
	}
};