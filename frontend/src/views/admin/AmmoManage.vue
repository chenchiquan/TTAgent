<template>
  <CrudTable api-name="ammo" :columns="columns" :form-fields="formFields" />
</template>

<script setup>
import CrudTable from '../../components/CrudTable.vue'

const columns = [
  { prop: 'code', label: '编码', width: 120 },
  { prop: 'name', label: '名称', width: 140 },
  { prop: 'caliber', label: '口径', width: 90 },
  { prop: 'caliberClass', label: '口径分类', width: 100 },
  { prop: 'penetration', label: '穿透等级', width: 90 },
]

const formFields = [
  { prop: 'code', label: '编码', type: 'text' },
  { prop: 'name', label: '名称', type: 'text' },
  { prop: 'caliber', label: '口径', type: 'text' },
  { prop: 'caliberClass', label: '口径分类', type: 'text' },
  { prop: 'penetration', label: '穿透等级', type: 'number' },
  { prop: 'version', label: '版本', type: 'text', default: 'v1' },
  { prop: 'isActive', label: '激活(1/0)', type: 'number', default: 1 },
]
</script>
