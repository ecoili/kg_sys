<!-- Login.vue -->
<script>
export default {
  name: 'PageLogin' // 或 TheLogin、AppLogin
}
</script>

<template>
  <div class="login-container">
    <el-card class="login-box">
      <h2>用户登录</h2>
      <el-form :model="form" :rules="rules" ref="loginForm">
        <el-form-item prop="phone">
          <el-input v-model="form.phone" placeholder="手机号" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" />
        </el-form-item>
        <el-form-item prop="captcha">
          <div class="captcha-wrapper">
            <el-input v-model="form.captcha" placeholder="验证码" />
            <img
              :src="captchaImage"
              @click="refreshCaptcha"
              class="captcha-image"
              v-if="captchaImage"
            />
          </div>
        </el-form-item>
        <el-button type="primary" @click="handleLogin">登录</el-button>
        <el-button link @click="$router.push('/auth/register')">去注册</el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getCaptcha, login } from '@/api/auth'
import { ElMessage } from 'element-plus'

const router = useRouter();

// 表单数据
const form = ref({
  phone: '',
  password: '',
  captcha: '',
  captcha_id: '',
});

// 验证码图片 本地存储
const captchaImage = ref('')

// 表单验证规则
const rules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式错误', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少8位', trigger: 'blur' }
  ],
  captcha: [
    { required: true, message: '请输入验证码', trigger: 'blur' }
  ]
};


// 刷新验证码

const refreshCaptcha = async () => {
  console.log('refreshCaptcha called')
  try {
    const response = await getCaptcha(); // 这里response已经是处理过的data
    if (response && response.image) {
      captchaImage.value = response.image;
      form.value.captcha_id = response.captcha_id;
    } else {
      console.error('验证码数据格式不正确:', response)
    }
  } catch (error) {
    console.error('获取验证码失败:', error)
    // 可以在这里显示错误提示给用户
  }
}
 // 登录状态，防止重复提交
const loading = ref(false)
// 登录逻辑
const handleLogin = async () => {
  console.log('handleLogin called')
  console.log('提交的数据:', JSON.stringify(form.value)) // 添加这行检查数据
  if(loading.value) return
  loading.value = true
  try {
    const res = await login({
      phone: form.value.phone,
      password: form.value.password,
      captcha: form.value.captcha,
      captcha_id: form.value.captcha_id
    })
    // 检查实际返回结构
    console.log('Raw response:', res)
    ElMessage.success('登录成功')
    //将返回的access_token存入浏览器本地存储
    //正常返回的是解构后的数据，data:{'access_token':xxxx,xxxxx},见auth.js响应拦截器
    localStorage.setItem('access_token', res.access_token)
    //检查是否存入成功
    console.log('Stored token:', localStorage.getItem('access_token'))
    router.push('/app/dashboard')
  } catch (error) {
    console.error('Login error details:', error) // 打印完整错误对象
  /*let errorMessage = '登录失败'
  if (error.response) {
    // 来自后端的错误响应
    errorMessage = error.response.data?.message ||
                  error.response.data?.error ||
                  error.response.statusText
  } else if (error.request) {
    // 请求已发出但无响应
    errorMessage = '网络错误，请检查连接'
  }
  ElMessage.error(errorMessage)
  //非密码/凭证错误，刷新验证码
   if (![401, 403].includes(error.response?.status)) {
    refreshCaptcha();
  }*/
    ElMessage.error(error.message || '登录失败')
    refreshCaptcha()
  } finally {
    loading.value = false;
  }
}

// 初始化时加载验证码
onMounted(() => {
  refreshCaptcha();
});
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: url('@/assets/airport_photo1.jpg') no-repeat center center fixed;
  background-size: cover;
}

.login-box {
  width: 400px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.85); /* 半透明白色背景 */
  backdrop-filter: blur(2px); /* 叠加轻微模糊增强质感 */
  border-radius: 10px;
}
.captcha-wrapper {
  display: flex;
  gap: 10px;
}
.captcha-image {
  height: 40px;
  cursor: pointer;
  border: 1px solid #ddd;
}
</style>