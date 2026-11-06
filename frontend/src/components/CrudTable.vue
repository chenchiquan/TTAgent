<template>
  <div class="crud-table">
    <div class="toolbar">
      <el-input v-model="keyword" placeholder="搜索..." style="width: 200px" clearable />
      <el-button type="primary" @click="loadData">刷新</el-button>
      <el-button type="success" @click="openCreate">新增</el-button>
    </div>
    <el-table :data="filteredData" border stripe v-loading="loading" style="width: 100%">
      <el-table-column type="index" width="50" />
      <el-table-column
        v-for="col in columns"
        :key="col.prop"
        :prop="col.prop"
        :label="col.label"
        :width="col.width"
      />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-popconfirm title="确认删除？" @confirm="handleDelete(row)">
            <template #reference>
              <el-button size="small" type="danger">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑' : '新增'" width="640px">
      <el-form :model="form" label-width="130px">
        <el-form-item v-for="field in formFields" :key="field.prop" :label="field.label">
          <el-input-number v-if="field.type === 'number'" v-model="form[field.prop]" controls-position="right" />
          <el-input
            v-else-if="field.type === 'textarea'"
            v-model="form[field.prop]"
            type="textarea"
            :rows="3"
          />
          <el-input v-else v-model="form[field.prop]" :placeholder="field.placeholder || ''" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const props = defineProps({
  apiName: { type: String, required: true },     // 如 'guns'
  columns: { type: Array, default: () => [] },    // 表格列 [{prop,label,width}]
  formFields: { type: Array, default: () => [] }  // 表单字段 [{prop,label,type,default}]
})

const loading = ref(false)
const data = ref([])
const keyword = ref('')
const dialogVisible = ref(false)
const editing = ref(false)
const form = ref({})

const filteredData = computed(() => {
  if (!keyword.value) return data.value
  const kw = keyword.value.toLowerCase()
  return data.value.filter(row =>
    props.columns.some(col => String(row[col.prop] ?? '').toLowerCase().includes(kw))
  )
})

const loadData = async () => {
  loading.value = true
  try {
    const { data: res } = await api.get(`/api/${props.apiName}`)
    data.value = res
  } catch (e) {
    ElMessage.error('加载失败：' + (e.response?.data?.message || e.message))
  } finally {
    loading.value = false
  }
}

const openCreate = () => {
  editing.value = false
  form.value = {}
  props.formFields.forEach(f => {
    form.value[f.prop] = f.default ?? (f.type === 'number' ? 0 : '')
  })
  dialogVisible.value = true
}

const openEdit = (row) => {
  editing.value = true
  form.value = { ...row }
  dialogVisible.value = true
}

const handleSave = async () => {
  try {
    if (editing.value) {
      await api.put(`/api/${props.apiName}`, form.value)
    } else {
      await api.post(`/api/${props.apiName}`, form.value)
    }
    ElMessage.success(editing.value ? '已更新' : '已新增')
    dialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error('保存失败：' + (e.response?.data?.message || e.message))
  }
}

const handleDelete = async (row) => {
  try {
    await api.delete(`/api/${props.apiName}/${row.id}`)
    ElMessage.success('已删除')
    loadData()
  } catch (e) {
    ElMessage.error('删除失败：' + (e.response?.data?.message || e.message))
  }
}

onMounted(loadData)
</script>

<style scoped>
.toolbar { margin-bottom: 16px; display: flex; gap: 8px; }
</style>
