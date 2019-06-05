<template>
  <Layout style="background: #fff; padding: 20px;">
    <Row>
      <Menu
        mode="horizontal"
        theme="light"
        active-name="overview"
        @on-select="currentTab = $event"
      >
        <h2 style="display: inline-block; float: left; margin-right: 20px;">
          {{ workflowInfo.name }}
        </h2>
        <MenuItem name="overview">
          概览
        </MenuItem>
        <MenuItem name="edit">
          编辑
        </MenuItem>
        <MenuItem name="test">
          测试
        </MenuItem>
      </Menu>
    </Row>
    <Row v-show="currentTab === 'overview'">
      <Row class="info-line" style="margin-top: 20px;">
        <Col span="4">工作流名称：</Col>
        <Col span="8">{{ workflowInfo.name }}</Col>
        <Col span="4">资源URI：</Col>
        <Col span="8">{{ workflowInfo.uri }}</Col>
      </Row>
      <Row class="info-line">
        <Col span="4">最大闲置时间(分)：</Col>
        <Col span="8">{{ workflowInfo.max_idle_time }}</Col>
        <Col span="4">部署状态：</Col>
        <Col span="8">
          <i-switch v-model="isRunning">
            <span slot="open">是</span>
            <span slot="close">否</span>
          </i-switch>
        </Col>
      </Row>
      <Row class="info-line">
        <Col span="12">
          <StatsLineChart
            :key="1"
            :title="'实时请求数'"
            :color="'rgba(54, 162, 235, 0.2)'"
            :url="
              'ws://' +
                window.location.host +
                '/stats/ws/request/' +
                workflowInfo.uri
            "
            :height="300"
          />
        </Col>
      </Row>
    </Row>
    <Row v-show="currentTab === 'edit'">
      <Form
        label-position="left"
        :label-width="130"
        :rules="rulesValidate"
        :model="form"
        style="margin-top: 30px;"
      >
        <FormItem label="工作流名称" prop="workflowName">
          <Row>
            <Col span="12">
              <Input :value="workflowInfo.name" disabled />
              <!-- <Input v-model="form.functionName" /> -->
            </Col>
          </Row>
        </FormItem>
        <FormItem label="URI" prop="workflowURI">
          <Row>
            <Col span="20">
              <Input :value="workflowInfo.uri" disabled />
              <!-- <Input v-model="form.functionURI" /> -->
              <!-- <span slot="prepend">这里是用户UID/function</span> -->
              <!-- </Input> -->
            </Col>
          </Row>
        </FormItem>
        <FormItem label="可选函数列表">
          <Row>
            <Col span="12">
              <input style="position: absolute; left: -999em;" id="dummy-uri" />
              <ul
                style="list-style: none; max-height: 100px; overflow-y: scroll"
              >
                <li
                  v-for="(f, idx) in functionList"
                  :key="idx"
                  style="border-top: solid 1px lightgrey"
                  :style="
                    idx === functionLastOne
                      ? 'border-bottom: solid 1px lightgrey'
                      : ''
                  "
                >
                  {{ f.name }} (URI: {{ f.uri }})
                  <Tooltip :content="'copy: ' + f.uri" placement="top">
                    <Icon
                      size="16"
                      type="ios-copy-outline"
                      style="color: blue; cursor: pointer;"
                      @click="copyToClipboard(f.uri)"
                    />
                  </Tooltip>
                </li>
              </ul>
            </Col>
          </Row>
        </FormItem>
        <FormItem label="工作流定义(JSON有限状态机)" prop="definition">
          <Row>
            <Col span="14">
              <AceEditor
                ref="workflowEditor"
                v-model="form.definition"
                @init="aceInit"
                lang="json"
                theme="chrome"
                value
                width="100%"
                height="430px"
                style="font-size: 0.9em;"
              />
            </Col>
            <Col span="10">
              <svg id="workflow-preview" style="width: 100%; height: 430px;">
                <g></g>
              </svg>
            </Col>
          </Row>
        </FormItem>
        <FormItem label="最大闲置时间(Minute)" prop="maxIdleTime">
          <Row>
            <Col span="6">
              <Input type="number" v-model="form.maxIdleTime" />
            </Col>
          </Row>
        </FormItem>
        <FormItem>
          <Button type="primary">提交</Button>
        </FormItem>
      </Form>
    </Row>
    <Row v-show="currentTab === 'test'">
      <Row>
        <Form
          label-position="left"
          :label-width="130"
          :model="testForm"
          style="margin-top: 30px"
        >
          <FormItem label="物联网节点IP" prop="deviceIP">
            <Row>
              <Col span="8">
                <Input type="text" v-model="testForm.deviceIP" />
              </Col>
              <Col span="1">&nbsp;</Col>
              <Col span="8">
                <Button type="primary" @click="test">发送</Button>
              </Col>
            </Row>
          </FormItem>
          <FormItem label="输入数据(JSON)" prop="input">
            <Row>
              <Col span="24">
                <AceEditor
                  ref="inputEditor"
                  v-model="testForm.input"
                  lang="json"
                  theme="chrome"
                  width="100%"
                  height="170px"
                  style="font-size: 0.9em"
                />
              </Col>
            </Row>
          </FormItem>
          <FormItem label="工作流状态">
            <Row>
              <Col span="14">
                <svg id="workflow-test" style="width: 100%; height: 420px;">
                  <g></g>
                </svg>
              </Col>
              <Col span="10">
                <pre
                  style="width: 100%; padding: 10px; background: lightgray; max-height: 420px; overflow-y: auto; line-height: 1.3;"
                  >{{ output }}
                </pre>
              </Col>
            </Row>
          </FormItem>
        </Form>
      </Row>
      <Row> </Row>
    </Row>
  </Layout>
</template>

<script>
import * as d3 from "d3";
import {
  WorkflowVis,
  Workflow,
  WorkflowUpdater
} from "@/assets/workflow-vis.js";
export default {
  name: "WorkflowView",
  props: ["workflowInfo"],
  components: { AceEditor: require("vue2-ace-editor") },
  data: function() {
    return {
      currentTab: "overview",
      testForm: {
        deviceIP: "",
        input: ""
      },
      form: {
        definition: this.workflowInfo.definition,
        maxIdleTime: this.workflowInfo.max_idle_time
      },
      functionList: [],
      rulesValidate: {
        definition: [{ type: "string", required: true }],
        maxIdleTime: [{ type: "number", required: true }]
      },
      workflowUpdater: null,
      output: "",
      wsConnection: null
    };
  },
  mounted: function() {
    console.log(this.workflowInfo);
    this.axios
      .get("/function")
      .then(rep => {
        if (rep.status === 200) {
          if (rep.data.status === "success") {
            this.functionList = rep.data.data;
          } else throw new Error(rep.data.info);
        } else throw new Error(rep.status + rep.statusText);
      })
      .catch(err => {
        console.error(err);
      });
    // this.updatePreview();
    require("brace/ext/language_tools");
    require("brace/mode/json");
    require("brace/theme/chrome");
  },
  computed: {
    isRunning: {
      get: function() {
        if (this.workflowInfo.status === "running") return true;
        else return false;
      },
      set: function() {}
    },
    functionLastOne: function() {
      return Object.keys(this.functionList).length - 1;
    }
  },
  watch: {
    currentTab: function(newValue) {
      if (newValue === "edit") setTimeout(this.updatePreview, 500);
      else if (newValue === "test") setTimeout(this.testInitialize, 500);
    },
    workflowInfo: function(newValue) {
      this.form.definition = newValue.definition;
      this.form.maxIdleTime = newValue.maxIdleTime;
    }
  },
  beforeDestroy: function() {
    if (this.wsConnection !== null) {
      let readyState = this.wsConnection.readyState;
      if (readyState !== WebSocket.CLOSED && readyState === WebSocket.CLOSING)
        this.wsConnection.close();
    }
    this.wsConnection = null;
  },
  methods: {
    test() {
      this.workflowUpdater.clear();
      this.axios
        .post("/test/workflow", {
          ip: this.testForm.deviceIP,
          uri: this.workflowInfo.uri,
          data: this.testForm.input
        })
        .then(rep => {
          if (rep.status === 200) {
            if (rep.data.status === "success") {
              //   let append = `ran on: ${rep.data.data.ip}, time cost: ${
              //     rep.data.data.time
              //   }\n${JSON.stringify(rep.data.data.data, null, 4)}\n`;
              this.output += `${rep.data.data}\n`;
              let recordId = rep.data.data;
              if (this.wsConnection !== null) {
                let readyState = this.wsConnection.readyState;
                if (
                  readyState !== WebSocket.CLOSED &&
                  readyState === WebSocket.CLOSING
                )
                  this.wsConnection.close();
              }
              this.wsConnection = new WebSocket(
                `ws://${window.location.host}/test/ws/${recordId}`
              );
              this.wsConnection.onmessage = msg => {
                // console.log(msg.data);
                let data = JSON.parse(msg.data);
                this.workflowUpdater.update(
                  data.role,
                  data.status,
                  data.ip,
                  data.info
                );
              };
              this.wsConnection.onerror = err => console.error(err);
              this.wsConnection.onclose = () => console.log("ws close");
            } else throw new Error(rep.data.info);
          } else throw new Error(rep.status + rep.statusText);
        })
        .catch(err => {
          this.$Message.error(err.message);
        });
    },
    aceInit: function() {
      let editor = this.$refs.workflowEditor.editor;
      editor.on("blur", this.updatePreview);
    },
    submit: function() {
      if (this.form.file !== null) {
        this.axios
          .post("/function/token", { uri: this.workflowInfo.uri })
          .then(rep => {
            if (rep.status === 200) {
              if (rep.data.status === "success") {
                return this.axios.put(rep.data.data, this.form.file, {
                  headers: {
                    "Content-Type": this.form.file.type
                  }
                });
              } else throw new Error(rep.data.info);
            } else throw new Error(rep.status + rep.statusText);
          })
          .then(this.modify)
          .catch(err => {
            this.$$Message.error(err.message);
          });
      } else {
        try {
          this.modify({ status: 200 });
        } catch (err) {
          this.$Message.error(err.message);
        }
      }
    },
    modify: function(rep) {
      if (rep.status === 200) {
        this.axios
          .post("/function/create", {
            name: this.form.functionName,
            uri: this.form.functionURI,
            memory_limit: this.form.memoryLimit,
            max_idle_time: this.form.maxIdleTime,
            environment: this.form.environment,
            entrypoint: this.form.entrypoint,
            code_url: this.form.code_url
          })
          .then(rep => {
            if (rep.status === 200) {
              if (rep.data.status === "success") {
                this.$Message.success("创建成功");
                this.$router.push("/center/function");
              } else throw new Error(rep.data.info);
            } else throw new Error(rep.status + rep.statusText);
          });
      } else throw new Error(rep.status + rep.statusText);
    },
    updatePreview() {
      try {
        let svg = d3.select("#workflow-preview");
        let inner = svg.select("g");
        let vis = new WorkflowVis(svg, inner);
        let workflow = new Workflow(JSON.parse(this.form.definition));
        let dag = workflow.toDAG();
        vis.clear();
        vis.setNodes(dag.nodes);
        vis.setEdges(dag.edges);
        vis.setStartNodes(dag.startNodes);
        vis.setEndNodes(dag.endNodes);
        vis.setParents(dag.parents);
        vis.redraw();
      } catch (err) {
        console.log(err);
      }
    },
    copyToClipboard(uri) {
      console.log(uri);
      let node = document.querySelector("#dummy-uri");
      node.value = uri;
      node.select();
      document.execCommand("copy");
    },
    testInitialize() {
      let svg = d3.select("#workflow-test");
      let inner = svg.select("g");
      let vis = new WorkflowVis(svg, inner);
      let workflow = new Workflow(JSON.parse(this.workflowInfo.definition));
      let dag = workflow.toDAG();
      vis.clear();
      vis.setNodes(dag.nodes);
      vis.setEdges(dag.edges);
      vis.setStartNodes(dag.startNodes);
      vis.setEndNodes(dag.endNodes);
      vis.setParents(dag.parents);
      vis.redraw(true);
      this.workflowUpdater = new WorkflowUpdater(vis, workflow);
    }
  }
};
</script>

<style>
.info-line {
  line-height: 40px;
  font-size: 1.1em;
}

.node rect,
.node circle,
.node ellipse {
  stroke: #333;
  fill: #fff;
  stroke-width: 1px;
}

.edgePath path {
  stroke: #333;
  fill: #333;
  stroke-width: 1.5px;
}

.cluster rect {
  stroke: #333;
  fill: #fff;
  stroke-dasharray: 5;
}
</style>
