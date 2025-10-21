const path = require('path');

module.exports = {
  devServer: {
    // Fix for webpack dev server allowedHosts error
    allowedHosts: 'all',
    // Additional webpack dev server options
    host: 'localhost',
    port: 3000,
    // Client configuration for webpack dev server
    client: {
      webSocketURL: {
        hostname: 'localhost',
        pathname: '/ws',
        port: 3000,
        protocol: 'ws',
      },
    },
  },
  webpack: {
    configure: (webpackConfig, { env, paths }) => {
      // Ensure proper configuration for development
      if (env === 'development') {
        webpackConfig.devServer = {
          ...webpackConfig.devServer,
          allowedHosts: 'all',
          host: 'localhost',
          port: 3000,
        };
      }
      return webpackConfig;
    },
  },
};
