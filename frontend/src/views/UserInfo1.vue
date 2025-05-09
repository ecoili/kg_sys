<template>
  <div class="user-info-container">
    <el-card class="user-info-card">
      <div class="header-section">
        <h2>个人中心</h2>
        <el-button
          type="primary"
          plain
          @click="goToDashboard"
          icon="el-icon-back">
          返回控制台
        </el-button>
      </div>

      <!-- 用户信息展示 -->
      <div class="info-section">
        <h3>基本信息</h3>
        <el-form label-width="100px">
<!--          <el-form-item label="头像">-->
<!--        <el-avatar :src="userInfo.avatar" :size="100" />-->
<!--        <el-upload-->
<!--          class="avatar-uploader"-->
<!--          action=""-->
<!--          :show-file-list="false"-->
<!--          :before-upload="beforeAvatarUpload"-->
<!--          :http-request="handleAvatarUpload">-->
<!--          <el-button type="primary" size="small">更换头像</el-button>-->
<!--        </el-upload>-->
<!--        </el-form-item>-->
          <el-form-item label="用户名">
            <span>{{ userInfo.username }}</span>
            <el-button link type="primary" @click="showUsernameEdit = true" icon="el-icon-edit">
            修改
          </el-button>
          </el-form-item>
          <el-form-item label="手机号">
            <span>{{ userInfo.phone }}</span>
          </el-form-item>
        </el-form>
      </div>

      <!-- 修改用户名表单 -->
      <el-dialog
        title="修改用户名"
        v-model="showUsernameEdit"
        width="30%">
        <el-form
          :model="usernameForm"
          :rules="usernameRules"
          ref="usernameFormRef">
          <el-form-item label="新用户名" prop="username">
            <el-input v-model="usernameForm.username" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showUsernameEdit = false">取消</el-button>
          <el-button type="primary" @click="updateUsername">确认</el-button>
        </template>
      </el-dialog>

      <!-- 修改密码表单 -->
      <div class="info-section">
        <h3>修改密码</h3>
        <el-form
          :model="passwordForm"
          :rules="passwordRules"
          ref="passwordFormRef"
          label-width="100px">
          <el-form-item label="当前密码" prop="currentPassword">
            <el-input
              v-model="passwordForm.currentPassword"
              type="password"
              show-password />
          </el-form-item>
          <el-form-item label="新密码" prop="newPassword">
            <el-input
              v-model="passwordForm.newPassword"
              type="password"
              show-password />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input
              v-model="passwordForm.confirmPassword"
              type="password"
              show-password />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              @click="updatePassword">
              修改密码
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
    getUserInfo,
    updateUsername as apiUpdateUsername,
    updatePassword as apiUpdatePassword,
    getAvatar,
    updateAvatar
} from '@/api/userinfo_fe'

const router = useRouter()

// 用户信息
const userInfo = reactive({
  username: '',
  phone: ''
})

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    const response = await getUserInfo()
    userInfo.username = response.username || localStorage.getItem('username') || '未登录用户'
    userInfo.phone = response.phone || '未知'
  } catch (error) {
    console.error('获取用户信息失败:', error)
    ElMessage.error('获取用户信息失败')
  }
}

// 修改用户名相关
const showUsernameEdit = ref(false)
const usernameFormRef = ref(null)
const usernameForm = reactive({
  username: ''
})

const usernameRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度在2到20个字符之间', trigger: 'blur' }
  ]
}
const passwordRules = {
  currentPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}
// 添加返回Dashboard的方法
const goToDashboard = () => {
  router.push('/app/dashboard')
}
const updateUsername = async () => {
  try {
    await usernameFormRef.value.validate()
    await apiUpdateUsername(usernameForm.username)

    ElMessage.success('用户名修改成功')
    userInfo.username = usernameForm.username
    localStorage.setItem('username', usernameForm.username)
    showUsernameEdit.value = false
  } catch (error) {
    console.error('修改用户名失败:', error)
    ElMessage.error(error.message || '修改用户名失败')
  }
}

// 修改密码相关
const passwordFormRef = ref(null)
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const updatePassword = async () => {
  try {
    await passwordFormRef.value.validate()
    await apiUpdatePassword(
      passwordForm.currentPassword,
      passwordForm.newPassword
    )

    ElMessage.success('密码修改成功，请重新登录')
    localStorage.removeItem('access_token')
    router.push('/auth/login')
  } catch (error) {
    console.error('修改密码失败:', error)
    ElMessage.error(error.message || '修改密码失败')
  }
}


// 初始化获取用户信息
onMounted(() => {
  fetchUserInfo()
  usernameForm.username = localStorage.getItem('username') || ''
})
</script>

<style scoped>
.user-info-container {
  display: flex;
  justify-content: center;
  padding: 20px;
}

.user-info-card {
  width: 600px;
  padding: 20px;
}

.info-section {
  margin-bottom: 30px;
}

.info-section h3 {
  margin-bottom: 20px;
  color: #409EFF;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}

.el-form-item {
  margin-bottom: 22px;
}
</style>