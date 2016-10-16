var develop = './develop/';
var release = './release/';
var src = './src/';

module.exports = {
	markup: {
		index: {
			dev: develop,
			release: release,
			src: src + 'html/*.html'
		},
		views: {
			dev: develop + 'html/views/',
			release: release + 'html/views/',
			src: src + 'html/views/**/*'
		},
		directives: {
			dev: develop + 'html/directives/',
			release: release + 'html/directives/',
			src: src + 'html/directives/**/*'
		},
		watch: src + 'html/**/*.html'
	},
	less: {
		dev: develop + '/css',
		release: release + '/css',
		src: src + 'less/*.less',
		watch: src + 'less/**/*.less'
	},
	libs: {
		dev: develop + '/js',
		release: release + '/js',
		src: src + 'libs/**/*',
		watch: src + 'libs/**/*.js'
	},
	angular: {
		dev: develop + '/js',
		release: release + '/js',
		src: src + 'angular/app.js',
		watch: src + 'angular/**/*.js'
	},
	images: {
		dev: develop + '/images',
		release: release + '/images',
		src: src + 'images/*'
	},
	svg: {
		dev: develop + '/images/svg',
		release: release + '/images/svg',
		src: src + 'images/svg/*.svg'
	},
	fonts: {
		dev: develop + '/fonts',
		release: release + '/fonts',
		src: src + 'fonts/**'
	},
	server: {
		dev: {
			dir: develop,
			port: 3000
		},
		release: {
			dir: release,
			port: 8080
		}
	}
};