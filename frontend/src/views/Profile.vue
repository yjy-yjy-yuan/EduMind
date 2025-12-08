<template>
  <div class="profile-container">
    <!-- 顶部个人资料卡片 -->
    <div class="profile-hero-section">
      <div class="hero-overlay"></div>
      <div class="hero-container">
        <div class="profile-header">
          <h1 class="main-title">我的个人资料</h1>
          <p class="subtitle">查看和管理您的个人信息和学习记录</p>
        </div>
      </div>
    </div>

    <div class="profile-content">
      <el-row :gutter="20">
        <!-- 左侧个人信息卡片 -->
        <el-col :xs="24" :sm="24" :md="8" :lg="6" :xl="6">
          <el-card class="profile-card" shadow="hover">
            <div class="avatar-container">
              <div class="avatar-wrapper">
                <el-avatar :size="100" :src="userInfo.avatar || defaultAvatar">
                  {{ userInfo.username ? userInfo.username.charAt(0).toUpperCase() : 'U' }}
                </el-avatar>
              </div>
              <h2 class="username">{{ userInfo.username }}</h2>
              <p class="user-email">{{ userInfo.email }}</p>
            </div>

            <div class="card-divider"></div>

            <div class="user-status">
              <div class="status-item">
                <div class="status-icon">
                  <el-icon><Trophy /></el-icon>
                </div>
                <div class="status-text">{{ userInfo.user_level || '初级学习者' }}</div>
              </div>
            </div>

            <div class="card-divider"></div>

            <div class="quick-stats">
              <div class="stat-item">
                <div class="stat-value">{{ userInfo.notes_count || 0 }}</div>
                <div class="stat-label">笔记</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ userInfo.videos_count || 0 }}</div>
                <div class="stat-label">视频</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ userInfo.qa_count || 0 }}</div>
                <div class="stat-label">问答</div>
              </div>
            </div>

            <div class="card-divider"></div>

            <div class="join-info">
              <div class="join-date">
                <el-icon><Calendar /></el-icon>
                <span>加入于 {{ formatDate(userInfo.created_at).split(' ')[0] }}</span>
              </div>
            </div>

            <div class="profile-actions">
              <el-button type="danger" @click="handleLogout" class="action-btn">
                <el-icon><SwitchButton /></el-icon> 退出登录
              </el-button>
            </div>
          </el-card>
        </el-col>

        <!-- 右侧内容区域 -->
        <el-col :xs="24" :sm="24" :md="16" :lg="18" :xl="18">
          <el-card class="tabs-card" shadow="hover">
            <el-tabs v-model="activeTab" class="profile-tabs">
              <!-- 个人信息标签页 -->
              <el-tab-pane label="个人信息" name="info">
                <div class="tab-header">
                  <h3>个人资料详情</h3>
                  <el-button type="primary" @click="toggleEditMode" class="edit-btn">
                    <el-icon><Edit /></el-icon> {{ isEditing ? '保存资料' : '编辑资料' }}
                  </el-button>
                </div>

                <div class="info-detail-list">
                  <div class="info-detail-item">
                    <div class="detail-label">用户名</div>
                    <div class="detail-value" v-if="!isEditing">{{ userInfo.username }}</div>
                    <el-input v-else v-model="editForm.username" placeholder="请输入用户名" class="edit-input"></el-input>
                  </div>
                  <div class="info-detail-item">
                    <div class="detail-label">邮箱</div>
                    <div class="detail-value" v-if="!isEditing">{{ userInfo.email }}</div>
                    <el-input v-else v-model="editForm.email" placeholder="请输入邮箱" class="edit-input"></el-input>
                  </div>
                  <div class="info-detail-item">
                    <div class="detail-label">性别</div>
                    <div class="detail-value" v-if="!isEditing">{{ userInfo.gender || '未设置' }}</div>
                    <el-select v-else v-model="editForm.gender" placeholder="请选择性别" class="edit-input">
                      <el-option label="男" value="男"></el-option>
                      <el-option label="女" value="女"></el-option>
                      <el-option label="其他" value="其他"></el-option>
                      <el-option label="不愿透露" value="不愿透露"></el-option>
                    </el-select>
                  </div>
                  <div class="info-detail-item">
                    <div class="detail-label">学历</div>
                    <div class="detail-value" v-if="!isEditing">{{ userInfo.education || '未设置' }}</div>
                    <el-select v-else v-model="editForm.education" placeholder="请选择学历" class="edit-input">
                      <el-option label="高中及以下" value="高中及以下"></el-option>
                      <el-option label="专科" value="专科"></el-option>
                      <el-option label="本科" value="本科"></el-option>
                      <el-option label="硕士" value="硕士"></el-option>
                      <el-option label="博士" value="博士"></el-option>
                    </el-select>
                  </div>
                  <div class="info-detail-item">
                    <div class="detail-label">职业</div>
                    <div class="detail-value" v-if="!isEditing">{{ userInfo.occupation || '未设置' }}</div>
                    <el-select v-else v-model="editForm.occupation" placeholder="请选择职业" class="edit-input">
                      <el-option label="学生" value="学生"></el-option>
                      <el-option label="教师" value="教师"></el-option>
                      <el-option label="IT/互联网" value="IT/互联网"></el-option>
                      <el-option label="金融" value="金融"></el-option>
                      <el-option label="医疗" value="医疗"></el-option>
                      <el-option label="其他" value="其他"></el-option>
                    </el-select>
                  </div>
                  <div class="info-detail-item">
                    <div class="detail-label">学习方向</div>
                    <div class="detail-value" v-if="!isEditing">{{ userInfo.learning_direction || '未设置' }}</div>
                    <el-select v-else v-model="editForm.learning_direction" placeholder="请选择学习方向" class="edit-input">
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
                  <div class="info-detail-item">
                    <div class="detail-label">注册时间</div>
                    <div class="detail-value">{{ formatDate(userInfo.created_at) }}</div>
                  </div>
                  <div class="info-detail-item">
                    <div class="detail-label">上次登录</div>
                    <div class="detail-value">{{ formatDate(userInfo.last_login) }}</div>
                  </div>
                  <div class="info-detail-item bio-item">
                    <div class="detail-label">个人简介</div>
                    <div class="detail-value" v-if="!isEditing">{{ userInfo.bio || '未设置个人简介' }}</div>
                    <el-input v-else v-model="editForm.bio" type="textarea" placeholder="请简单介绍一下自己" :rows="3" class="edit-input"></el-input>
                  </div>
                </div>
              </el-tab-pane>

              <!-- 笔记管理标签页 -->
              <el-tab-pane label="笔记管理" name="notes">
                <div class="tab-header">
                  <h3>我的笔记</h3>
                </div>

                <div class="empty-placeholder" v-if="!notes.length">
                  <el-empty description="暂无笔记记录">
                    <el-button type="primary">去创建笔记</el-button>
                  </el-empty>
                </div>

                <el-table v-else :data="notes" style="width: 100%">
                  <el-table-column prop="title" label="标题" width="180"></el-table-column>
                  <el-table-column prop="video_title" label="关联视频" width="180"></el-table-column>
                  <el-table-column prop="created_at" label="创建时间"></el-table-column>
                  <el-table-column label="操作" width="150">
                    <template #default="scope">
                      <el-button size="small" @click="viewNote(scope.row)">查看</el-button>
                      <el-button size="small" type="danger" @click="deleteNote(scope.row)">删除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </el-tab-pane>

              <!-- 总结记录标签页 -->
              <el-tab-pane label="总结记录" name="summaries">
                <div class="tab-header">
                  <h3>我的总结</h3>
                </div>

                <div class="empty-placeholder" v-if="!summaries.length">
                  <el-empty description="暂无总结记录">
                    <el-button type="primary">去创建总结</el-button>
                  </el-empty>
                </div>

                <el-table v-else :data="summaries" style="width: 100%">
                  <el-table-column prop="title" label="标题" width="180"></el-table-column>
                  <el-table-column prop="video_title" label="关联视频" width="180"></el-table-column>
                  <el-table-column prop="created_at" label="创建时间"></el-table-column>
                  <el-table-column label="操作" width="150">
                    <template #default="scope">
                      <el-button size="small" @click="viewSummary(scope.row)">查看</el-button>
                      <el-button size="small" type="danger" @click="deleteSummary(scope.row)">删除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </el-tab-pane>

              <!-- 学习知识点标签页 -->
              <el-tab-pane label="学习知识点" name="knowledge">
                <div class="tab-header">
                  <h3>我的知识点</h3>
                </div>

                <div class="empty-placeholder" v-if="!knowledgePoints.length">
                  <el-empty description="暂无知识点记录">
                    <el-button type="primary">去学习</el-button>
                  </el-empty>
                </div>

                <el-timeline v-else>
                  <el-timeline-item
                    v-for="(point, index) in knowledgePoints"
                    :key="index"
                    :timestamp="formatDate(point.created_at)"
                    placement="top"
                  >
                    <el-card>
                      <h4>{{ point.title }}</h4>
                      <p>{{ point.content }}</p>
                      <p class="knowledge-source">来源视频：{{ point.video_title }}</p>
                    </el-card>
                  </el-timeline-item>
                </el-timeline>
              </el-tab-pane>
            </el-tabs>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import authStore from '../store/auth'
import {
  User, School, Briefcase, Compass, Calendar, Clock,
  Edit, SwitchButton, Trophy
} from '@element-plus/icons-vue'

const router = useRouter()
const defaultAvatar = 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'

// 用户信息
const userInfo = ref({})
const editForm = reactive({
  username: '',
  email: '',
  gender: '',
  education: '',
  occupation: '',
  learning_direction: '',
  bio: ''
})

// 标签页
const activeTab = ref('info')

// 模拟数据
const notes = ref([])
const summaries = ref([])
const knowledgePoints = ref([])

// 编辑模式
const isEditing = ref(false)
const updateLoading = ref(false)

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    const response = await axios.get('/api/auth/user')
    if (response.data.success) {
      // 确保所有字段都有默认值
      userInfo.value = {
        username: '',
        email: '',
        gender: '',
        education: '',
        occupation: '',
        learning_direction: '',
        bio: '',
        created_at: null,
        last_login: null,
        ...response.data.user
      }
    } else {
      ElMessage.error(response.data.message || '获取用户信息失败')
      router.push('/login')
    }
  } catch (error) {
    console.error('获取用户信息错误:', error)
    ElMessage.error('获取用户信息失败，请重新登录')
    router.push('/login')
  }
}

// 切换编辑模式
const toggleEditMode = () => {
  if (!isEditing.value) {
    // 进入编辑模式
    isEditing.value = true
    // 复制当前用户信息到编辑表单
    Object.keys(editForm).forEach(key => {
      editForm[key] = userInfo.value[key] || ''
    })
  } else {
    // 保存更改
    updateUserInfo()
  }
}

// 更新用户信息
const updateUserInfo = async () => {
  if (!editForm.username || !editForm.email) {
    ElMessage.warning('用户名和邮箱不能为空')
    return
  }

  updateLoading.value = true

  try {
    const response = await axios.post('/api/auth/user/update', editForm)

    if (response.data.success) {
      // 更新本地用户信息
      userInfo.value = {
        ...userInfo.value,
        ...editForm
      }

      ElMessage.success('个人信息更新成功')
      isEditing.value = false
    } else {
      ElMessage.error(response.data.message || '更新失败')
    }
  } catch (error) {
    console.error('更新用户信息错误:', error)
    ElMessage.error(error.response?.data?.message || '更新失败，请稍后再试')
    isEditing.value = true // 保持编辑模式，让用户可以修复错误
  } finally {
    updateLoading.value = false
  }
}

// 取消编辑
const cancelEdit = () => {
  isEditing.value = false
  ElMessage.info('已取消编辑')
}

// 退出登录
const handleLogout = () => {
  ElMessageBox.confirm(
    '确定要退出登录吗？',
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(async () => {
      try {
        const response = await axios.post('/api/auth/logout')

        if (response.data.success) {
          // 清除本地存储的用户信息
          authStore.clearAuth()

          ElMessage.success('退出成功')
          router.push('/login')
        } else {
          ElMessage.error(response.data.message || '退出失败')
        }
      } catch (error) {
        console.error('退出登录错误:', error)
        ElMessage.error('退出失败，请稍后再试')
      }
    })
    .catch(() => {
      // 取消退出
    })
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '未知'

  try {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    return dateString
  }
}

// 笔记相关方法
const viewNote = (note) => {
  // 查看笔记的实现
  console.log('查看笔记', note)
}

const deleteNote = (note) => {
  ElMessageBox.confirm('确定要删除这条笔记吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    // 删除笔记的实现
    console.log('删除笔记', note)
  })
}

// 总结相关方法
const viewSummary = (summary) => {
  // 查看总结的实现
  console.log('查看总结', summary)
}

const deleteSummary = (summary) => {
  ElMessageBox.confirm('确定要删除这条总结吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    // 删除总结的实现
    console.log('删除总结', summary)
  })
}

// 页面加载时获取用户信息
onMounted(() => {
  fetchUserInfo()
})
</script>

<style scoped>
/* 基本样式 */
.profile-container {
  min-height: 100vh;
  background-color: #f5f8fa;
}

/* 顶部英雄区域 */
.profile-hero-section {
  position: relative;
  padding: 80px 20px;
  background-image: linear-gradient(135deg, rgba(255, 192, 203, 0.8), rgba(102, 126, 234, 0.8)), url('https://public.readdy.ai/ai/img_res/b2856a465ee244a4bb2ffa4b39614527.jpg');
  background-size: cover;
  background-position: center;
  color: #fff;
  overflow: hidden;
}

.hero-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  background: linear-gradient(135deg, rgba(255, 192, 203, 0.7), rgba(118, 75, 162, 0.7));
  backdrop-filter: blur(2px);
}

.hero-container {
  position: relative;
  z-index: 2;
  max-width: 1200px;
  margin: 0 auto;
}

.profile-header {
  text-align: center;
  margin-bottom: 1rem;
}

.main-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
  letter-spacing: -0.5px;
  line-height: 1.2;
  animation: fadeInDown 1s ease-out;
  color: #fff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.subtitle {
  font-size: 1.25rem;
  margin-bottom: 1.5rem;
  line-height: 1.6;
  max-width: 700px;
  margin-left: auto;
  margin-right: auto;
  animation: fadeInUp 1s ease-out 0.3s both;
}

/* 内容区域 */
.profile-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
  margin-top: -40px;
  position: relative;
  z-index: 10;
}

/* 个人信息卡片 */
.profile-card {
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  border: none;
  margin-bottom: 20px;
}

.profile-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.15);
}

.avatar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px 0;
  background: linear-gradient(to right, rgba(255, 192, 203, 0.2) 0%, rgba(255, 192, 203, 0.4) 100%);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  position: relative;
  overflow: hidden;
}

.avatar-container::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.3) 0%, transparent 60%);
  animation: rotate 20s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.avatar-wrapper {
  position: relative;
  z-index: 1;
  padding: 5px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ff9a9e, #fad0c4);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
  margin-bottom: 15px;
}

.username {
  position: relative;
  z-index: 1;
  margin: 15px 0 5px;
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
}

.user-email {
  position: relative;
  z-index: 1;
  color: #666;
  font-size: 0.9rem;
  margin: 0;
  background-color: rgba(255, 192, 203, 0.1);
  padding: 5px 12px;
  border-radius: 20px;
}

.card-divider {
  height: 1px;
  background-color: rgba(0, 0, 0, 0.05);
  margin: 20px 0;
}

.user-status {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.status-item {
  display: flex;
  align-items: flex-start;
  color: #555;
  padding: 12px;
  border-radius: 10px;
  transition: all 0.3s ease;
  background-color: #fff;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05);
  border-left: 3px solid rgba(255, 192, 203, 0.5);
}

.status-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 15px rgba(0, 0, 0, 0.08);
  border-left: 3px solid rgba(255, 192, 203, 0.8);
}

.status-icon {
  margin-right: 15px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ffd3a5, #fd6585);
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-icon .el-icon {
  color: white;
  font-size: 1.2rem;
}

.status-text {
  font-size: 1rem;
  color: #333;
  font-weight: 500;
}

.quick-stats {
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  margin: 15px 0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #555;
  padding: 15px;
  border-radius: 10px;
  transition: all 0.3s ease;
  background-color: rgba(255, 192, 203, 0.05);
  width: 30%;
  text-align: center;
}

.stat-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 15px rgba(0, 0, 0, 0.08);
  background-color: rgba(255, 192, 203, 0.1);
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 5px;
  background: linear-gradient(135deg, #ff9a9e, #fad0c4);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.stat-label {
  font-size: 0.9rem;
  color: #666;
}

.join-info {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.join-date {
  display: flex;
  align-items: center;
  color: #555;
  padding: 12px;
  border-radius: 10px;
  transition: all 0.3s ease;
  background-color: #fff;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05);
  border-left: 3px solid rgba(255, 192, 203, 0.5);
}

.join-date:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 15px rgba(0, 0, 0, 0.08);
  border-left: 3px solid rgba(255, 192, 203, 0.8);
}

.join-date .el-icon {
  margin-right: 10px;
  font-size: 1.2rem;
  color: #ff9a9e;
}

.join-date span {
  font-size: 1rem;
  color: #333;
  font-weight: 500;
}

.profile-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 0 25px 25px;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 44px;
  transition: all 0.3s ease;
  border-radius: 8px;
  font-weight: 500;
}

.action-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

/* 标签页卡片 */
.tabs-card {
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  border: none;
}

.profile-tabs {
  padding: 25px;
}

:deep(.el-tabs__item) {
  font-size: 1rem;
  padding: 0 20px;
  height: 50px;
  line-height: 50px;
  transition: all 0.3s ease;
}

:deep(.el-tabs__item.is-active) {
  color: #ff9a9e;
  font-weight: 600;
}

:deep(.el-tabs__active-bar) {
  background-color: #ff9a9e;
  height: 3px;
  border-radius: 3px;
}

:deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: rgba(0, 0, 0, 0.05);
}

.tab-header {
  margin-bottom: 25px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  padding-bottom: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tab-header h3 {
  font-size: 1.2rem;
  color: #333;
  margin: 0;
  position: relative;
  padding-left: 15px;
}

.tab-header h3::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 16px;
  background: linear-gradient(135deg, #ff9a9e, #fad0c4);
  border-radius: 2px;
}

.edit-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.9rem;
  padding: 8px 15px;
  border-radius: 8px;
  transition: all 0.3s ease;
  background: linear-gradient(135deg, #ff9a9e, #fad0c4);
  border-color: transparent;
  color: #fff;
  font-weight: 500;
}

.edit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
  opacity: 0.9;
}

.info-detail-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.info-detail-item {
  padding: 15px;
  border-radius: 10px;
  background-color: #fff;
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  border-left: 3px solid rgba(255, 192, 203, 0.5);
}

.info-detail-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 15px rgba(0, 0, 0, 0.08);
  border-left: 3px solid rgba(255, 192, 203, 0.8);
}

.bio-item {
  grid-column: span 2;
}

.detail-label {
  font-size: 0.85rem;
  color: #999;
  margin-bottom: 8px;
  position: relative;
  padding-left: 12px;
}

.detail-label::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 12px;
  background: linear-gradient(135deg, #ff9a9e, #fad0c4);
  border-radius: 2px;
}

.detail-value {
  font-size: 1rem;
  color: #333;
  font-weight: 500;
  word-break: break-word;
}

.bio-item .detail-value {
  padding: 10px;
  background-color: rgba(255, 192, 203, 0.05);
  border-radius: 8px;
  margin-top: 5px;
  line-height: 1.6;
  min-height: 80px;
}

.empty-placeholder {
  padding: 50px 0;
  text-align: center;
}

:deep(.el-empty__image) {
  width: 120px;
  height: 120px;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #ff9a9e, #fad0c4);
  border-color: #ff9a9e;
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #ff9a9e, #fad0c4);
  opacity: 0.9;
  border-color: #ff9a9e;
}

:deep(.el-button--danger) {
  background: linear-gradient(135deg, #ff758c, #ff7eb3);
  border-color: #ff758c;
}

:deep(.el-button--danger:hover) {
  background: linear-gradient(135deg, #ff758c, #ff7eb3);
  opacity: 0.9;
  border-color: #ff758c;
}

.knowledge-source {
  font-size: 0.85rem;
  color: #999;
  margin-top: 10px;
}

/* 编辑输入框样式 */
.edit-input {
  width: 100%;
  margin-top: 5px;
}

:deep(.el-input__wrapper) {
  background-color: rgba(255, 192, 203, 0.1);
  border-radius: 8px;
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  background-color: rgba(255, 192, 203, 0.2);
}

:deep(.el-input__wrapper.is-focus) {
  background-color: rgba(255, 192, 203, 0.3);
  box-shadow: 0 0 0 1px rgba(255, 154, 158, 0.5);
}

:deep(.el-textarea__inner) {
  background-color: rgba(255, 192, 203, 0.1);
  border-radius: 8px;
  transition: all 0.3s ease;
  padding: 10px;
}

:deep(.el-textarea__inner:hover) {
  background-color: rgba(255, 192, 203, 0.2);
}

:deep(.el-textarea__inner:focus) {
  background-color: rgba(255, 192, 203, 0.3);
  box-shadow: 0 0 0 1px rgba(255, 154, 158, 0.5);
}

:deep(.el-select .el-input__wrapper) {
  background-color: rgba(255, 192, 203, 0.1);
}

:deep(.el-select .el-input.is-focus .el-input__wrapper) {
  box-shadow: 0 0 0 1px rgba(255, 154, 158, 0.5);
}

:deep(.el-select-dropdown__item.selected) {
  background-color: rgba(255, 192, 203, 0.2);
  color: #333;
}

/* 动画效果 */
@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
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

/* 响应式调整 */
@media (max-width: 768px) {
  .profile-hero-section {
    padding: 60px 15px;
  }

  .main-title {
    font-size: 2rem;
  }

  .subtitle {
    font-size: 1rem;
  }

  .profile-content {
    padding: 20px 15px;
    margin-top: -30px;
  }

  .info-item {
    padding: 8px;
  }

  .profile-tabs {
    padding: 20px 15px;
  }
}
</style>
