<template>
  <div class="cl-layout">
    <div class="cl-top"><strong>窗帘用布</strong></div>
    <div class="cl-body">
      <nav class="cl-tabs">
        <router-link to="/">概览</router-link>
        <router-link to="/windows">窗户</router-link>
        <router-link to="/fabrics">面料</router-link>
        <router-link to="/bench">算料</router-link>
        <router-link to="/fullness">褶倍</router-link>
        <router-link to="/history">记录</router-link>
        <router-link to="/settings">设置</router-link>
      </nav>
      <section class="cl-content"><router-view /></section>
      <aside class="cl-roll" aria-hidden="true"><div class="fabric-roll"></div></aside>
    </div>
  </div>
</template>
