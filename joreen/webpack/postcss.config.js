const purgecss = require("@fullhuman/postcss-purgecss")({
  content: [
    __dirname + "/../*/templates/**/*.html",
    __dirname + "/../static/**/*.js",
    __dirname + "/../*/static/**/*.js",
  ],
  defaultExtractor: content => content.match(/[\w-/:]+(?<!:)/g) || []
});
const cssnano = require("cssnano")({ preset: "default" });

module.exports = {
  plugins: [
    require("tailwindcss")(__dirname + "/tailwind.config.js"),
    require("autoprefixer"),
    ...(process.env.NODE_ENV === "production" ? [purgecss] : []),
    ...(process.env.NODE_ENV === "production" ? [cssnano] : [])
  ]
};
