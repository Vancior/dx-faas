import Vue from "vue";
import Router from "vue-router";

Vue.use(Router);

export default new Router({
  mode: "history",
  base: process.env.BASE_URL,
  routes: [
    {
      path: "/center",
      name: "center",
      component: () => import("./views/Center.vue"),
      children: [
        {
          path: "",
          component: () => import("./components/Overview")
        },
        {
          path: "function",
          component: () => import("./components/FunctionManage")
        },
        {
          path: "workflow",
          component: () => import("./components/WorkflowManage")
        },
        {
          path: "function/create",
          component: () => import("./components/FunctionCreate")
        },
        {
          path: "workflow/create",
          component: () => import("./components/WorkflowCreate")
        }
      ]
    },
    {
      path: "/about",
      name: "about",
      // route level code-splitting
      // this generates a separate chunk (about.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () =>
        import(/* webpackChunkName: "about" */ "./views/About.vue")
    },
    {
      path: "/login",
      name: "login",
      component: () => import("./views/Login.vue")
    },
    {
      path: "/register",
      name: "register",
      component: () => import("./views/Register.vue")
    },
    {
      path: "/404",
      name: "404",
      component: () => import("./views/404.vue")
    },
    {
      path: "/",
      redirect: "/center"
    },
    {
      path: "*",
      redirect: "/404"
    }
    // {
    //   path: "/",
    //   redirect: "/center"
    // }
  ]
});
