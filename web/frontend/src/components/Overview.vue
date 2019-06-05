<template>
  <Layout style="min-height: calc(100vh - 128px); width: 80%; margin: 0 auto;">
    <Header style="background: #f8f8f9; padding: 0;"> </Header>
    <Layout style="height: 100%; background: #fff; padding: 16px;">
      <h2>账户信息</h2>
      <Row>
        <Row class="info-line">
          <Col span="4">Access Key</Col>
          <Col span="20">{{ $store.getters.ak }}</Col>
        </Row>
        <Row class="info-line">
          <Col span="4">Secret Key</Col>
          <Col span="20">{{ $store.getters.sk }}</Col>
        </Row>
      </Row>
    </Layout>
  </Layout>
</template>

<script>
export default {
  name: "Overview",
  data: function() {
    return {};
  }
};
</script>

<style>
.info-line {
  line-height: 40px;
  font-size: 1.1em;
}
</style>
