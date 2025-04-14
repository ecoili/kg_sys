const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  configureWebpack: {
    resolve: {
      fallback: {
        path: require.resolve("path-browserify")
      }
    }
  },
  css: {
    loaderOptions: {
      sass: {
        implementation: require('sass'), // 使用 Dart Sass
      },
    },
  },
  devServer: {   //开发环境代理
    proxy: {
      '/api': {  // 代理所有以 `/api` 开头的请求
        target: 'http://localhost:5000',  // Flask 后端地址
        changeOrigin: true,
        pathRewrite: {
          '^/api': ''  // 去掉 `/api` 前缀
        }
      }
    }
  },
  chainWebpack: config => {
    config.resolve.alias.set('vue', '@vue/compat')
    config.plugin('define').tap(args => {
      args[0]['process.env'].BASE_URL = JSON.stringify(process.env.BASE_URL)
      return args
    })
    config.module
      .rule('jsx')
      .test(/\.jsx$/)
      .use('babel-loader')
      .loader('babel-loader')
      .end()
  }
}
)
