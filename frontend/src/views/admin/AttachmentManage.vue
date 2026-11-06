<template>
  <CrudTable api-name="attachments" :columns="columns" :form-fields="formFields" />
</template>

<script setup>
import CrudTable from '../../components/CrudTable.vue'

const columns = [
  { prop: 'code', label: '编码', width: 120 },
  { prop: 'name', label: '名称', width: 140 },
  { prop: 'category', label: '类别', width: 80 },
  { prop: 'slotType', label: '槽位', width: 90 },
  { prop: 'verticalRecoilBonus', label: '后座加成', width: 90 },
  { prop: 'ergonomicsBonus', label: '据枪加成', width: 90 },
]

const formFields = [
  { prop: 'code', label: '编码', type: 'text' },
  { prop: 'name', label: '名称', type: 'text' },
  { prop: 'category', label: '类别', type: 'text' },
  { prop: 'slotType', label: '槽位', type: 'text' },
  { prop: 'fleshDamageBonus', label: '肉体伤害加成', type: 'number' },
  { prop: 'armorDamageBonus', label: '护甲伤害加成', type: 'number' },
  { prop: 'ergonomicsBonus', label: '人机工效(据枪)加成', type: 'number' },
  { prop: 'verticalRecoilBonus', label: '垂直后坐力加成', type: 'number' },
  { prop: 'horizontalRecoilBonus', label: '水平后坐力加成', type: 'number' },
  { prop: 'hipfireAccuracyBonus', label: '腰射精度加成', type: 'number' },
  { prop: 'adsSpeedBonus', label: '开镜速度加成', type: 'number' },
  { prop: 'adsMoveSpeedBonus', label: '开镜移速加成', type: 'number' },
  { prop: 'fireRateBonus', label: '射速加成', type: 'number' },
  { prop: 'effectiveRangeBonus', label: '有效射程加成', type: 'number' },
  { prop: 'unlockedSlots', label: '解锁槽位(JSON)', type: 'textarea' },
  { prop: 'version', label: '版本', type: 'text', default: 'v1' },
  { prop: 'isActive', label: '激活(1/0)', type: 'number', default: 1 },
]
</script>
