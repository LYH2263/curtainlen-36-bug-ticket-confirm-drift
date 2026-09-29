<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const w = ref([])
onMounted(async () => { w.value = (await getJSON('/api/windows')).items })
</script>
<template><div class="page"><h1>概览</h1><p>{{ w.filter(x=>x.data_quality==='clean').length }} 扇可算窗</p></div></template>
