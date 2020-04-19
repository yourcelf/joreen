"use strict";

const path = require("path");
const webpack = require("webpack");
const BundleTracker = require("webpack-bundle-tracker");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

const root = path.join(__dirname, "..");
const localhost = "http://localhost:3000";
//const localhost = "http://192.168.1.101:3000"

const postCssLoader = {
  loader: "postcss-loader",
  options: {
    config: { path: path.join(__dirname, "postcss.config.js") }
  }
};
const cssLoader = { loader: "css-loader", options: { importLoaders: 1 } };

function urlLoader(ext, mimetype) {
  return {
    test: new RegExp(`\.${ext}(\\?v=.*)?$`),
    loader: `url-loader?limit=10000&mimetype=${mimetype}`
  };
}

function clearNulls(arr) {
  return arr.filter(a => a !== null);
}

function buildEntryPoints(isProd) {
  const entry = {};
  [
    ["main", path.join(root, "static", "index.js")],
  ].forEach(point => {
    const name = point[0];
    const files = point.slice(1);
    if (isProd) {
      entry[name] = files;
    } else {
      entry[name] = [
        "webpack-dev-server/client?" + localhost,
        "webpack/hot/only-dev-server",
        ...files
      ];
    }
  });
  return entry;
}

function outputPath(isProd) {
  // Prod goes to "tmp" so we can check for changes and switch after a
  // successful build (see ./build_prod_assets.sh).  Dev goees to "dev" for
  // instant reloads.
  return path.join(root, "static", isProd ? "tmp" : "dev");
}

/**
 * Main configuration building function. Call with boolean "isProd".
 */
module.exports.buildConfig = isProd => ({
  mode: isProd ? "production" : "development",
  devtool: isProd ? "source-map" : "eval-source-map",
  entry: buildEntryPoints(isProd),
  output: {
    path: outputPath(isProd),
    filename: "[name]-[hash].js",
    sourceMapFilename: "[name]-[hash].js.map",
    publicPath: isProd ? "/static/dist/" : localhost + "/static/dev/"
  },
  plugins: clearNulls([
    // Set NODE_ENV=production on prod.
    isProd
      ? new webpack.DefinePlugin({
          "process.env": { NODE_ENV: JSON.stringify("production") }
        })
      : null,
    // Dev helpers.
    isProd ? null : new webpack.HotModuleReplacementPlugin(),
    // Export stats json for Django to track for paths to bundles.
    new BundleTracker({
      path: outputPath(isProd),
      filename: "webpack-stats.json"
    }),
    // Extract css to a file.
    new MiniCssExtractPlugin({
      filename: isProd ? "[name]-[hash].css" : "[name].css"
    })
  ]),
  module: {
    rules: [
      {
        test: /\.jsx?$/,
        exclude: /node_modules/,
        use: [
          {
            loader: "babel-loader",
            // Look in the parent directory for babel.config.js.
            options: { rootMode: "upward" }
          }
        ]
      },
      {
        test: /\.s?css$/,
        use: [
          { loader: MiniCssExtractPlugin.loader, options: { hmr: !isProd } },
          { loader: "css-loader", options: { importLoaders: 2 } },
          postCssLoader,
          {
            loader: "sass-loader",
            options: {
              sassOptions: {
                includePaths: [path.join(root, "node_modules"), "node_modules"],
                // Preserve comments, so we can pass directives through to purgecss
                outputStyle: "expanded",
              }
            }
          }
        ]
      },
      urlLoader("woff2", "application/font-woff2"),
      urlLoader("woff", "application/font-woff"),
      urlLoader("ttf", "application/x-font-ttf"),
      urlLoader("eot", "application/vnd.ms-fontobject"),
      urlLoader("svg", "image/svg+xml"),
      urlLoader("otf", "application/x-font-opentype")
    ]
  },
  resolve: {
    // The path wherein we expect modules directories (e.g. node_modules) to reside.
    modules: [path.join(root, "node_modules"), "node_modules"],
  }
});
