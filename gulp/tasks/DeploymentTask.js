var gulp = require('gulp');
var GulpSSH = require('gulp-ssh');
var fs = require('fs');

var config = {
  host: 'jamesbrannon.co.uk',
  port: 22,
  username: 'jbrannon',
  privateKey: fs.readFileSync('/Users/james/.ssh/arvixe_rsa'),
  passphrase: "Valiant11"
}
 
var SSH = new GulpSSH({
  ignoreErrors: false,
  sshConfig: config
});


var DeploymentTask = function () {

	return gulp
		.src('./release/**/*')
		.pipe(SSH.dest('public_html/'))
};
module.exports = DeploymentTask;