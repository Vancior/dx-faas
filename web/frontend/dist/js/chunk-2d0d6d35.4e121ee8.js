(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-2d0d6d35"],{"73cf":function(t,s,e){"use strict";e.r(s);var r=function(){var t=this,s=t.$createElement,e=t._self._c||s;return e("Layout",{staticStyle:{height:"100%"}},[e("Row",{staticStyle:{height:"100%"}},[e("Col",{staticStyle:{height:"100%"},attrs:{xs:1,sm:4,md:7,lg:9}},[t._v(" ")]),e("Col",{staticStyle:{height:"100%"},attrs:{xs:22,sm:16,md:10,lg:6}},[e("Layout",{staticStyle:{position:"relative",top:"50%",transform:"translateY(-68%)"}},[e("Card",{staticStyle:{width:"100%","padding-bottom":"20px"}},[e("p",{attrs:{slot:"title"},slot:"title"},[t._v("\n            注册\n          ")]),e("Form",{attrs:{rules:t.rulesValidate,model:t.form}},[e("FormItem",{attrs:{label:"邮箱",prop:"email"}},[e("Input",{attrs:{type:"email"},model:{value:t.form.email,callback:function(s){t.$set(t.form,"email",s)},expression:"form.email"}})],1),e("FormItem",{attrs:{label:"密码",prop:"password"}},[e("Input",{attrs:{type:"password"},model:{value:t.form.password,callback:function(s){t.$set(t.form,"password",s)},expression:"form.password"}})],1),e("FormItem",{attrs:{label:"确认密码",prop:"confirm"}},[e("Input",{attrs:{type:"password"},model:{value:t.form.confirm,callback:function(s){t.$set(t.form,"confirm",s)},expression:"form.confirm"}})],1),e("Button",{attrs:{type:"success",long:""},on:{click:t.register}},[t._v("注册")])],1)],1)],1)],1),e("Col",{attrs:{xs:1,sm:3,md:6,lg:9,stlye:"height: 100%;"}},[t._v(" ")])],1)],1)},a=[],o={name:"Login",data:function(){var t=this;return{rulesValidate:{email:[{required:!0},{type:"email"},{validator:function(s,e,r){t.axios.post("/user/validate",{email:e}).then(function(t){200===t.status?"success"===t.data.status?r():r(new Error(t.data.info)):r(new Error(t.status+t.statusText))})},trigger:"blur"}],password:[{required:!0}],confirm:[{required:!0},{validator:function(s,e,r){e===t.form.password?r():r(new Error("密码不一致"))}}]},form:{email:"",password:"",confirm:""}}},methods:{register:function(){var t=this;this.axios.post("/user/register",{email:this.form.email,password:this.form.password}).then(function(s){console.log(s),200===s.status?"success"===s.data.status?(t.$Message.success("注册成功"),t.$router.push("/login")):t.$Message.error(s.data.info):t.$Message.error(s.status+s.statusText)}).catch(function(t){console.error(t)})}}},i=o,l=e("2877"),n=Object(l["a"])(i,r,a,!1,null,null,null);s["default"]=n.exports}}]);
//# sourceMappingURL=chunk-2d0d6d35.4e121ee8.js.map