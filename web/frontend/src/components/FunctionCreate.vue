<template>
  <!-- <Layout style="height: 100%; width: 60%; margin: 0 auto;"> -->
  <Layout style="height: 100%; width: 80%; margin: 0 auto;">
    <Row>
      <!-- <Col :xs="1" :sm="1" :md="2" :lg="4">&nbsp;</Col> -->
      <!-- <Col :xs="22" :sm="22" :md="20" :lg="16"> -->
      <Header style="background: transparent; padding: 0;">
        <Button
          size="large"
          shape="circle"
          type="default"
          icon="md-arrow-round-back"
          @click="$router.replace('/center/function')"
        />
        &nbsp;
        <Button size="large" shape="circle" type="primary" @click="submit()"
          >提交</Button
        >
      </Header>
      <Layout
        style="height: 100%; background: #fff; padding: 50px 100px 0 100px;"
      >
        <Form
          label-position="left"
          :label-width="100"
          :rules="rulesValidate"
          :model="form"
        >
          <FormItem label="函数名称" prop="functionName">
            <Row>
              <Col span="12">
                <Input v-model="form.functionName" />
              </Col>
            </Row>
          </FormItem>
          <FormItem label="URI" prop="functionURI">
            <Row>
              <Col span="20">
                <Input v-model="form.functionURI">
                  <span slot="prepend">系统将加入UID作为前缀</span>
                </Input>
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
                <Input type="number" v-model.number="form.cpuLimit" />
              </Col>
            </Row>
          </FormItem>
          <FormItem label="内存限制(MB)" prop="memoryLimit">
            <Row>
              <Col span="6">
                <Input type="number" v-model.number="form.memoryLimit" />
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
    </Row>
  </Layout>
</template>

<script>
import Vue from "vue";
export default {
  name: "FunctionCreate",
  data: function() {
    return {
      form: {
        functionName: "",
        functionURI: "",
        environment: "",
        // entrypoint: "main.handler",
        handler: "main.handler",
        initializer: "main.initializer",
        cpuLimit: 2,
        memoryLimit: 128,
        maxIdleTime: 60,
        file: null,
        code_url: ""
      },
      rulesValidate: {
        functionName: [
          { type: "string", required: true, message: "函数名称不能为空" }
        ],
        functionURI: [
          { type: "string", required: true, pattern: /^[A-Za-z0-9-]+$/ },
          {
            validator(rule, value, callback) {
              Vue.axios
                .post("/function/validate", { uri: value })
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
        environment: [{ type: "string", required: true }],
        file: [{ type: "file", required: true }],
        handler: [{ type: "string", required: true }],
        initializer: [{ type: "string", required: true }],
        memoryLimit: [{ type: "number", required: true }],
        cpuLimit: [{ type: "number", required: true }],
        maxIdleTime: [{ type: "number", required: true }]
      }
    };
  },
  methods: {
    submit: function() {
      this.axios
        .post("/function/token", { uri: this.form.functionURI })
        .then(rep => {
          if (rep.status === 200) {
            if (rep.data.status === "success") {
              if (this.form.file == null) throw new Error("文件未上传");
              return this.axios.put(rep.data.data, this.form.file, {
                headers: {
                  "Content-Type": this.form.file.type
                }
              });
              // var form = new FormData();
              // for (var i of rep.data.data.args) {
              //   form.set(i[0], i[1]);
              // }
              // form.set("file", this.form.file);
              // return this.axios.post(rep.data.data.url, form, {
              //   headers: { "Content-Type": "multipart/form-data" },
              //   withCredentials: true
              // });
            } else throw new Error(rep.data.info);
          } else throw new Error(rep.status + rep.statusText);
        })
        .then(rep => {
          if (rep.status === 200) {
            return this.axios.post("/function/create", {
              name: this.form.functionName,
              uri: this.form.functionURI,
              cpu_limit: this.form.cpuLimit,
              memory_limit: this.form.memoryLimit,
              max_idle_time: this.form.maxIdleTime,
              environment: this.form.environment,
              handler: this.form.handler,
              initializer: this.form.initializer,
              code_url: this.form.code_url
            });
          } else throw new Error(rep.status + rep.statusText);
        })
        .then(rep => {
          if (rep.status === 200) {
            if (rep.data.status === "success") {
              this.$Message.success("创建成功");
              this.$router.push("/center/function");
            } else throw new Error(rep.data.info);
          } else throw new Error(rep.status + rep.statusText);
        })
        .catch(err => {
          this.$Message.error(err.message);
        });
    },
    handleUpload: function(file) {
      this.form.file = file;
      return false;
    }
  }
};
</script>

<style></style>
