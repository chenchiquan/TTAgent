<template>
  <CrudTable api-name="prices" :columns="columns" :form-fields="formFields" />
</template>

<script setup>
import CrudTable from '../../components/CrudTable.vue'

const columns = [
  { prop: 'id', label: 'ID', width: 60 },
  { prop: 'itemType', label: '物品类型', width: 100 },
  { prop: 'itemId', label: '物品ID', width: 90 },
  { prop: 'price', label: '价格', width: 120 },
]

const formFields = [
  { prop: 'itemType', label: '物品类型(gun/ammo/attachment)', type: 'text' },
  { prop: 'itemId', label: '物品ID', type: 'number' },
  { prop: 'price', label: '价格', type: 'text' },
]
</script>
