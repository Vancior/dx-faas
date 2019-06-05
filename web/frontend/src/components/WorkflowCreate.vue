<template>
  <!-- <Layout style="height: 100%; width: 60%; margin: 0 auto;"> -->
  <Layout style="height: 100%; width: 80%; margin: 0 auto;">
    <!-- <Row>
      <Col :xs="1" :sm="1" :md="2" :lg="4">&nbsp;</Col>
    <Col :xs="22" :sm="22" :md="20" :lg="16">-->
    <Header style="background: transparent; padding: 0;">
      <Button
        size="large"
        shape="circle"
        type="default"
        icon="md-arrow-round-back"
        @click="$router.replace('/center/workflow')"
      />&nbsp;
      <Button size="large" shape="circle" type="primary" @click="submit()"
        >提交</Button
      >
    </Header>
    <Layout style="height: 100%; background: #fff; padding: 50px 50px 0 50px;">
      <Form
        label-position="left"
        :label-width="100"
        :rules="rulesValidate"
        :model="form"
      >
        <FormItem label="工作流名称" prop="workflowName">
          <Row>
            <Col span="12">
              <Input v-model="form.workflowName" />
            </Col>
          </Row>
        </FormItem>
        <FormItem label="URI" prop="workflowURI">
          <Row>
            <Col span="20">
              <Input v-model="form.workflowURI" />
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
                height="420px"
                style="font-size: 0.9em;"
              />
            </Col>
            <Col span="10">
              <svg id="workflow-preview" style="width: 100%; height: 420px;">
                <g></g>
              </svg>
            </Col>
          </Row>
        </FormItem>
        <FormItem label="最大闲置时间(Minute)" prop="maxIdleTime">
          <Row>
            <Col span="6">
              <Input type="number" v-model.number="form.maxIdleTime" />
            </Col>
          </Row>
        </FormItem>
        <FormItem label="立即部署">
          <i-switch>
            <span slot="open">是</span>
            <span slot="close">否</span>
          </i-switch>
        </FormItem>
      </Form>
    </Layout>
    <!-- </Col> -->
    <!-- <Col :xs="1" :sm="1" :md="2" :lg="4">&nbsp;</Col> -->
    <!-- </Row> -->
  </Layout>
</template>

<script>
import Vue from "vue";
import * as d3 from "d3";
// import * as dagre from "dagre-d3";
import { WorkflowVis, Workflow } from "@/assets/workflow-vis.js";
export default {
  name: "WorkflowCreate",
  components: { AceEditor: require("vue2-ace-editor") },
  data: function() {
    return {
      form: {
        workflowName: "",
        workflowURI: "",
        definition: "",
        maxIdleTime: 60
      },
      functionList: [],
      rulesValidate: {
        workflowName: [
          { type: "string", required: true, message: "工作流名称不能为空" }
        ],
        workflowURI: [
          { type: "string", required: true, pattern: /^[A-Za-z0-9-]+$/ },
          {
            validator(rule, value, callback) {
              Vue.axios
                .post("/workflow/validate", { uri: value })
                .then(function(rep) {
                  if (rep.data.status === "success") callback();
                  else callback(new Error(rep.data.info));
                })
                .catch(function(err) {
                  callback(new Error(err));
                });
            },
            trigger: "blur"
          }
        ],
        definition: [{ type: "string", required: true }],
        maxIdleTime: [{ type: "number", required: true }]
      }
    };
  },
  mounted: function() {
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
  },
  methods: {
    aceInit: function() {
      require("brace/ext/language_tools");
      require("brace/mode/json");
      require("brace/theme/chrome");
      let editor = this.$refs.workflowEditor.editor;
      editor.on("blur", this.updatePreview);
    },
    submit: function() {
      this.axios
        .post("/workflow/create", {
          name: this.form.workflowName,
          uri: this.form.workflowURI,
          definition: this.form.definition,
          max_idle_time: this.form.maxIdleTime
        })
        .then(rep => {
          if (rep.status === 200) {
            if (rep.data.status === "success") {
              this.$Message.success("创建成功");
              this.$router.push("/center/workflow");
            } else throw new Error(rep.data.info);
          } else throw new Error(rep.status + rep.statusText);
        })
        .catch(err => {
          this.$Message.error(err.message);
        });
    },
    updatePreview() {
      console.log("update");
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
    }
  },
  computed: {
    functionLastOne: function() {
      return Object.keys(this.functionList).length - 1;
    }
  }
};
</script>

<style>
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
