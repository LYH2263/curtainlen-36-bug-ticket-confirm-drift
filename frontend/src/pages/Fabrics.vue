<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
onMounted(async () => { items.value = (await getJSON('/api/fabrics')).items })
</script>
<template><div class="page"><h1>面料</h1><div v-for="f in items" :key="f.id" class="fab">{{ f.name }} 门幅{{ f.fabric_width }}m</div></div></template>
