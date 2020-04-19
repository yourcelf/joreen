module.exports = {
  presets: [
    "@babel/preset-react",
    [
      "@babel/preset-env",
      {
        targets: "> 0.25%, not dead, iOS >= 9",
        useBuiltIns: "usage",
        corejs: { version: 3 }
      }
    ]
  ],
  plugins: []
};
