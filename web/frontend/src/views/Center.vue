<template>
  <div class="layout" style="min-height: 100%">
    <Layout style="min-height: 100%">
      <Header>
        <Menu
          mode="horizontal"
          theme="dark"
          @on-select="jump_if($event)"
          active-name="dashboard"
        >
          <MenuItem name="logo" style="cursor: auto">
            <img style="height: 60px" src="@/assets/logo.png" />
          </MenuItem>
          <MenuItem name="dashboard">
            <Icon type="ios-stats" />
            概览
          </MenuItem>
          <MenuItem name="function">
            <Icon class="menu-icon" type="ios-cube" />
            函数管理
          </MenuItem>
          <MenuItem name="workflow">
            <Icon class="menu-icon" type="ios-git-network" />
            工作流管理
          </MenuItem>
          <Submenu class="d-right" name="account">
            <template slot="title">
              <Icon type="md-person" />
              {{ $store.getters.nickname }}
            </template>
            <MenuItem name="logout" @click.native.stop.prevent="logout">
              注销
            </MenuItem>
          </Submenu>
        </Menu>
      </Header>
      <!-- <transition name="fade" mode="out-in"> -->
      <router-view />
      <!-- </transition> -->
    </Layout>
  </div>
</template>

<script>
export default {
  name: "Center",
  data: function() {
    return {
      identity: undefined,
      jump_routes: {
        dashboard: "/center",
        function: "/center/function",
        workflow: "/center/workflow"
      }
    };
  },
  mounted: function() {
    this.axios
      .get("/user/verify")
      .then(rep => {
        if (rep.status !== 200 || rep.data.status !== "success")
          throw new Error("not login");
        else return this.axios.get("/user/info");
      })
      .then(rep => {
        if (rep.status === 200) {
          if (rep.data.status === "success") {
            this.$store.commit("update", rep.data.data);
          } else throw new Error(rep.data.info);
        } else throw new Error(rep.status + rep.statusText);
      })
      .catch(() => {
        this.$router.replace("/login");
      });
  },
  methods: {
    jump: function(path) {
      this.$router.push(path);
    },
    jump_if: function(event) {
      if (this.jump_routes[event] != null)
        this.$router.push(this.jump_routes[event]);
    },
    logout() {
      this.$router.push("/login");
    }
  }
};
</script>
