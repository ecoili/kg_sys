const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
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
  }
}
)
