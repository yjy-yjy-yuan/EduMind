<template>
  <div class="register-container">
    <div class="register-card">
      <div class="register-header">
        <!-- 添加与顶部栏相同的logo -->
        <div class="logo-container">
          <i class="fas fa-graduation-cap logo-icon"></i>
          <span class="logo-text">视频智能伴学</span>
        </div>
        <h2>注册账号</h2>
        <p>加入视频智能伴学系统，开启智能学习之旅</p>
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
              @input="checkPasswordStrength(registerForm.password)"
            />
            <div v-if="passwordStrength === 0" class="password-feedback">密码应至少包含8个字符</div>
            <div v-else-if="passwordStrength === 1" class="password-feedback">密码较弱，请添加大写字母、小写字母、数字或特殊字符</div>
            <div v-else-if="passwordStrength === 2" class="password-feedback">密码较强，但可以通过添加更多字符类型来提高安全性</div>
            <div v-else class="password-feedback">密码强度良好</div>
            <el-button 
              type="text" 
              class="generate-password-button" 
              @click="generateStrongPassword"
            >
              生成强密码
            </el-button>
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
import { User, Lock, Message, RefreshRight } from '@element-plus/icons-vue'
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
const passwordStrength = ref(0)
const passwordFeedback = ref('')

// 注册表单
const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  gender: '',
  education: '',
  occupation: '',
  bio: '',
  learning_direction: ''
})

// 验证邮箱格式
const validateEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email)
}

// 检查密码强度
const checkPasswordStrength = (password) => {
  if (!password) {
    passwordStrength.value = 0
    passwordFeedback.value = ''
    return
  }
  
  let strength = 0
  let feedback = []
  
  // 长度检查
  if (password.length >= 8) {
    strength += 1
  } else {
    feedback.push('密码应至少包含8个字符')
  }
  
  // 包含大写字母
  if (/[A-Z]/.test(password)) {
    strength += 1
  } else {
    feedback.push('添加大写字母可提高安全性')
  }
  
  // 包含小写字母
  if (/[a-z]/.test(password)) {
    strength += 1
  } else {
    feedback.push('添加小写字母可提高安全性')
  }
  
  // 包含数字
  if (/[0-9]/.test(password)) {
    strength += 1
  } else {
    feedback.push('添加数字可提高安全性')
  }
  
  // 包含特殊字符
  if (/[^A-Za-z0-9]/.test(password)) {
    strength += 1
  } else {
    feedback.push('添加特殊字符可提高安全性')
  }
  
  passwordStrength.value = strength
  passwordFeedback.value = feedback.join('；')
}

// 生成随机强密码
const generateStrongPassword = () => {
  const length = 12
  const charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+'
  let password = ''
  
  // 确保至少包含一个大写字母、小写字母、数字和特殊字符
  password += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[Math.floor(Math.random() * 26)]
  password += 'abcdefghijklmnopqrstuvwxyz'[Math.floor(Math.random() * 26)]
  password += '0123456789'[Math.floor(Math.random() * 10)]
  password += '!@#$%^&*()-_=+'[Math.floor(Math.random() * 14)]
  
  // 填充剩余字符
  for (let i = 4; i < length; i++) {
    password += charset[Math.floor(Math.random() * charset.length)]
  }
  
  // 打乱密码字符顺序
  password = password.split('').sort(() => 0.5 - Math.random()).join('')
  
  registerForm.password = password
  confirmPassword.value = password
  checkPasswordStrength(password)
}

// 下一步
const nextStep = () => {
  // 步骤1验证
  if (activeStep.value === 0) {
    if (!registerForm.username) {
      showDialog('提示', '请输入用户名')
      return
    }
    if (!registerForm.email) {
      showDialog('提示', '请输入邮箱')
      return
    }
    if (!validateEmail(registerForm.email)) {
      showDialog('提示', '请输入有效的邮箱地址')
      return
    }
    if (!registerForm.password) {
      showDialog('提示', '请输入密码')
      return
    }
    if (registerForm.password.length < 8) {
      showDialog('提示', '密码长度不能少于8位')
      return
    }
    if (passwordStrength.value < 3) {
      showDialog('提示', '请设置更强的密码：' + passwordFeedback.value)
      return
    }
    if (registerForm.password !== confirmPassword.value) {
      showDialog('提示', '两次输入的密码不一致')
      return
    }
  }
  
  // 添加动画类
  const formContainer = document.querySelector('.register-form')
  formContainer.classList.add('slide-right')
  
  // 延迟切换步骤，等待动画完成
  setTimeout(() => {
    activeStep.value++
    formContainer.classList.remove('slide-right')
  }, 300)
}

// 上一步
const prevStep = () => {
  // 添加动画类
  const formContainer = document.querySelector('.register-form')
  formContainer.classList.add('slide-left')
  
  // 延迟切换步骤，等待动画完成
  setTimeout(() => {
    activeStep.value--
    formContainer.classList.remove('slide-left')
  }, 300)
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

// 显示对话框
const showDialog = (title, message, success = false) => {
  dialogTitle.value = title
  dialogMessage.value = message
  registerSuccess.value = success
  dialogVisible.value = true
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: calc(100vh - 84px);
  padding: 0;
  background: linear-gradient(135deg, #f5f7fa, #c3cfe2);
  overflow: hidden;
  position: fixed;
  top: 84px;
  left: 0;
  right: 0;
  bottom: 0;
}

.register-card {
  width: 100%;
  max-width: 550px;
  max-height: 90vh;
  overflow-y: auto;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  animation: slideUp 0.6s ease-out;
  transition: all 0.3s ease;
}

.register-card:hover {
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
}

.register-header {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  padding: 2rem;
  text-align: center;
}

/* Logo样式 */
.logo-container {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 15px;
  animation: fadeIn 1s ease;
}

.logo-icon {
  font-size: 32px;
  color: #fff;
  margin-right: 10px;
  animation: bounce 1s ease infinite alternate;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.logo-text {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.5px;
}

.register-header h2 {
  margin: 0;
  font-size: 1.8rem;
  font-weight: 600;
}

.register-header p {
  margin: 0.5rem 0 0;
  opacity: 0.9;
}

.register-form {
  padding: 2rem;
}

/* 步骤动画 */
.el-steps {
  margin-bottom: 30px !important;
  transition: all 0.5s ease;
}

.el-step__title {
  transition: all 0.3s ease;
}

.el-step__title.is-process {
  color: #667eea !important;
  font-weight: bold;
  transform: scale(1.05);
}

.form-group {
  margin-bottom: 1.5rem;
  transition: all 0.3s ease;
  animation: fadeInUp 0.5s ease;
}

.form-group label {
  display: block;
  margin-bottom: 0.8rem;
  font-weight: 500;
  color: #333;
  font-size: 0.95rem;
  letter-spacing: 0.5px;
  position: relative;
  padding-left: 12px;
}

.form-group label::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 14px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 2px;
}

/* 输入框样式增强 */
:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.1) inset;
  border-radius: 8px;
  padding: 0 12px;
  transition: all 0.3s ease;
  background-color: rgba(255, 192, 203, 0.15);
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(255, 105, 180, 0.3) inset;
  background-color: rgba(255, 192, 203, 0.25);
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px rgba(255, 105, 180, 0.5) inset, 0 4px 10px rgba(255, 105, 180, 0.1);
  transform: translateY(-2px);
  background-color: rgba(255, 192, 203, 0.3);
}

/* 确保输入框内部也是粉红色 */
:deep(.el-input__inner) {
  height: 42px;
  font-size: 0.95rem;
  color: #333;
  background-color: transparent !important;
}

/* 确保前缀图标区域也是粉红色 */
:deep(.el-input__prefix) {
  color: #667eea;
  background-color: transparent;
}

/* 确保后缀图标区域也是粉红色 */
:deep(.el-input__suffix) {
  background-color: transparent;
}

:deep(.el-textarea__inner) {
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.1) inset;
  transition: all 0.3s ease;
  background-color: rgba(255, 192, 203, 0.15) !important;
}

:deep(.el-textarea__inner:hover) {
  box-shadow: 0 0 0 1px rgba(255, 105, 180, 0.3) inset;
  background-color: rgba(255, 192, 203, 0.25) !important;
}

:deep(.el-textarea__inner:focus) {
  box-shadow: 0 0 0 1px rgba(255, 105, 180, 0.5) inset, 0 4px 10px rgba(255, 105, 180, 0.1);
  transform: translateY(-2px);
  background-color: rgba(255, 192, 203, 0.3) !important;
}

/* 下拉选择框样式增强 */
:deep(.el-select .el-input__wrapper) {
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.1) inset;
  background-color: rgba(255, 192, 203, 0.15);
}

:deep(.el-select .el-input.is-focus .el-input__wrapper) {
  box-shadow: 0 0 0 1px rgba(255, 105, 180, 0.5) inset, 0 4px 10px rgba(255, 105, 180, 0.1);
  background-color: rgba(255, 192, 203, 0.3);
}

:deep(.el-select-dropdown__item.selected) {
  color: #667eea;
  font-weight: 600;
}

/* 密码反馈样式优化 */
.password-feedback {
  font-size: 12px;
  color: #666;
  margin-top: 8px;
  padding: 6px 10px;
  background-color: #f8f9fa;
  border-radius: 6px;
  border-left: 3px solid #667eea;
  transition: all 0.3s ease;
}

.generate-password-button {
  font-size: 13px;
  color: #667eea;
  margin-top: 8px;
  cursor: pointer;
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  background-color: rgba(102, 126, 234, 0.1);
  transition: all 0.3s ease;
}

.generate-password-button:hover {
  background-color: rgba(102, 126, 234, 0.2);
  color: #5a6eea;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 2rem;
}

.register-button, .next-button, .prev-button {
  transition: all 0.3s ease;
}

.register-button, .next-button {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  position: relative;
  overflow: hidden;
}

.register-button:hover, .next-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.register-button:active, .next-button:active {
  transform: translateY(0);
}

.prev-button:hover {
  transform: translateY(-2px);
}

.form-footer {
  text-align: center;
  margin-top: 1.5rem;
  color: #666;
}

.login-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s ease;
}

.login-link:hover {
  color: #764ba2;
  text-decoration: underline;
}

/* 步骤切换动画 */
.slide-right {
  animation: slideInRight 0.3s forwards;
}

.slide-left {
  animation: slideInLeft 0.3s forwards;
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* 添加动画关键帧 */
@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeInUp {
  from { 
    opacity: 0;
    transform: translateY(10px);
  }
  to { 
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes bounce {
  from { transform: translateY(0); }
  to { transform: translateY(-5px); }
}
</style>
