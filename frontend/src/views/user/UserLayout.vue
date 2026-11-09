<template>
  <el-container class="user-layout">
    <el-header class="header">
      <div class="title">TTAgent · 三角洲行动助手</div>
      <el-menu mode="horizontal" :default-active="activeMenu" router :ellipsis="false">
        <el-menu-item index="/">数据</el-menu-item>
      </el-menu>
      <router-link to="/admin" class="admin-link">管理后台</router-link>
      <span class="user-info">
        <span class="username">{{ username }}</span>
        <el-button link type="primary" @click="logout">退出</el-button>
      </span>
    </el-header>
    <el-main>
      <router-view />
    </el-main>

    <!-- 右下角浮动对话按钮 -->
    <div class="chat-fab" @click="chatVisible = true">对话</div>

    <!-- 右侧对话抽屉（可弹出/关闭） -->
    <el-drawer v-model="chatVisible" title="涛涛对话" direction="rtl" size="380px">
      <ChatPanel />
    </el-drawer>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ChatPanel from '../../components/ChatPanel.vue'

const route = useRoute()
const router = useRouter()
const activeMenu = computed(() => route.path)
const chatVisible = ref(false)
const username = ref(localStorage.getItem('username') || '')
const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  router.push('/login')
}
</script>

<style scoped>
.user-layout { min-height: 100vh; position: relative; }
.header { background: #fff; border-bottom: 1px solid #eee; display: flex; align-items: center; padding: 0 24px; }
.title { font-size: 18px; font-weight: bold; color: #409eff; margin-right: 40px; white-space: nowrap; }
.header :deep(.el-menu) { border-bottom: none; flex: 1; }
.admin-link { color: #888; text-decoration: none; font-size: 14px; white-space: nowrap; }
.admin-link:hover { color: #409eff; }
.user-info { display: flex; align-items: center; gap: 8px; color: #888; font-size: 14px; white-space: nowrap; }
.username { color: #606266; }
.chat-fab {
  position: fixed;
  right: 24px;
  bottom: 24px;
  background: #409eff;
  color: #fff;
  padding: 12px 22px;
  border-radius: 24px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.4);
  z-index: 1000;
}
.chat-fab:hover { background: #66b1ff; }
</style>
