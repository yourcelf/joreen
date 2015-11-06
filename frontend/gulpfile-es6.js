"use strict";
const babelify = require("babelify")
const browserify = require("browserify")
const browserSync = require("browser-sync").create()
const buffer = require("vinyl-buffer")
const concat = require("gulp-concat")
const cssimport = require("gulp-cssimport")
const del = require("del")
const eslint = require("gulp-eslint")
const filter = require("gulp-filter")
const gulp = require("gulp")
const less = require("gulp-less")
const minifyCSS = require("gulp-minify-css")
const nib = require("nib")
const source = require("vinyl-source-stream")
const sourcemaps = require("gulp-sourcemaps")
const streamqueue = require("streamqueue")
const stylus = require("gulp-stylus")
const uglify = require("gulp-uglify")

const DEST = "./build/"
const JSDEST = "./build/js/"

const IS_PROD = process.env.NODE_ENV !== "development"

gulp.task("clean", function(done) {
  del([DEST], done)
})

gulp.task("img", function() {
  return gulp.src("./src/img/**")
    .pipe(gulp.dest(DEST + "img/"))
})

gulp.task("js", function() {
  let s = browserify({entries: ["./src/js/main.js"]})
  s = s.transform(babelify)
  s = s.bundle(function(err) {
    if (err) {
      console.log(err.toString());
      this.emit('end');
    }
  })
  s = s.pipe(source("js/main.js"))
  s = s.pipe(buffer())
  s = s.pipe(sourcemaps.init({loadMaps: true}))
  if (IS_PROD) s = s.pipe(uglify())
  if (IS_PROD) s = s.pipe(gulp.dest(DEST))
  s = s.pipe(sourcemaps.write("./"))
  s = s.pipe(gulp.dest(DEST))
  return s;
})

gulp.task("css", function() {
  let s = streamqueue({objectMode: true},
    gulp.src(["src/css/bootstrap/bootstrap.less"]).pipe(less()),
    gulp.src(["src/**/*.styl"]).pipe(stylus({use: nib()}))
  )
  s = s.pipe(cssimport())
  s = s.pipe(sourcemaps.init())
  s = s.pipe(concat({path: "./css/all.css", cwd: "."}))
  s = s.pipe(minifyCSS({keepBreaks: true}))
  s = s.pipe(sourcemaps.write("./"))
  s = s.pipe(gulp.dest(DEST))
  // auto-inject css if we have a browserSync session open.
  s = s.pipe(filter('**/*.css')) // filter out .map's, etc.
  s = s.pipe(browserSync.stream())
})

gulp.task("fonts", function() {
  return gulp.src([
      "bower_components/font-awesome/fonts/*"
    ]).pipe(gulp.dest(DEST + "fonts/"))
})

gulp.task('html', function() {
  return gulp.src(['src/**/*.html']).pipe(gulp.dest(DEST))
})

gulp.task("lint", function() {
  return gulp.src(["src/**/*.js", "src/**/*.jsx"])
    .pipe(eslint())
    .pipe(eslint.format())

})

gulp.task("watch-lint", ["lint"], function() {
  gulp.watch(["src/**/*.js", "src/**/*.jsx"], ["lint"])
})

gulp.task("watch", ["build"], function(cb) {
  browserSync.init({
    server: {
      baseDir: "./build"
    }
  })

  gulp.watch(["src/img/**"], ['reload-img'])
  gulp.watch(["src/**/*.js", "src/**/*.jsx"], ['reload-js'])
  gulp.watch(["src/**/*.styl", "src/**/*.less"], ['css'])
  gulp.watch(["src/**/*.html"], ['reload-html'])
})

// This indirection is needed to make sure that the task finishes before
// ``browserSync.reload`` is called.
gulp.task('reload-js', ['js'], browserSync.reload);
gulp.task('reload-img', ['img'], browserSync.reload);
gulp.task('reload-html', ['html'], browserSync.reload);

gulp.task("build", ["img", "fonts", "js", "css", "html"])
gulp.task("default", ["build"])
