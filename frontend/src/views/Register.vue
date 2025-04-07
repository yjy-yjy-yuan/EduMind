<template>
  <div class="register-container">
    <div class="register-card">
      <div class="register-header">
        <h2>注册账号</h2>
        <p>加入 AI-EdVision，开启智能学习之旅</p>
      </div>
      
      <div class="register-form">
        <el-steps :active="activeStep" finish-status="success" simple style="margin-bottom: 20px">
          <el-step title="基本信息" />
          <el-step title="个人资料" />
          <el-step title="学习偏好" />
        </el-steps>
        
        <!-- 步骤1：基本信息 -->
        <div v-if="activeStep === 0">
          <div class="form-group">
            <label for="username">用户名</label>
            <el-input 
              v-model="registerForm.username" 
              placeholder="请输入用户名" 
              :prefix-icon="User"
            />
          </div>
          
          <div class="form-group">
            <label for="email">邮箱</label>
            <el-input 
              v-model="registerForm.email" 
              placeholder="请输入邮箱" 
              :prefix-icon="Message"
            />
          </div>
          
          <div class="form-group">
            <label for="password">密码</label>
            <el-input 
              v-model="registerForm.password" 
              type="password" 
              placeholder="请输入密码" 
              :prefix-icon="Lock"
              show-password
            />
          </div>
          
          <div class="form-group">
            <label for="confirmPassword">确认密码</label>
            <el-input 
              v-model="confirmPassword" 
              type="password" 
              placeholder="请再次输入密码" 
              :prefix-icon="Lock"
              show-password
            />
          </div>
          
          <div class="form-actions">
            <el-button 
              type="primary" 
              class="next-button" 
              @click="nextStep"
            >
              下一步
            </el-button>
          </div>
        </div>
        
        <!-- 步骤2：个人资料 -->
        <div v-if="activeStep === 1">
          <div class="form-group">
            <label for="gender">性别</label>
            <el-select v-model="registerForm.gender" placeholder="请选择性别" style="width: 100%">
              <el-option label="男" value="男"></el-option>
              <el-option label="女" value="女"></el-option>
              <el-option label="其他" value="其他"></el-option>
              <el-option label="不愿透露" value="不愿透露"></el-option>
            </el-select>
          </div>
          
          <div class="form-group">
            <label for="education">学历</label>
            <el-select v-model="registerForm.education" placeholder="请选择学历" style="width: 100%">
              <el-option label="高中及以下" value="高中及以下"></el-option>
              <el-option label="专科" value="专科"></el-option>
              <el-option label="本科" value="本科"></el-option>
              <el-option label="硕士" value="硕士"></el-option>
              <el-option label="博士" value="博士"></el-option>
            </el-select>
          </div>
          
          <div class="form-group">
            <label for="occupation">职业</label>
            <el-select v-model="registerForm.occupation" placeholder="请选择职业" style="width: 100%">
              <el-option label="学生" value="学生"></el-option>
              <el-option label="教师" value="教师"></el-option>
              <el-option label="IT/互联网" value="IT/互联网"></el-option>
              <el-option label="金融" value="金融"></el-option>
              <el-option label="医疗" value="医疗"></el-option>
              <el-option label="其他" value="其他"></el-option>
            </el-select>
          </div>
          
          <div class="form-group">
            <label for="bio">个人简介</label>
            <el-input 
              v-model="registerForm.bio" 
              type="textarea" 
              placeholder="请简单介绍一下自己" 
              :rows="3"
            />
          </div>
          
          <div class="form-actions">
            <el-button 
              class="prev-button" 
              @click="prevStep"
            >
              上一步
            </el-button>
            <el-button 
              type="primary" 
              class="next-button" 
              @click="nextStep"
            >
              下一步
            </el-button>
          </div>
        </div>
        
        <!-- 步骤3：学习偏好 -->
        <div v-if="activeStep === 2">
          <div class="form-group">
            <label for="learning_direction">学习方向</label>
            <el-select 
              v-model="registerForm.learning_direction" 
              placeholder="请选择您感兴趣的学习方向" 
              style="width: 100%"
            >
              <el-option label="高等数学" value="高等数学"></el-option>
              <el-option label="线性代数" value="线性代数"></el-option>
              <el-option label="英语" value="英语"></el-option>
              <el-option label="计算机科学" value="计算机科学"></el-option>
              <el-option label="物理" value="物理"></el-option>
              <el-option label="化学" value="化学"></el-option>
              <el-option label="生物" value="生物"></el-option>
              <el-option label="经济学" value="经济学"></el-option>
              <el-option label="其他" value="其他"></el-option>
            </el-select>
          </div>
          
          <div class="form-actions">
            <el-button 
              class="prev-button" 
              @click="prevStep"
            >
              上一步
            </el-button>
            <el-button 
              type="primary" 
              class="register-button" 
              :loading="loading" 
              @click="handleRegister"
            >
              完成注册
            </el-button>
          </div>
        </div>
        
        <div class="form-footer">
          <p>已有账号？<router-link to="/login" class="login-link">立即登录</router-link></p>
        </div>
      </div>
    </div>
    
    <!-- 提示消息 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="30%"
      align-center
    >
      <span>{{ dialogMessage }}</span>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">关闭</el-button>
          <el-button v-if="registerSuccess" type="primary" @click="goToLogin">
            去登录
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, Message } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import authStore from '../store/auth'

const router = useRouter()
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const dialogMessage = ref('')
const registerSuccess = ref(false)
const confirmPassword = ref('')
const activeStep = ref(0)

// 注册表单
const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  gender: '',
  education: '',
  occupation: '',
  learning_direction: '',
  bio: ''
})

// 显示对话框
const showDialog = (title, message, success = false) => {
  dialogTitle.value = title
  dialogMessage.value = message
  registerSuccess.value = success
  dialogVisible.value = true
}

// 验证邮箱格式
const validateEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email)
}

// 下一步
const nextStep = () => {
  if (activeStep.value === 0) {
    // 验证基本信息
    if (!registerForm.username) {
      ElMessage.error('请输入用户名')
      return
    }
    if (!registerForm.email) {
      ElMessage.error('请输入邮箱')
      return
    }
    if (!validateEmail(registerForm.email)) {
      ElMessage.error('邮箱格式不正确')
      return
    }
    if (!registerForm.password) {
      ElMessage.error('请输入密码')
      return
    }
    if (registerForm.password !== confirmPassword.value) {
      ElMessage.error('两次输入的密码不一致')
      return
    }
  }
  
  activeStep.value++
}

// 上一步
const prevStep = () => {
  activeStep.value--
}

// 处理注册
const handleRegister = async () => {
  loading.value = true
  
  try {
    // 使用 authStore 的 register 方法进行注册
    const result = await authStore.register(registerForm)
    
    if (result.success) {
      // 注册成功后自动登录
      const loginResult = await authStore.login(registerForm.username, registerForm.password)
      
      if (loginResult.success) {
        // 登录成功，显示成功消息
        ElMessage({
          message: '注册并登录成功',
          type: 'success',
          duration: 2000
        })
        
        // 跳转到首页
        router.push('/')
      } else {
        // 注册成功但登录失败，提示用户去登录
        showDialog('注册成功', '您的账号已创建成功，请登录', true)
      }
    } else {
      showDialog('注册失败', result.message)
    }
  } catch (error) {
    console.error('注册错误:', error)
    showDialog('注册失败', error.response?.data?.message || '注册失败，请稍后再试')
  } finally {
    loading.value = false
  }
}

// 跳转到登录页
const goToLogin = () => {
  dialogVisible.value = false
  router.push('/login')
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea, #764ba2);
  padding: 20px;
}

.register-card {
  width: 100%;
  max-width: 500px;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  animation: fadeInUp 0.8s ease-out;
}

.register-header {
  padding: 25px 30px;
  text-align: center;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
}

.register-header h2 {
  margin: 0 0 10px;
  font-size: 24px;
  font-weight: 600;
}

.register-header p {
  margin: 0;
  font-size: 16px;
  opacity: 0.9;
}

.register-form {
  padding: 30px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 30px;
}

.next-button, .prev-button, .register-button {
  width: 48%;
  height: 44px;
  font-size: 16px;
  transition: all 0.3s ease;
}

.register-button {
  width: 100%;
}

.next-button:hover, .register-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.form-footer {
  margin-top: 20px;
  text-align: center;
  color: #666;
}

.login-link {
  color: #4F46E5;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.3s ease;
}

.login-link:hover {
  color: #6366F1;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
