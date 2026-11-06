<template>
  <div class="data-view">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="枪械" name="guns">
        <el-table :data="guns" border stripe v-loading="loading">
          <el-table-column prop="name" label="名称" width="140" />
          <el-table-column prop="type" label="类型" width="80" />
          <el-table-column prop="caliber" label="口径" width="90" />
          <el-table-column prop="fleshDamage" label="肉体伤害" width="90" />
          <el-table-column prop="armorDamage" label="护甲伤害" width="90" />
          <el-table-column prop="fireRate" label="射速" width="70" />
          <el-table-column prop="verticalRecoil" label="后座" width="70" />
          <el-table-column prop="hipfireAccuracy" label="腰射" width="70" />
          <el-table-column prop="ergonomics" label="据枪" width="70" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="弹药" name="ammo">
        <el-table :data="ammo" border stripe>
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="caliber" label="口径" />
          <el-table-column prop="caliberClass" label="口径分类" />
          <el-table-column prop="penetration" label="穿透等级" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="配件" name="attachments">
        <el-table :data="attachments" border stripe>
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="category" label="类别" />
          <el-table-column prop="slotType" label="槽位" />
          <el-table-column prop="verticalRecoilBonus" label="后座加成" />
          <el-table-column prop="ergonomicsBonus" label="据枪加成" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="价格" name="prices">
        <el-table :data="prices" border stripe>
          <el-table-column prop="itemType" label="物品类型" />
          <el-table-column prop="itemId" label="物品ID" />
          <el-table-column prop="price" label="价格" />
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'

const activeTab = ref('guns')
const loading = ref(false)
const guns = ref([])
const ammo = ref([])
const attachments = ref([])
const prices = ref([])

const loadAll = async () => {
  loading.value = true
  try {
    const [g, a, at, p] = await Promise.all([
      api.get('/api/guns'),
      api.get('/api/ammo'),
      api.get('/api/attachments'),
      api.get('/api/prices')
    ])
    guns.value = g.data
    ammo.value = a.data
    attachments.value = at.data
    prices.value = p.data
  } catch (e) {
    console.error('加载数据失败', e)
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)
</script>

<style scoped>
.data-view { padding: 20px; }
</style>
