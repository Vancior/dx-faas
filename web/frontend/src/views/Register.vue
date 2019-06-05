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
              注册
            </p>
            <Form :rules="rulesValidate" :model="form">
              <FormItem label="邮箱" prop="email">
                <Input type="email" v-model="form.email" />
              </FormItem>
              <FormItem label="密码" prop="password">
                <Input type="password" v-model="form.password" />
              </FormItem>
              <FormItem label="确认密码" prop="confirm">
                <Input type="password" v-model="form.confirm" />
              </FormItem>
              <Button type="success" long @click="register">注册</Button>
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
        email: [
          { required: true },
          { type: "email" },
          {
            validator: (rule, value, callback) => {
              this.axios.post("/user/validate", { email: value }).then(rep => {
                if (rep.status === 200) {
                  if (rep.data.status === "success") callback();
                  else callback(new Error(rep.data.info));
                } else callback(new Error(rep.status + rep.statusText));
              });
            },
            trigger: "blur"
          }
        ],
        password: [{ required: true }],
        confirm: [
          { required: true },
          {
            validator: (rule, value, callback) => {
              if (value === this.form.password) callback();
              else callback(new Error("密码不一致"));
            }
          }
        ]
      },
      form: {
        email: "",
        password: "",
        confirm: ""
      }
    };
  },
  methods: {
    register: function() {
      this.axios
        .post("/user/register", {
          email: this.form.email,
          password: this.form.password
        })
        .then(rep => {
          console.log(rep);
          if (rep.status === 200) {
            if (rep.data.status === "success") {
              this.$Message.success("注册成功");
              this.$router.push("/login");
            } else this.$Message.error(rep.data.info);
          } else this.$Message.error(rep.status + rep.statusText);
        })
        .catch(function(err) {
          console.error(err);
        });
    }
  }
};
</script>
