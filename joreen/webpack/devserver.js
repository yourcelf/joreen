var webpack = require("webpack");
var WebpackDevServer = require("webpack-dev-server");
var config = require("./config.dev.js");
var devserverHost = process.env.DEVSERVER_HOST
  ? process.env.DEVSERVER_HOST
  : "localhost";
var devserverPort = 3000;

new WebpackDevServer(webpack(config), {
  publicPath: config.output.publicPath,
  hot: true,
  host: devserverHost,
  port: devserverPort,
  inline: true,
  historyApiFallback: true,
  noInfo: true,
  headers: {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
    "Access-Control-Allow-Headers":
      "X-Requested-With, content-type, Authorization"
  }
}).listen(devserverPort, "0.0.0", function(err, result) {
  if (err) {
    console.log(err);
  }
  console.log("Listening at http://localhost:3000");
});
