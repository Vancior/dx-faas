<template>
  <Layout style="min-height: calc(100vh - 128px); width: 80%; margin: 0 auto;">
    <Header style="background: #f8f8f9; padding: 0;">
      <Button
        size="large"
        shape="circle"
        type="primary"
        @click="$router.push('/center/function/create')"
      >
        创建新函数 </Button
      >&nbsp;
      <Button
        size="large"
        shape="circle"
        type="default"
        icon="md-refresh"
        @click="refreshFunctions(() => {})"
      />
    </Header>
    <Layout style="height: 100%; background: #fff; padding: 16px;">
      <Row style="height: 100%;">
        <Col :xs="8" :sm="8" :md="6" :lg="4" style="height: 100%;">
          <Layout style="height: 100%; overflow-y: auto; background: #fff;">
            <h2>函数列表</h2>
            <br />
            <ul>
              <li
                class="function-wrapper"
                v-for="(f, idx) in functions"
                :key="idx"
                :id="'function' + idx"
                @click.prevent.stop="selectFunction(idx)"
              >
                <div class="function-name">
                  <!-- <Badge status="default" style="display: table-cell;" /> -->
                  <Badge status="default" />
                  {{ f.name }}
                </div>
                <!-- <div style="float: right">
                  <Badge
                    style="display: table-cell;"
                    class-name="d-background-red"
                    text="error"
                  />
                </div> -->
              </li>
            </ul>
          </Layout>
        </Col>
        <Col
          :xs="16"
          :sm="16"
          :md="18"
          :lg="20"
          style="height: 100%; padding-left: 16px;"
        >
          <Layout v-if="current_function">
            <FunctionView
              :functionInfo="current_function"
              :key="selected_idx"
            />
          </Layout>
        </Col>
      </Row>
    </Layout>
  </Layout>
</template>

<script>
import FunctionView from "@/components/FunctionView";
export default {
  name: "FunctionManage",
  components: { FunctionView },
  data: () => {
    return {
      create_page: false,
      functions: [],
      current_function: null,
      selected_idx: 0
    };
  },
  mounted: function() {
    this.refreshFunctions(() => {
      this.selectFunction(this.selected_idx);
    });
    // 'this' of callback is bind to the instance
    // this.$nextTick(function() {
    //   this.selectFunction(0);
    // });
  },
  methods: {
    refreshFunctions: function(callback) {
      this.axios
        .get("/function")
        .then(rep => {
          if (rep.status === 200) {
            if (rep.data.status === "success") {
              this.functions = rep.data.data;
              this.$nextTick(callback);
            } else throw new Error(rep.data.info);
          } else throw new Error(rep.status + rep.statusText);
        })
        .catch(err => {
          console.error(err);
        });
    },
    selectFunction: function(idx) {
      if (idx < 0 || idx >= this.functions.length) {
        console.log(this.functions);
        return;
      }
      if (this.selected_idx !== null)
        document
          .querySelector("#function" + this.selected_idx)
          .classList.remove("selected");
      document.querySelector("#function" + idx).classList.add("selected");
      this.selected_idx = idx;
      this.current_function = this.functions[idx];
    }
  }
};
</script>

<style>
.function-wrapper {
  /* display: inline-table; */
  width: 100%;
  height: 32px;
  /* line-height: 32px; */
  padding-left: 8px;
  list-style-type: none;
  cursor: pointer;
}

.function-wrapper:hover {
  background: #f8f8f9;
}

.function-wrapper.selected {
  background: #dcdee2;
}

.function-name {
  display: table-cell;
  /* max-width: 130px; */
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  vertical-align: middle;
  font-size: 1.1em;
  line-height: 32px;
}

.menu-item {
  display: inline-table;
  width: 100%;
  font-size: 1em;
}

.menu-icon {
  margin-right: 6px;
}
</style>
