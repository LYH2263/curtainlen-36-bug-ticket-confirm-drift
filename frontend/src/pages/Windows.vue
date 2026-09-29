<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
onMounted(async () => { items.value = (await getJSON('/api/windows')).items })
</script>
<template><div class="page"><h1>窗户</h1><ul><li v-for="x in items" :key="x.id"><router-link :to="`/windows/${x.id}`">{{ x.name }}</router-link> {{ x.width }}×{{ x.height }}</li></ul></div></template>
