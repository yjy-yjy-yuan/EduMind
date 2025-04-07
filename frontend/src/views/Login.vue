<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h2>登录</h2>
        <p>欢迎回到 AI-EdVision</p>
      </div>
      
      <div class="login-form">
        <!-- 历史登录信息下拉菜单 -->
        <div class="form-group" v-if="savedAccounts.length > 0">
          <label>快速登录</label>
          <el-select 
            v-model="selectedAccount" 
            placeholder="选择历史账号" 
            style="width: 100%"
            @change="handleSelectAccount"
          >
            <el-option 
              v-for="account in savedAccounts" 
              :key="account.username" 
              :label="account.username" 
              :value="account.username"
            >
              <div class="account-option">
                <span>{{ account.username }}</span>
                <el-button 
                  type="danger" 
                  size="small" 
                  icon="Delete" 
                  circle 
                  @click.stop="removeAccount(account.username)"
                ></el-button>
              </div>
            </el-option>
          </el-select>
        </div>
        
        <div class="form-group">
          <label for="username">用户名/邮箱</label>
          <el-input 
            v-model="loginForm.username" 
            placeholder="请输入用户名或邮箱" 
            :prefix-icon="User"
            @keyup.enter="handleLogin"
          />
        </div>
        
        <div class="form-group">
          <label for="password">密码</label>
          <el-input 
            v-model="loginForm.password" 
            type="password" 
            placeholder="请输入密码" 
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </div>
        
        <div class="form-options">
          <el-checkbox v-model="rememberMe">记住我</el-checkbox>
        </div>
        
        <div class="form-actions">
          <el-button 
            type="primary" 
            class="login-button" 
            :loading="loading" 
            @click="handleLogin"
          >
            登录
          </el-button>
        </div>
        
        <div class="form-footer">
          <p>还没有账号？<router-link to="/register" class="register-link">快速注册</router-link></p>
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
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import authStore from '../store/auth'

const router = useRouter()
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('')
const dialogMessage = ref('')
const rememberMe = ref(false)
const savedAccounts = ref([])
const selectedAccount = ref('')

const loginForm = reactive({
  username: '',
  password: ''
})

// 加载保存的账号信息
onMounted(() => {
  const accounts = JSON.parse(localStorage.getItem('savedAccounts') || '[]')
  savedAccounts.value = accounts
  
  // 如果有上次登录的账号，自动填充
  const lastAccount = localStorage.getItem('lastAccount')
  if (lastAccount) {
    const account = accounts.find(acc => acc.username === lastAccount)
    if (account) {
      loginForm.username = account.username
      loginForm.password = account.password
      rememberMe.value = true
    }
  }
})

// 选择历史账号
const handleSelectAccount = (username) => {
  const account = savedAccounts.value.find(acc => acc.username === username)
  if (account) {
    loginForm.username = account.username
    loginForm.password = account.password
  }
}

// 删除保存的账号
const removeAccount = (username) => {
  savedAccounts.value = savedAccounts.value.filter(acc => acc.username !== username)
  localStorage.setItem('savedAccounts', JSON.stringify(savedAccounts.value))
  
  // 如果删除的是当前选中的账号，清空选择
  if (selectedAccount.value === username) {
    selectedAccount.value = ''
  }
  
  // 如果删除的是上次登录的账号，清空上次登录记录
  if (localStorage.getItem('lastAccount') === username) {
    localStorage.removeItem('lastAccount')
  }
  
  ElMessage({
    message: '已删除保存的账号信息',
    type: 'success',
    duration: 2000
  })
}

const showDialog = (title, message) => {
  dialogTitle.value = title
  dialogMessage.value = message
  dialogVisible.value = true
}

const handleLogin = async () => {
  // 表单验证
  if (!loginForm.username || !loginForm.password) {
    showDialog('提示', '请输入用户名/邮箱和密码')
    return
  }
  
  try {
    loading.value = true
    
    // 使用 authStore 的 login 方法进行登录
    const result = await authStore.login(loginForm.username, loginForm.password)
    
    if (result.success) {
      // 登录成功
      
      // 如果选择了"记住我"，保存账号信息
      if (rememberMe.value) {
        // 检查是否已经保存过该账号
        const existingIndex = savedAccounts.value.findIndex(acc => acc.username === loginForm.username)
        
        if (existingIndex >= 0) {
          // 更新已有账号信息
          savedAccounts.value[existingIndex] = {
            username: loginForm.username,
            password: loginForm.password
          }
        } else {
          // 添加新账号信息
          savedAccounts.value.push({
            username: loginForm.username,
            password: loginForm.password
          })
        }
        
        // 保存到本地存储
        localStorage.setItem('savedAccounts', JSON.stringify(savedAccounts.value))
        localStorage.setItem('lastAccount', loginForm.username)
      } else {
        // 如果没有选择"记住我"，清除上次登录记录
        localStorage.removeItem('lastAccount')
      }
      
      // 显示成功提示
      ElMessage({
        message: '登录成功',
        type: 'success',
        duration: 2000
      })
      
      // 跳转到首页
      router.push('/')
    } else {
      // 登录失败
      showDialog('登录失败', result.message)
    }
  } catch (error) {
    console.error('登录错误:', error)
    showDialog('登录错误', error.response?.data?.message || '登录失败，请稍后再试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 450px;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  overflow: hidden;
  padding: 40px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  font-size: 28px;
  color: #333;
  margin-bottom: 10px;
}

.login-header p {
  color: #666;
  font-size: 16px;
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

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.login-button {
  width: 100%;
  padding: 12px 0;
  font-size: 16px;
  font-weight: 500;
  margin-top: 10px;
}

.form-footer {
  margin-top: 25px;
  text-align: center;
  color: #666;
}

.register-link {
  color: #764ba2;
  font-weight: 500;
  text-decoration: none;
  transition: color 0.3s;
}

.register-link:hover {
  color: #667eea;
  text-decoration: underline;
}

.account-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}
</style>
