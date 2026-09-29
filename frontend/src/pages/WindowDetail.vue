<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const props = defineProps({ id: String })
const w = ref(null)
onMounted(async () => { w.value = await getJSON(`/api/windows/${props.id}`) })
</script>
<template><div class="page" v-if="w"><h1>{{ w.name }}</h1><p v-if="w.data_quality==='dirty'" class="bad">{{ w.note }}</p><p>宽 {{ w.width }} 高 {{ w.height }} 褶倍 {{ w.fullness }}</p></div></template>
