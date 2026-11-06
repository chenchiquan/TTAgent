<template>
  <CrudTable api-name="guns" :columns="columns" :form-fields="formFields" />
</template>

<script setup>
import CrudTable from '../../components/CrudTable.vue'

// 表格显示的主要列
const columns = [
  { prop: 'code', label: '编码', width: 100 },
  { prop: 'name', label: '名称', width: 140 },
  { prop: 'type', label: '类型', width: 80 },
  { prop: 'caliber', label: '口径', width: 90 },
  { prop: 'fleshDamage', label: '肉体', width: 70 },
  { prop: 'armorDamage', label: '护甲', width: 70 },
  { prop: 'fireRate', label: '射速', width: 70 },
  { prop: 'verticalRecoil', label: '后座', width: 70 },
  { prop: 'hipfireAccuracy', label: '腰射', width: 70 },
  { prop: 'ergonomics', label: '据枪', width: 70 },
]

// 表单可编辑的全部字段
const formFields = [
  { prop: 'code', label: '编码', type: 'text' },
  { prop: 'name', label: '名称', type: 'text' },
  { prop: 'type', label: '类型', type: 'text' },
  { prop: 'caliber', label: '口径', type: 'text' },
  { prop: 'fleshDamage', label: '肉体伤害', type: 'number' },
  { prop: 'armorDamage', label: '护甲伤害', type: 'number' },
  { prop: 'fireRate', label: '射速(发/分)', type: 'number' },
  { prop: 'effectiveRange', label: '有效射程(米)', type: 'number' },
  { prop: 'muzzleVelocity', label: '初速(米/秒)', type: 'number' },
  { prop: 'ergonomics', label: '人机工效(据枪)', type: 'number' },
  { prop: 'verticalRecoil', label: '垂直后坐力', type: 'number' },
  { prop: 'horizontalRecoil', label: '水平后坐力', type: 'number' },
  { prop: 'hipfireAccuracy', label: '腰射精度', type: 'number' },
  { prop: 'adsSpeed', label: '开镜速度(ms)', type: 'number' },
  { prop: 'adsMoveSpeed', label: '开镜移速', type: 'number' },
  { prop: 'reloadTime', label: '换弹时间(ms)', type: 'number' },
  { prop: 'magazineSize', label: '弹匣容量', type: 'number' },
  { prop: 'weight', label: '重量(kg)', type: 'text' },
  { prop: 'baseSlots', label: '槽位(JSON)', type: 'textarea' },
  { prop: 'remark', label: '说明', type: 'textarea' },
  { prop: 'version', label: '版本', type: 'text', default: 'v1' },
  { prop: 'isActive', label: '激活(1/0)', type: 'number', default: 1 },
]
</script>
