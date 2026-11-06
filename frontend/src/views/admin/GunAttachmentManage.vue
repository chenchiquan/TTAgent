<template>
  <CrudTable api-name="gun-attachments" :columns="columns" :form-fields="formFields" />
</template>

<script setup>
import CrudTable from '../../components/CrudTable.vue'

const columns = [
  { prop: 'id', label: 'ID', width: 60 },
  { prop: 'gunId', label: '枪械ID', width: 90 },
  { prop: 'attachmentId', label: '配件ID', width: 90 },
  { prop: 'slot', label: '槽位', width: 100 },
  { prop: 'isActive', label: '激活', width: 70 },
]

const formFields = [
  { prop: 'gunId', label: '枪械ID', type: 'number' },
  { prop: 'attachmentId', label: '配件ID', type: 'number' },
  { prop: 'slot', label: '槽位', type: 'text' },
  { prop: 'isActive', label: '激活(1/0)', type: 'number', default: 1 },
]
</script>
