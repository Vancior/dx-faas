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
          {{ functionInfo.name }}
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
        <Col span="4">函数名称：</Col>
        <Col span="8">{{ functionInfo.name }}</Col>
        <Col span="4">资源URI：</Col>
        <Col span="8">{{ functionInfo.uri }}</Col>
      </Row>
      <Row class="info-line">
        <Col span="4">运行环境：</Col>
        <Col span="8">{{ functionInfo.environment }}</Col>
        <Col span="4">部署状态：</Col>
        <Col span="8">
          <i-switch v-model="isRunning">
            <span slot="open">是</span>
            <span slot="close">否</span>
          </i-switch>
        </Col>
      </Row>
      <Row class="info-line">
        <Col span="4">处理函数入口：</Col>
        <Col span="8">{{ functionInfo.handler }}</Col>
        <Col span="4">初始化函数入口：</Col>
        <Col span="8">{{ functionInfo.initializer }}</Col>
      </Row>
      <Row class="info-line">
        <Col span="4">CPU(单位算力)：</Col>
        <Col span="8">{{ functionInfo.cpu_limit }}</Col>
        <Col span="4">内存限制(MB)：</Col>
        <Col span="8">{{ functionInfo.memory_limit }}</Col>
      </Row>
      <Row class="info-line">
        <Col span="4">最大闲置时间(分)：</Col>
        <Col span="8">{{ functionInfo.max_idle_time }}</Col>
      </Row>
      <Row class="info-line">
        <Col span="12">
          <StatsLineChart
            :key="0"
            :title="'运行实例数'"
            :color="'rgba(255, 99, 132, 0.2)'"
            :url="
              'ws://' +
                window.location.host +
                '/stats/ws/function/' +
                functionInfo.uri
            "
            :height="300"
          />
        </Col>
        <Col span="12">
          <StatsLineChart
            :key="1"
            :title="'实时请求数'"
            :color="'rgba(54, 162, 235, 0.2)'"
            :url="
              'ws://' +
                window.location.host +
                '/stats/ws/request/' +
                functionInfo.uri
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
        <FormItem label="函数名称" prop="functionName">
          <Row>
            <Col span="12">
              <Input :value="functionInfo.name" disabled />
              <!-- <Input v-model="form.functionName" /> -->
            </Col>
          </Row>
        </FormItem>
        <FormItem label="URI" prop="functionURI">
          <Row>
            <Col span="20">
              <Input :value="functionInfo.uri" disabled />
              <!-- <Input v-model="form.functionURI" /> -->
              <!-- <span slot="prepend">这里是用户UID/function</span> -->
              <!-- </Input> -->
            </Col>
          </Row>
        </FormItem>
        <FormItem label="运行环境" prop="environment">
          <Row>
            <Col span="16">
              <Select v-model="form.environment">
                <Option value="python3">Python 3(3.7.2)</Option>
                <Option value="nodejs">Node.js(10.15.3LTS)</Option>
              </Select>
            </Col>
          </Row>
        </FormItem>
        <FormItem label="函数代码" prop="file">
          <Upload :before-upload="handleUpload" action="">
            <Button icon="md-cloud-upload">上传</Button>
            &nbsp;
            <span v-if="form.file !== null">{{ form.file.name }}</span>
          </Upload>
        </FormItem>
        <FormItem label="处理函数入口" prop="handler">
          <Row>
            <Col span="8">
              <Input v-model="form.handler" />
            </Col>
          </Row>
        </FormItem>
        <FormItem label="初始化函数入口" prop="initializer">
          <Row>
            <Col span="8">
              <Input v-model="form.initializer" />
            </Col>
          </Row>
        </FormItem>
        <FormItem label="CPU限制(单位算力)" prop="cpuLimit">
          <Row>
            <Col span="6">
              <Input type="number" v-model="form.cpuLimit" />
            </Col>
          </Row>
        </FormItem>
        <FormItem label="内存限制(MB)" prop="memoryLimit">
          <Row>
            <Col span="6">
              <Input type="number" v-model="form.memoryLimit" />
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
                  @init="aceInit"
                  lang="json"
                  theme="chrome"
                  width="100%"
                  height="200px"
                  style="font-size: 0.9em"
                />
              </Col>
            </Row>
          </FormItem>
          <FormItem label="输出数据">
            <Row>
              <Col span="24">
                <pre
                  style="width: 100%; padding: 10px; background: lightgray; max-height: 400px; overflow-y: auto; line-height: 1.3;"
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
// import LineChart from "@/charts/LineChart";
import StatsLineChart from "@/charts/StatsLineChart";
export default {
  name: "FunctionView",
  props: ["functionInfo"],
  components: { AceEditor: require("vue2-ace-editor"), StatsLineChart },
  data: function() {
    return {
      currentTab: "overview",
      testForm: {
        deviceIP: "",
        input: ""
      },
      form: {
        // functionName: "",
        // functionURI: "",
        environment: this.functionInfo.environment,
        // entrypoint: "main.handler",
        handler: this.functionInfo.handler,
        initializer: this.functionInfo.initializer,
        cpuLimit: this.functionInfo.cpu_limit,
        memoryLimit: this.functionInfo.memory_limit,
        maxIdleTime: this.functionInfo.max_idle_time,
        file: null,
        code_url: ""
      },
      rulesValidate: {
        environment: [{ type: "string", required: true }],
        file: [{ type: "file", required: true }],
        handler: [{ type: "string", required: true }],
        initializer: [{ type: "string", required: true }],
        memoryLimit: [{ type: "number", required: true }],
        cpuLimit: [{ type: "number", required: true }],
        maxIdleTime: [{ type: "number", required: true }]
      },
      output: "",
      window: window
    };
  },
  mounted: function() {
    console.log(this.functionInfo);
  },
  computed: {
    isRunning: {
      get: function() {
        if (this.functionInfo.status === "running") return true;
        else return false;
      },
      set: function() {}
    }
  },
  methods: {
    test: function() {
      this.axios
        .post("/test/function", {
          ip: this.testForm.deviceIP,
          uri: this.functionInfo.uri,
          data: this.testForm.input
        })
        .then(rep => {
          if (rep.status === 200) {
            if (rep.data.status === "success") {
              if (rep.data.data.status === "success") {
                let append = `ran on: ${rep.data.data.ip}, time cost: ${
                  rep.data.data.time
                }\n${JSON.stringify(rep.data.data.data, null, 4)}\n`;
                this.output += append;
              } else {
                let append = `error: ${rep.data.data.info}`;
                this.output += append;
              }
            } else throw new Error(rep.data.info);
          } else throw new Error(rep.status + rep.statusText);
        })
        .catch(err => {
          this.$Message.error(err.message);
        });
    },
    aceInit: function() {
      require("brace/ext/language_tools");
      require("brace/mode/json");
      require("brace/theme/chrome");
      // let editor = this.$refs.workflowEditor.editor;
      // editor.on("blur", this.updatePreview);
    },
    submit: function() {
      if (this.form.file !== null) {
        this.axios
          .post("/function/token", { uri: this.functionInfo.uri })
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
    handleUpload: function(file) {
      this.form.file = file;
      return false;
    }
  }
};
</script>

<style scoped>
.info-line {
  line-height: 40px;
  font-size: 1.1em;
}
</style>
