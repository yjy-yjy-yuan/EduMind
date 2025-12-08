<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <!-- 添加与顶部栏相同的logo -->
        <div class="logo-container">
          <i class="fas fa-graduation-cap logo-icon"></i>
          <span class="logo-text">视频智能伴学</span>
        </div>
        <h2>登录</h2>
        <p>欢迎回到视频智能伴学系统</p>
      </div>

      <div class="login-form">
        <div class="form-group">
          <label for="username">用户名/邮箱</label>
          <el-autocomplete
            v-model="loginForm.username"
            :fetch-suggestions="queryAccountSuggestions"
            placeholder="请输入用户名或邮箱"
            class="full-width-autocomplete"
            @select="handleSelectAccountSuggestion"
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
            <template #default="{ item }">
              <div class="account-suggestion">
                <span>{{ item.value }}</span>
                <el-button
                  type="danger"
                  size="small"
                  circle
                  @click.stop="removeAccount(item.value)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </template>
          </el-autocomplete>
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
            @keyup.enter="handleLogin"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
          <div class="password-security-tip">
            <i class="fas fa-shield-alt"></i>
            <span>使用强密码可以提高账户安全性</span>
          </div>
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

    <!-- 密码安全提示对话框 -->
    <el-dialog
      v-model="securityDialogVisible"
      title="密码安全提示"
      width="40%"
      align-center
    >
      <div class="security-dialog-content">
        <div class="security-icon">
          <i class="fas fa-shield-alt"></i>
        </div>
        <div class="security-message">
          <h3>提高您的账户安全性</h3>
          <p>我们注意到您可能使用了较为简单的密码。为了保护您的账户安全，建议：</p>
          <ul>
            <li>使用至少8个字符的密码</li>
            <li>包含大小写字母、数字和特殊字符</li>
            <li>避免使用容易猜测的信息（如生日、姓名等）</li>
            <li>定期更换密码</li>
          </ul>
          <p>您可以在个人中心随时更新您的密码。</p>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="securityDialogVisible = false">稍后再说</el-button>
          <el-button type="primary" @click="goToChangePassword">
            立即更新密码
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, Delete } from '@element-plus/icons-vue'
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
const securityDialogVisible = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

// 加载保存的账号信息
onMounted(() => {
  // 从本地存储中加载保存的账号
  const savedAccountsStr = localStorage.getItem('savedAccounts')
  if (savedAccountsStr) {
    try {
      savedAccounts.value = JSON.parse(savedAccountsStr)
    } catch (e) {
      console.error('解析保存的账号失败:', e)
      savedAccounts.value = []
    }
  }

  // 加载上次登录的账号
  const lastAccount = localStorage.getItem('lastAccount')
  if (lastAccount) {
    selectedAccount.value = lastAccount

    // 如果存在上次登录的账号，自动填充
    const account = savedAccounts.value.find(acc => acc.username === lastAccount)
    if (account) {
      loginForm.username = account.username
      loginForm.password = account.password
    }
  }
})

// 查询账号建议
const queryAccountSuggestions = (queryString, callback) => {
  const results = queryString
    ? savedAccounts.value.filter(account =>
        account.username.toLowerCase().includes(queryString.toLowerCase())
      )
    : savedAccounts.value

  // 将账号对象转换为自动完成组件所需的格式
  callback(results.map(account => ({
    value: account.username,
    account: account
  })))
}

// 选择账号建议
const handleSelectAccountSuggestion = (item) => {
  // 找到对应的账号
  const account = savedAccounts.value.find(acc => acc.username === item.value)
  if (account) {
    // 填充用户名和密码
    loginForm.username = account.username
    loginForm.password = account.password
  }
}

// 删除保存的账号
const removeAccount = (username) => {
  // 从数组中移除账号
  const index = savedAccounts.value.findIndex(acc => acc.username === username)
  if (index >= 0) {
    savedAccounts.value.splice(index, 1)

    // 更新本地存储
    localStorage.setItem('savedAccounts', JSON.stringify(savedAccounts.value))

    // 如果删除的是当前选中的账号，清空选择
    if (selectedAccount.value === username) {
      selectedAccount.value = ''
      loginForm.username = ''
      loginForm.password = ''
    }

    // 如果删除的是上次登录的账号，清空上次登录记录
    if (localStorage.getItem('lastAccount') === username) {
      localStorage.removeItem('lastAccount')
    }

    ElMessage({
      message: '账号已删除',
      type: 'success'
    })
  }
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

      // 显示成功消息
      ElMessage({
        message: '登录成功',
        type: 'success',
        duration: 2000
      })

      // 检查密码强度，如果密码较弱，显示安全提示
      checkPasswordStrength(loginForm.password)

      // 跳转到首页
      router.push('/')
    } else {
      // 登录失败
      showDialog('登录失败', result.message || '用户名或密码错误')
    }
  } catch (error) {
    console.error('登录错误:', error)
    showDialog('登录错误', '服务器连接失败，请稍后再试')
  } finally {
    loading.value = false
  }
}

// 检查密码强度
const checkPasswordStrength = (password) => {
  let strength = 0

  // 长度检查
  if (password.length >= 8) strength += 1

  // 包含大写字母
  if (/[A-Z]/.test(password)) strength += 1

  // 包含小写字母
  if (/[a-z]/.test(password)) strength += 1

  // 包含数字
  if (/[0-9]/.test(password)) strength += 1

  // 包含特殊字符
  if (/[^A-Za-z0-9]/.test(password)) strength += 1

  // 如果密码强度较弱，显示安全提示对话框
  if (strength < 3) {
    setTimeout(() => {
      securityDialogVisible.value = true
    }, 1000)
  }
}

// 前往修改密码页面
const goToChangePassword = () => {
  securityDialogVisible.value = false
  router.push('/profile?tab=security')
}
</script>

<style scoped>
.login-container {
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

.login-card {
  width: 100%;
  max-width: 450px;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  animation: slideUp 0.6s ease-out;
  transition: all 0.3s ease;
}

.login-card:hover {
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
}

.login-header {
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

.login-header h2 {
  margin: 0;
  font-size: 1.8rem;
  font-weight: 600;
}

.login-header p {
  margin: 0.5rem 0 0;
  opacity: 0.9;
}

.login-form {
  padding: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
  transition: all 0.3s ease;
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

/* 下拉选择框样式增强 */
:deep(.el-select .el-input__wrapper) {
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.1) inset;
}

:deep(.el-select .el-input.is-focus .el-input__wrapper) {
  box-shadow: 0 0 0 1px rgba(102, 126, 234, 0.5) inset, 0 4px 10px rgba(102, 126, 234, 0.1);
}

:deep(.el-select-dropdown__item.selected) {
  color: #667eea;
  font-weight: 600;
}

/* 密码安全提示样式优化 */
.password-security-tip {
  display: flex;
  align-items: center;
  font-size: 12px;
  color: #666;
  margin-top: 8px;
  padding: 6px 10px;
  background-color: #f8f9fa;
  border-radius: 6px;
  border-left: 3px solid #667eea;
  transition: all 0.3s ease;
}

.password-security-tip i {
  margin-right: 8px;
  color: #667eea;
}

/* 账号选项样式优化 */
:deep(.el-select-dropdown__item) {
  padding: 0 12px;
}

.account-suggestion {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 8px 0;
}

.account-suggestion span {
  font-size: 0.95rem;
  color: #333;
}

/* 复选框样式优化 */
:deep(.el-checkbox__inner) {
  border-color: rgba(102, 126, 234, 0.5);
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #667eea;
  border-color: #667eea;
}

:deep(.el-checkbox__label) {
  font-size: 0.9rem;
  color: #555;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.form-actions {
  margin-bottom: 1.5rem;
}

.login-button {
  width: 100%;
  height: 44px;
  font-size: 1rem;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.login-button:active {
  transform: translateY(0);
}

.form-footer {
  text-align: center;
  color: #666;
}

.register-link {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s ease;
}

.register-link:hover {
  color: #764ba2;
  text-decoration: underline;
}

.security-dialog-content {
  display: flex;
  align-items: flex-start;
  padding: 10px;
}

.security-icon {
  font-size: 48px;
  color: #667eea;
  margin-right: 20px;
  animation: pulse 2s infinite;
}

.security-message h3 {
  margin-top: 0;
  color: #333;
}

.security-message ul {
  text-align: left;
  margin: 15px 0;
  padding-left: 20px;
}

.security-message li {
  margin-bottom: 8px;
  color: #555;
}

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

@keyframes bounce {
  from { transform: translateY(0); }
  to { transform: translateY(-5px); }
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}

/* 自动完成组件样式 */
.full-width-autocomplete {
  width: 100%;
}

.account-suggestion {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  padding: 8px 0;
}

:deep(.el-autocomplete-suggestion__list) {
  padding: 8px;
}

:deep(.el-autocomplete-suggestion__wrap) {
  max-height: 280px;
}

:deep(.el-autocomplete-suggestion li) {
  line-height: normal;
  padding: 8px 10px;
  border-radius: 6px;
  transition: all 0.3s;
}

:deep(.el-autocomplete-suggestion li:hover) {
  background-color: rgba(255, 192, 203, 0.15);
}

:deep(.el-autocomplete-suggestion li.highlighted) {
  background-color: rgba(255, 192, 203, 0.25);
}
</style>
