(window["webpackJsonp"]=window["webpackJsonp"]||[]).push([["chunk-2d0c5196"],{"3e3a":function(t,e,r){"use strict";r.r(e);var n=function(){var t=this,e=t.$createElement,r=t._self._c||e;return r("Layout",{staticStyle:{height:"100%",width:"80%",margin:"0 auto"}},[r("Row",[r("Header",{staticStyle:{background:"transparent",padding:"0"}},[r("Button",{attrs:{size:"large",shape:"circle",type:"default",icon:"md-arrow-round-back"},on:{click:function(e){return t.$router.replace("/center/function")}}}),t._v("\n       \n      "),r("Button",{attrs:{size:"large",shape:"circle",type:"primary"},on:{click:function(e){return t.submit()}}},[t._v("提交")])],1),r("Layout",{staticStyle:{height:"100%",background:"#fff",padding:"50px 100px 0 100px"}},[r("Form",{attrs:{"label-position":"left","label-width":100,rules:t.rulesValidate,model:t.form}},[r("FormItem",{attrs:{label:"函数名称",prop:"functionName"}},[r("Row",[r("Col",{attrs:{span:"12"}},[r("Input",{model:{value:t.form.functionName,callback:function(e){t.$set(t.form,"functionName",e)},expression:"form.functionName"}})],1)],1)],1),r("FormItem",{attrs:{label:"URI",prop:"functionURI"}},[r("Row",[r("Col",{attrs:{span:"20"}},[r("Input",{model:{value:t.form.functionURI,callback:function(e){t.$set(t.form,"functionURI",e)},expression:"form.functionURI"}},[r("span",{attrs:{slot:"prepend"},slot:"prepend"},[t._v("系统将加入UID作为前缀")])])],1)],1)],1),r("FormItem",{attrs:{label:"运行环境",prop:"environment"}},[r("Row",[r("Col",{attrs:{span:"16"}},[r("Select",{model:{value:t.form.environment,callback:function(e){t.$set(t.form,"environment",e)},expression:"form.environment"}},[r("Option",{attrs:{value:"python3"}},[t._v("Python 3(3.7.2)")]),r("Option",{attrs:{value:"nodejs"}},[t._v("Node.js(10.15.3LTS)")])],1)],1)],1)],1),r("FormItem",{attrs:{label:"函数代码",prop:"file"}},[r("Upload",{attrs:{"before-upload":t.handleUpload,action:""}},[r("Button",{attrs:{icon:"md-cloud-upload"}},[t._v("上传")]),t._v("\n             \n            "),null!==t.form.file?r("span",[t._v(t._s(t.form.file.name))]):t._e()],1)],1),r("FormItem",{attrs:{label:"处理函数入口",prop:"handler"}},[r("Row",[r("Col",{attrs:{span:"8"}},[r("Input",{model:{value:t.form.handler,callback:function(e){t.$set(t.form,"handler",e)},expression:"form.handler"}})],1)],1)],1),r("FormItem",{attrs:{label:"初始化函数入口",prop:"initializer"}},[r("Row",[r("Col",{attrs:{span:"8"}},[r("Input",{model:{value:t.form.initializer,callback:function(e){t.$set(t.form,"initializer",e)},expression:"form.initializer"}})],1)],1)],1),r("FormItem",{attrs:{label:"CPU限制(单位算力)",prop:"cpuLimit"}},[r("Row",[r("Col",{attrs:{span:"6"}},[r("Input",{attrs:{type:"number"},model:{value:t.form.cpuLimit,callback:function(e){t.$set(t.form,"cpuLimit",t._n(e))},expression:"form.cpuLimit"}})],1)],1)],1),r("FormItem",{attrs:{label:"内存限制(MB)",prop:"memoryLimit"}},[r("Row",[r("Col",{attrs:{span:"6"}},[r("Input",{attrs:{type:"number"},model:{value:t.form.memoryLimit,callback:function(e){t.$set(t.form,"memoryLimit",t._n(e))},expression:"form.memoryLimit"}})],1)],1)],1),r("FormItem",{attrs:{label:"最大闲置时间(Minute)",prop:"maxIdleTime"}},[r("Row",[r("Col",{attrs:{span:"6"}},[r("Input",{attrs:{type:"number"},model:{value:t.form.maxIdleTime,callback:function(e){t.$set(t.form,"maxIdleTime",t._n(e))},expression:"form.maxIdleTime"}})],1)],1)],1),r("FormItem",{attrs:{label:"立即部署"}},[r("i-switch",[r("span",{attrs:{slot:"open"},slot:"open"},[t._v("是")]),r("span",{attrs:{slot:"close"},slot:"close"},[t._v("否")])])],1)],1)],1)],1)],1)},o=[],i=r("2b0e"),a={name:"FunctionCreate",data:function(){return{form:{functionName:"",functionURI:"",environment:"",handler:"main.handler",initializer:"main.initializer",cpuLimit:2,memoryLimit:128,maxIdleTime:60,file:null,code_url:""},rulesValidate:{functionName:[{type:"string",required:!0,message:"函数名称不能为空"}],functionURI:[{type:"string",required:!0,pattern:/^[A-Za-z0-9-]+$/},{validator:function(t,e,r){i["default"].axios.post("/function/validate",{uri:e}).then(function(t){"success"===t.data.status?r():r(new Error(t.data.info))}).catch(function(t){r(new Error(t))})},trigger:"blur"}],environment:[{type:"string",required:!0}],file:[{type:"file",required:!0}],handler:[{type:"string",required:!0}],initializer:[{type:"string",required:!0}],memoryLimit:[{type:"number",required:!0}],cpuLimit:[{type:"number",required:!0}],maxIdleTime:[{type:"number",required:!0}]}}},methods:{submit:function(){var t=this;this.axios.post("/function/token",{uri:this.form.functionURI}).then(function(e){if(200===e.status){if("success"===e.data.status){if(null==t.form.file)throw new Error("文件未上传");return t.axios.put(e.data.data,t.form.file,{headers:{"Content-Type":t.form.file.type}})}throw new Error(e.data.info)}throw new Error(e.status+e.statusText)}).then(function(e){if(200===e.status)return t.axios.post("/function/create",{name:t.form.functionName,uri:t.form.functionURI,cpu_limit:t.form.cpuLimit,memory_limit:t.form.memoryLimit,max_idle_time:t.form.maxIdleTime,environment:t.form.environment,handler:t.form.handler,initializer:t.form.initializer,code_url:t.form.code_url});throw new Error(e.status+e.statusText)}).then(function(e){if(200!==e.status)throw new Error(e.status+e.statusText);if("success"!==e.data.status)throw new Error(e.data.info);t.$Message.success("创建成功"),t.$router.push("/center/function")}).catch(function(e){t.$Message.error(e.message)})},handleUpload:function(t){return this.form.file=t,!1}}},s=a,l=r("2877"),m=Object(l["a"])(s,n,o,!1,null,null,null);e["default"]=m.exports}}]);
//# sourceMappingURL=chunk-2d0c5196.1e732125.js.map