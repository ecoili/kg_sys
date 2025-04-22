import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      /*'dayjs': 'dayjs/esm',  //主入口
      'dayjs/plugin': 'dayjs/esm/plugin', // 处理插件，映射到xxx/index.js*/
      // 'dayjs': path.resolve(__dirname, 'node_modules/dayjs/esm/index.js'),
      // 'dayjs/plugin': path.resolve(__dirname, 'node_modules/dayjs/esm/plugin')
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
    },
    watch: {
      // 限制监听的文件范围
      ignored: ['node_modules', 'dist']
    }
  },
  optimizeDeps: {
  // noDiscovery: true,
  include: ['dayjs',
    'dayjs/plugin/customParseFormat',
    'dayjs/plugin/localeData',
    'dayjs/plugin/advancedFormat',
    'dayjs/plugin/weekOfYear',
    'dayjs/plugin/weekYear',
    'dayjs/plugin/dayOfYear',
    'dayjs/plugin/isSameOrAfter',
    'dayjs/plugin/isSameOrBefore']
},
  build: {
    // 关闭 sourcemap 减少内存
    sourcemap: false,
  }
})
