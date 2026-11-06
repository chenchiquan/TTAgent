<template>
  <div class="chat-panel">
    <div class="messages" ref="msgBox">
      <div v-for="(msg, i) in messages" :key="i" :class="['msg', msg.role]">
        <div class="bubble">{{ msg.content }}</div>
      </div>
      <el-empty v-if="!messages.length" description="开始和 Agent 对话吧" :image-size="60" />
    </div>
    <div class="input-area">
      <el-input
        v-model="input"
        placeholder="输入消息..."
        @keyup.enter="send"
      />
      <el-button type="primary" @click="send">发送</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'

const input = ref('')
const messages = ref([])
const msgBox = ref(null)

const send = async () => {
  if (!input.value.trim()) return
  messages.value.push({ role: 'user', content: input.value })
  input.value = ''
  // TODO: 后续接 Python AI 服务 SSE 流式输出，现在先返回占位
  messages.value.push({ role: 'agent', content: '对话功能开发中，后续接入 AI 服务' })
  await nextTick()
  if (msgBox.value) msgBox.value.scrollTop = msgBox.value.scrollHeight
}
</script>

<style scoped>
.chat-panel { display: flex; flex-direction: column; height: 100%; }
.messages { flex: 1; overflow-y: auto; padding: 12px; }
.msg { margin-bottom: 12px; display: flex; }
.msg.user { justify-content: flex-end; }
.msg.agent { justify-content: flex-start; }
.bubble { max-width: 75%; padding: 8px 12px; border-radius: 8px; word-break: break-word; }
.msg.user .bubble { background: #409eff; color: #fff; }
.msg.agent .bubble { background: #f0f2f5; color: #333; }
.input-area { display: flex; gap: 8px; padding: 12px; border-top: 1px solid #eee; }
</style>
