<template>
  <Layout style="min-height: calc(100vh - 128px); width: 80%; margin: 0 auto;">
    <Header style="background: #f8f8f9; padding: 0;">
      <Button
        shape="circle"
        size="large"
        type="primary"
        @click="$router.push('/center/workflow/create')"
      >
        创建新工作流 </Button
      >&nbsp;
      <Button
        icon="md-refresh"
        shape="circle"
        size="large"
        type="default"
        @click="refreshWorkflows(() => selectWorkflow(selected_idx))"
      />
    </Header>
    <Layout style="height: 100%; background: #fff; padding: 16px;">
      <Row style="height: 100%;">
        <Col :xs="8" :sm="8" :md="6" :lg="4" style="height: 100%;">
          <Layout style="height: 100%; overflow-y: auto; background: #fff;">
            <h2>工作流列表</h2>
            <br />
            <ul>
              <li
                class="workflow-wrapper"
                v-for="(w, idx) in workflows"
                :key="idx"
                :id="'workflow' + idx"
                @click.prevent.stop="selectWorkflow(idx)"
              >
                <div class="workflow-name">
                  <Badge status="default" />
                  {{ w.name }}
                </div>
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
          <!-- <Layout>
            <WorkflowView
              v-for="(workflow, index) in current_workflow"
              :key="index"
              :workflowInfo="workflow"
            />
          </Layout> -->
          <Layout v-if="current_workflow">
            <WorkflowView
              :workflowInfo="current_workflow"
              :key="selected_idx"
            />
          </Layout>
        </Col>
      </Row>
    </Layout>
  </Layout>
</template>

<script>
import WorkflowView from "@/components/WorkflowView";
export default {
  name: "WorkflowManage",
  components: { WorkflowView },
  data: () => {
    return {
      workflows: [],
      current_workflow: null,
      selected_idx: 0
    };
  },
  mounted: function() {
    this.refreshWorkflows(() => {
      this.selectWorkflow(this.selected_idx);
    });
  },
  methods: {
    refreshWorkflows: function(callback) {
      this.axios
        .get("/workflow")
        .then(rep => {
          if (rep.status === 200) {
            if (rep.data.status === "success") {
              this.workflows = rep.data.data;
              if (callback !== undefined) this.$nextTick(callback);
            } else throw new Error(rep.data.info);
          } else throw new Error(rep.status + rep.statusText);
        })
        .catch(err => {
          console.error(err);
        });
    },
    selectWorkflow: function(idx) {
      if (idx < 0 || idx >= this.workflows.length) {
        return;
      }
      if (this.selected_idx !== null)
        document
          .querySelector("#workflow" + this.selected_idx)
          .classList.remove("selected");
      document.querySelector("#workflow" + idx).classList.add("selected");
      this.selected_idx = idx;
      // this.current_workflow = null;
      this.current_workflow = this.workflows[idx];
    }
  }
};
</script>

<style>
.workflow-wrapper {
  width: 100%;
  height: 32px;
  padding-left: 8px;
  list-style-type: none;
  cursor: pointer;
}

.workflow-wrapper:hover {
  background: #f8f8f9;
}

.workflow-wrapper.selected {
  background: #dcdee2;
}

.workflow-name {
  display: table-cell;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  vertical-align: middle;
  font-size: 1.1em;
  line-height: 32px;
}
</style>
