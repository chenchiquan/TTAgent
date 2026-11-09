<template>
  <div class="chat-panel">
    <div class="messages" ref="msgBox">
      <div v-for="(msg, i) in messages" :key="i" :class="['msg', msg.role]">
        <div class="bubble">{{ msg.content }}</div>
      </div>
      <el-empty v-if="!messages.length" description="开始和何涛对话吧喵" :image-size="60" />
    </div>
    <div class="input-area">
      <el-input
        v-model="input"
        placeholder="输入消息..."
        @keyup.enter="send"
        :disabled="loading"
      />
      <el-button type="primary" @click="send" :loading="loading">发送</el-button>
      <el-button @click="newChat" :disabled="loading">新对话</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const input = ref('')
const messages = ref([])
const msgBox = ref(null)
const loading = ref(false)

const scrollDown = async () => {
  await nextTick()
  if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
}

const send = async () => {
  if (!input.value.trim() || loading.value) return
  const userMsg = input.value
  messages.value.push({ role: 'user', content: userMsg })
  input.value = ''
  loading.value = true

  // 创建 assistant 消息，流式追加内容
  const assistantMsg = { role: 'agent', content: '' }
  messages.value.push(assistantMsg)

  try {
    // fetch POST 调 Java /api/chat（SSE 流式）
    const res = await fetch(`${api.defaults.baseURL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({ message: userMsg, history: [] })
    })

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()  // 保留最后不完整的一行
      for (const line of lines) {
        if (line.startsWith('data:')) {
          const data = line.slice(5).trim()
          if (data === '[DONE]') continue
          if (data.startsWith('[ERROR]')) {
            assistantMsg.content = data
            ElMessage.error('对话出错')
            break
          }
          assistantMsg.content += data
          scrollDown()
        }
      }
    }
  } catch (e) {
    assistantMsg.content = '[ERROR] 请求失败：' + e.message
    ElMessage.error('请求失败')
  } finally {
    loading.value = false
    scrollDown()
  }
}

// 开启新对话：清空所有消息
const newChat = () => {
  messages.value = []
  input.value = ''
}
</script>

<style scoped>
.chat-panel { display: flex; flex-direction: column; height: 100%; }
.messages { flex: 1; overflow-y: auto; padding: 12px; }
.msg { margin-bottom: 12px; display: flex; }
.msg.user { justify-content: flex-end; }
.msg.agent { justify-content: flex-start; }
.bubble { max-width: 75%; padding: 8px 12px; border-radius: 8px; word-break: break-word; white-space: pre-wrap; }
.msg.user .bubble { background: #409eff; color: #fff; }
.msg.agent .bubble { background: #f0f2f5; color: #333; }
.input-area { display: flex; gap: 8px; padding: 12px; border-top: 1px solid #eee; }
</style>
