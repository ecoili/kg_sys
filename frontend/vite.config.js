import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    proxy: {
      '/api': {  // 前端请求前缀
        target: 'http://127.0.0.1:5000',  // Flask地址,一定要用127.0.0.1强制使用ipv4!!!不然默认使用ipv6请求到不了后端！！！
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''), // 移除/api前缀
        configure: (proxy) => {
          proxy.on('proxyReq', (req) => {
            console.log('[Vite Proxy] 请求路径:', req.path)  // 检查重写后的路径
          });
        }
      }
    }
  }
})
