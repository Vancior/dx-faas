import Vue from "vue";
import Vuex from "vuex";
import axios from "axios";
import VueAxios from "vue-axios";
import VueCookies from "vue-cookies";

axios.defaults.baseURL = "/api";

Vue.use(Vuex);
Vue.use(VueAxios, axios);
Vue.use(VueCookies);

export default new Vuex.Store({
  state: {
    user: {}
  },
  getters: {
    nickname: state => state.user.nickname,
    ak: state => state.user.ak,
    sk: state => state.user.sk
  },
  mutations: {
    update(state, payload) {
      state.user = payload;
    }
  },
  actions: {}
});
