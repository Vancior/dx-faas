<template>
  <Layout style="height: 100%;">
    <Row style="height: 100%;">
      <Col :xs="1" :sm="4" :md="7" :lg="9" style="height: 100%;">&nbsp;</Col>
      <Col :xs="22" :sm="16" :md="10" :lg="6" style="height: 100%;">
        <Layout
          style="position: relative; top: 50%; transform: translateY(-68%);"
        >
          <Card style="width: 100%; padding-bottom: 20px;">
            <p slot="title">
              登录
            </p>
            <Form :rules="rulesValidate" :model="form">
              <FormItem label="邮箱" prop="email">
                <Input type="email" v-model="form.email" />
              </FormItem>
              <FormItem label="密码" prop="password">
                <Input type="password" v-model="form.password" />
              </FormItem>
              <Button type="success" long @click="login">登录</Button>
            </Form>
          </Card>
        </Layout>
      </Col>
      <Col :xs="1" :sm="3" :md="6" :lg="9" stlye="height: 100%;">&nbsp;</Col>
    </Row>
  </Layout>
</template>

<script>
export default {
  name: "Login",
  data: function() {
    return {
      rulesValidate: {
        email: [{ required: true }, { type: "email" }],
        password: [{ required: true }]
      },
      form: {
        email: "",
        password: ""
      }
    };
  },
  mounted: function() {
    this.$cookies.remove("user-token");
  },
  methods: {
    login: function() {
      this.axios
        .post("/user/login", {
          email: this.form.email,
          password: this.form.password
        })
        .then(rep => {
          console.log(rep);
          if (rep.status === 200) {
            if (rep.data.status === "success") {
              this.$Message.success("登录成功");
              this.$router.push("/center");
              return this.axios.get("/user/info");
            } else throw new Error(rep.data.info);
          } else throw new Error(rep.status + rep.statusText);
        })
        .then(rep => {
          if (rep.status === 200) {
            if (rep.data.status === "success") {
              this.$store.commit("update", rep.data.data);
            } else throw new Error(rep.data.info);
          } else throw new Error(rep.status + rep.statusText);
        })
        .catch(err => {
          this.$Message.error(err.message);
          // console.error(err);
        });
    }
  }
};
</script>
