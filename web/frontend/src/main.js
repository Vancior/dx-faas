import Vue from "vue";
import App from "./App.vue";
import router from "./router";
import store from "./store";
import "./plugins/iview.js";

Vue.config.productionTip = false;
Vue.prototype.Navigator = window.navigator;

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount("#app");
