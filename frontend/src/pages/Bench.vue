<script setup>
import { onMounted, ref, watch } from 'vue'
import { getJSON, postJSON } from '../api'
import PanelCut from '../components/PanelCut.vue'
const windows = ref([]); const fabrics = ref([]); const wid = ref(1); const fid = ref(1)
const ticket = ref(null); const saved = ref(null); const err = ref('')
onMounted(async () => {
  windows.value = (await getJSON('/api/windows')).items.filter(x=>x.data_quality==='clean')
  fabrics.value = (await getJSON('/api/fabrics')).items.filter(x=>x.data_quality==='clean')
  if (windows.value.length) wid.value = windows.value[0].id
  if (fabrics.value.length) fid.value = fabrics.value[0].id
})
watch([wid, fid], () => { ticket.value = null; saved.value = null; err.value = '' })
async function dry() {
  err.value = ''; saved.value = null
  try { ticket.value = await postJSON('/api/tickets', { window_id: wid.value, fabric_id: fid.value }) }
  catch (e) { ticket.value = null; err.value = e.message }
}
async function confirm() {
  if (!ticket.value) return
  err.value = ''
  try {
    saved.value = await postJSON(`/api/tickets/${ticket.value.ticket_no}/confirm`, {})
    // 一次性票：确认成功后票即核销，数字以票面为准写入历史
    ticket.value = null
  } catch (e) { err.value = e.message }
}
</script>
<template><div class="page"><h1>算料</h1>
<select v-model.number="wid"><option v-for="x in windows" :key="x.id" :value="x.id">{{ x.name }}</option></select>
<select v-model.number="fid"><option v-for="x in fabrics" :key="x.id" :value="x.id">{{ x.name }}</option></select>
<button @click="dry">干算签票</button><button v-if="ticket" @click="confirm">确认落库</button>
<p v-if="ticket">算料票 {{ ticket.ticket_no }}（未使用），确认后写入历史</p>
<p v-if="saved">已落库，历史编号 #{{ saved.run_id }}（{{ saved.panels }} 幅 × {{ saved.cut_height }} m = {{ saved.meters }} m，票面数字）</p>
<p v-if="err" class="bad">{{ err }}</p>
<PanelCut v-if="ticket" :panels="ticket.panels" :cut-height="ticket.cut_height" :meters="ticket.meters" />
<PanelCut v-else-if="saved" :panels="saved.panels" :cut-height="saved.cut_height" :meters="saved.meters" />
</div></template>
