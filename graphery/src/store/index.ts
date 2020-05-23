import Vue from 'vue';
import Vuex from 'vuex';

Vue.use(Vuex);

import meta from '@/store/modules/meta';
import notifications from '@/store/modules/notifications';
import tutorials from '@/store/modules/tutorials';
import settings from '@/store/modules/settings';

export default new Vuex.Store({
  modules: {
    meta,
    notifications,
    tutorials,
    settings,
  },
  state: {
    drawer: false,
  },
  mutations: {
    CHANGE_DRAWER_STATE(state, value) {
      state.drawer = value;
    },
  },
  actions: {
    changeDrawerState({ commit }, value) {
      commit('CHANGE_DRAWER_STATE', value);
    },
  },
});
