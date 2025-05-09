<!-- Register.vue -->
<script>
export default {
  name: 'PageRegister' // 或 TheRegister、AppRegister
}
</script>

<template>
  <div class="register-container">
    <el-card class="register-box">
      <h2>用户注册</h2>
      <el-form :model="form" :rules="rules" ref="registerForm">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item prop="phone">
          <el-input v-model="form.phone" placeholder="手机号" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
    v-model="form.password"
    :type="showPassword ? 'text' : 'password'"
    placeholder="密码"
  >
    <template #suffix>
      <el-icon @click="showPassword = !showPassword" style="cursor: pointer">
        <component :is="showPassword ? View : Hide" />
      </el-icon>
    </template>
  </el-input>
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
        <el-button type="primary" @click="handleRegister">注册</el-button>
        <el-button link @click="$router.push('/auth/login')">去登录</el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { getCaptcha, register } from '@/api/auth';
import { ElMessage } from 'element-plus';
import { View, Hide } from '@element-plus/icons-vue'

const router = useRouter()
const showPassword = ref(false)
const form = ref({
  username: '',
  phone: '',
  password: '',
  captcha: '',
  captcha_id: '',
})
const captchaImage = ref('')

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式错误', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少8位', trigger: 'blur' }
  ],
  captcha: [{ required: true, message: '请输入验证码', trigger: 'blur' }]
};

// const refreshCaptcha = async () => {
//   const res = await getCaptcha();
//   captchaImage.value = `data:image/png;base64,${res.data.image}`;
//   form.value.captcha_id = res.data.captcha_id;
// };
const refreshCaptcha = async () => {
  try {
    // const res = await getCaptcha();
    // captchaImage.value = `data:image/png;base64,${res.data.image}`;
    // form.value.captcha_id = res.data.captcha_id;
    const response = await getCaptcha(); // 这里response已经是处理过的data
    if (response && response.image) {
      captchaImage.value = response.image;
      form.value.captcha_id = response.captcha_id;
    } else {
      console.error('验证码数据格式不正确:', response);
    }
  } catch (error) {
    console.error('Failed to load captcha:', error);
    ElMessage.error('加载验证码失败');
  }
};

const handleRegister = async () => {
  // try {
  //   await register(form.value)
  //   ElMessage.success('注册成功')
  //   await router.push('/auth/login')
  // } catch (error) {
  //   /*ElMessage.error(error.response?.data?.message || '注册失败');
  //   await refreshCaptcha()*/
  //   //统一修改
  //   console.log(error.message)
  //   ElMessage.error(error.message || '注册失败')
  //   refreshCaptcha()
  // }
  try {
    const res = await register(form.value)
    if (res && res.code === 201) {  // 明确检查成功状态
      ElMessage.success(res.message || '注册成功')
      await router.push('/auth/login')
    } else {
      ElMessage.error(res.message || '注册失败')
      refreshCaptcha()
    }
  } catch (error) {
    console.error('Registration error:', error)
    ElMessage.error(error.message || '注册失败')
    refreshCaptcha()
  }
}

onMounted(() => {
  refreshCaptcha()
})
</script>

<style scoped>
/* 复用登录页样式 */
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: url('@/assets/airport_photo2.jpg') no-repeat center center fixed;
  background-size: cover;
}
.register-box {
  width: 400px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.9); /* 给卡片添加半透明白色背景 */
}
</style>