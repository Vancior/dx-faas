<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script>
// import HelloWorld from './components/HelloWorld.vue'

export default {
  name: "App",
  components: {
    // HelloWorld
  }
};
</script>

<style>
html,
body {
  width: 100%;
  height: 100%;
}
html {
  background-color: #f5f7f9;
}

#app {
  /* font-family: 'Avenir', Helvetica, Arial, sans-serif; */
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  /* text-align: center; */
  /* color: #2c3e50; */
  /* background-color: #f8f8f9; */
  background-color: #f5f7f9;
  height: 100%;
}

.d-right {
  float: right !important;
}

.d-background-red {
  background: #ed4014 !important;
}

.d-background-green {
  background: #19be6b !important;
}

.d-background-blue {
  background: #2db7f5 !important;
}
</style>
