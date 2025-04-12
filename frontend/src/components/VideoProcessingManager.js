/**
 * 视频处理管理器
 * 用于在页面刷新后恢复视频处理状态的轮询
 */

import { ElMessage } from 'element-plus'
import { getVideoStatus } from '@/api/video'

/**
 * 检查是否有正在处理的视频，并恢复轮询
 * @param {Array} videoList 视频列表
 * @param {Function} startPollingVideoStatus 启动视频状态轮询的函数
 * @param {Function} startPollingProcessStatus 启动处理状态轮询的函数
 * @param {Function} refreshList 刷新视频列表的函数
 */
export const checkProcessingVideos = (
  videoList, 
  startPollingVideoStatus, 
  startPollingProcessStatus,
  refreshList
) => {
  console.log('检查是否有正在处理的视频...')
  
  // 筛选出状态为 'processing', 'pending' 或 'downloading' 的视频
  const processingVideos = videoList.filter(video => 
    video.status === 'processing' || 
    video.status === 'pending' || 
    video.status === 'downloading'
  )
  
  if (processingVideos.length > 0) {
    console.log(`发现${processingVideos.length}个正在处理的视频，恢复轮询`)
    
    // 为每个正在处理的视频启动轮询
    processingVideos.forEach(video => {
      // 如果是下载中的视频，使用下载轮询
      if (video.status === 'downloading') {
        console.log(`恢复视频${video.id}的下载状态轮询`)
        startPollingVideoStatus(video.id, true) // 第二个参数表示是YouTube视频
      } else {
        // 否则使用处理轮询
        console.log(`恢复视频${video.id}的处理状态轮询`)
        startPollingProcessStatus(video.id)
      }
      
      // 显示提示
      ElMessage({
        message: `正在继续处理视频: ${video.filename || video.title}`,
        type: 'info',
        duration: 3000
      })
    })
  } else {
    console.log('没有发现正在处理的视频')
  }
}

/**
 * 创建持久化的处理状态
 * 将正在处理的视频ID保存到localStorage
 * @param {String} videoId 视频ID
 * @param {String} status 视频状态
 */
export const saveProcessingState = (videoId, status) => {
  try {
    // 获取现有的处理中视频列表
    const processingVideos = JSON.parse(localStorage.getItem('processingVideos') || '{}')
    
    // 添加或更新视频状态
    processingVideos[videoId] = {
      status,
      timestamp: new Date().getTime()
    }
    
    // 保存回localStorage
    localStorage.setItem('processingVideos', JSON.stringify(processingVideos))
    console.log(`保存视频${videoId}的处理状态: ${status}`)
  } catch (error) {
    console.error('保存处理状态失败:', error)
  }
}

/**
 * 移除持久化的处理状态
 * 从localStorage中移除已完成处理的视频ID
 * @param {String} videoId 视频ID
 */
export const removeProcessingState = (videoId) => {
  try {
    // 获取现有的处理中视频列表
    const processingVideos = JSON.parse(localStorage.getItem('processingVideos') || '{}')
    
    // 移除该视频
    if (processingVideos[videoId]) {
      delete processingVideos[videoId]
      
      // 保存回localStorage
      localStorage.setItem('processingVideos', JSON.stringify(processingVideos))
      console.log(`移除视频${videoId}的处理状态`)
    }
  } catch (error) {
    console.error('移除处理状态失败:', error)
  }
}

/**
 * 获取所有持久化的处理中视频
 * @returns {Object} 处理中的视频对象，键为视频ID，值为状态对象
 */
export const getProcessingVideos = () => {
  try {
    return JSON.parse(localStorage.getItem('processingVideos') || '{}')
  } catch (error) {
    console.error('获取处理中视频失败:', error)
    return {}
  }
}

/**
 * 检查视频处理状态
 * @param {String} videoId 视频ID
 * @param {Number} attempts 尝试次数
 * @param {Number} maxAttempts 最大尝试次数
 * @param {Boolean} isGeneratingSummary 是否正在生成摘要
 * @param {Function} refreshList 刷新列表函数
 * @param {Function} clearInterval 清除定时器函数
 * @param {Object} timers 定时器对象
 */
export const checkVideoProcessStatus = async (
  videoId, 
  attempts, 
  maxAttempts, 
  isGeneratingSummary,
  refreshList,
  clearIntervalFn,
  timers
) => {
  try {
    console.log(`正在检查视频${videoId}的处理状态，第${attempts+1}次尝试`)
    
    // 获取视频状态
    const { data: statusResponse } = await getVideoStatus(videoId)
    
    // 每次轮询都刷新视频列表，但在生成摘要时不刷新
    if (!isGeneratingSummary) {
      await refreshList()
      console.log(`第${attempts+1}次轮询，刷新视频列表`)
    } else {
      console.log(`第${attempts+1}次轮询，正在生成摘要，跳过刷新视频列表`)
    }
    
    if (statusResponse) {
      const status = statusResponse.status
      
      // 更新持久化状态
      if (status === 'processing' || status === 'pending' || status === 'downloading') {
        saveProcessingState(videoId, status)
      } else {
        // 如果状态已完成或失败，移除持久化状态
        removeProcessingState(videoId)
      }
      
      // 如果视频处理完成或失败，停止轮询
      if (status === 'completed' || status === 'failed') {
        if (timers[videoId]) {
          clearIntervalFn(timers[videoId])
          delete timers[videoId]
        }
      }
    }
  } catch (error) {
    console.error('轮询视频状态失败:', error)
    // 出错时不停止轮询，继续尝试
  }
}
