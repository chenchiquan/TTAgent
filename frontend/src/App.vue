<template>
  <div class="app">
    <header class="header">
      <h1>TTAgent - 三角洲行动助手</h1>
      <span class="status" :class="{ ok: isOk }">{{ statusText }}</span>
    </header>

    <nav class="nav">
      <button
        v-for="tab in tabs"
        :key="tab"
        @click="currentTab = tab"
        :class="{ active: currentTab === tab }"
      >
        {{ tab }}
      </button>
    </nav>

    <main class="card">
      <p class="placeholder" v-if="currentTab === '对话'">对话界面占位，后续接入 /chat 接口。</p>
      <p class="placeholder" v-if="currentTab === '枪械分析'">枪械数值分析占位，后续接入 /gun 接口。</p>
      <p class="placeholder" v-if="currentTab === '改枪推荐'">改枪推荐占位，后续接入 /loadout 接口。</p>
      <p class="placeholder" v-if="currentTab === '价格'">价格信息占位，后续接入 /price 接口。</p>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from './api'

const tabs = ['对话', '枪械分析', '改枪推荐', '价格']
const currentTab = ref('对话')

const isOk = ref(false)
const statusText = ref('后端未连接')

onMounted(async () => {
  try {
    const { data } = await api.get('/health')
    if (data.status === 'ok') {
      isOk.value = true
      statusText.value = '后端已连接'
    }
  } catch (e) {
    isOk.value = false
    statusText.value = '后端未连接'
  }
})
</script>

<style>
body {
  margin: 0;
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
  background: #f5f6fa;
}
.app {
  max-width: 900px;
  margin: 40px auto;
  padding: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #1f2733;
  color: #fff;
  padding: 16px 20px;
  border-radius: 8px;
}
.header h1 {
  font-size: 18px;
  margin: 0;
}
.status {
  font-size: 13px;
  padding: 4px 10px;
  border-radius: 12px;
  background: #e74c3c;
  color: #fff;
}
.status.ok {
  background: #2ecc71;
}
.nav {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}
.nav button {
  padding: 8px 14px;
  border: 1px solid #dcdfe6;
  background: #fff;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}
.nav button.active {
  border-color: #409eff;
  color: #409eff;
}
.card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-top: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
.placeholder {
  color: #888;
  font-size: 14px;
}
</style>
