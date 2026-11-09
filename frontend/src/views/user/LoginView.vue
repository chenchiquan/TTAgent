<template>
  <div class="login-page">
    <el-card class="login-card">
      <h2 class="title">TTAgent · 登录</h2>
      <el-form @submit.prevent>
        <el-input
          v-model="form.username"
          placeholder="用户名"
          :prefix-icon="User"
          class="field"
        />
        <el-input
          v-model="form.password"
          type="password"
          placeholder="密码"
          show-password
          :prefix-icon="Lock"
          class="field"
          @keyup.enter="submit('login')"
        />
      </el-form>
      <div class="btns">
        <el-button type="primary" @click="submit('login')" :loading="loading">登录</el-button>
        <el-button @click="submit('register')" :loading="loading">注册</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import api from '../../api'

const router = useRouter()
const form = ref({ username: '', password: '' })
const loading = ref(false)

const submit = async (action) => {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const { data } = await api.post(`/api/auth/${action}`, form.value)
    if (action === 'register') {
      ElMessage.success('注册成功，请登录')
    } else {
      localStorage.setItem('token', data.token)
      localStorage.setItem('username', data.username)
      ElMessage.success('登录成功')
      router.push('/')
    }
  } catch (e) {
    // 后端抛 RuntimeException，Spring 默认错误体里有 message 字段
    ElMessage.error(e.response?.data?.message || '操作失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #409eff 0%, #667eea 100%);
}
.login-card { width: 360px; padding: 20px; }
.title { text-align: center; margin: 0 0 24px; color: #333; }
.field { margin-bottom: 16px; }
.btns { display: flex; gap: 12px; }
.btns .el-button { flex: 1; }
</style>
