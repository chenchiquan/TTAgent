<template>
  <el-container class="admin-layout">
    <el-aside width="200px" class="aside">
      <div class="logo">TTAgent 管理后台</div>
      <el-menu :default-active="activeMenu" router>
        <el-menu-item index="/admin/guns">枪械</el-menu-item>
        <el-menu-item index="/admin/ammo">弹药</el-menu-item>
        <el-menu-item index="/admin/attachments">配件</el-menu-item>
        <el-menu-item index="/admin/gun-attachments">兼容关系</el-menu-item>
        <el-menu-item index="/admin/prices">价格</el-menu-item>
      </el-menu>
      <div class="back-user">
        <router-link to="/">← 返回用户前台</router-link>
      </div>
    </el-aside>
    <el-container>
      <el-header class="header">{{ pageTitle }}</el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => route.path)
const pageTitle = computed(() => {
  const map = {
    guns: '枪械管理',
    ammo: '弹药管理',
    attachments: '配件管理',
    'gun-attachments': '兼容关系管理',
    prices: '价格管理'
  }
  const key = route.path.split('/').pop()
  return map[key] || '管理后台'
})
</script>

<style scoped>
.admin-layout { height: 100vh; }
.aside { background: #1f2733; color: #fff; display: flex; flex-direction: column; }
.logo { padding: 20px; font-size: 16px; font-weight: bold; color: #fff; border-bottom: 1px solid #333; }
.aside :deep(.el-menu) { background: #1f2733; border-right: none; }
.aside :deep(.el-menu-item) { color: #ccc; }
.aside :deep(.el-menu-item.is-active) { color: #409eff; background: #2a3441; }
.back-user { margin-top: auto; padding: 16px 20px; font-size: 13px; }
.back-user a { color: #888; text-decoration: none; }
.header {
  background: #fff;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: bold;
  color: #333;
}
</style>
