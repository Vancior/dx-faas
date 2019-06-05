import * as dagre from "dagre-d3";
import * as d3 from "d3";
import tippy from "tippy.js";

class WorkflowVis {
  constructor(svg, inner) {
    this.svg = svg;
    this.inner = inner;
    this.g = new dagre.graphlib.Graph({ compound: true }).setGraph({});

    this.svg.on("wheel", () => {
      d3.event.preventDefault();
      if (d3.event.wheelDelta > 0) {
        this.scale += 0.2;
        this.transformInner();
      } else {
        this.scale -= 0.2;
        this.transformInner();
      }
    });

    let previousPoint = null;
    this.svg.on("mousedown", () => {
      d3.event.preventDefault();
      previousPoint = { x: d3.event.screenX, y: d3.event.screenY };
    });
    this.svg.on("mousemove", () => {
      d3.event.preventDefault();
      if (previousPoint !== null) {
        // console.log(this.translateX, this.translateY);
        this.translateX += d3.event.screenX - previousPoint.x;
        this.translateY += d3.event.screenY - previousPoint.y;
        // console.log(this.translateX, this.translateY);
        previousPoint = { x: d3.event.screenX, y: d3.event.screenY };
        this.transformInner();
      }
    });
    this.svg.on("mouseup", () => {
      d3.event.preventDefault();
      previousPoint = null;
    });
    this.svg.on("mouseleave", () => {
      d3.event.preventDefault();
      previousPoint = null;
    });

    this.translateX = 0;
    this.translateY = 0;
    this.scale = 1;
  }

  clear() {
    this.inner.select("g").remove();
    this.g.setGraph({});
    // this.g = new dagre.graphlib.Graph({ compound: true }).setGraph({});
  }

  setNodes(nodes) {
    nodes.forEach(node => {
      this.g.setNode(node, { label: node });
    });
  }

  setEdges(edges) {
    edges.forEach(e => {
      this.g.setEdge(e.from, e.to, {
        label: e.label,
        curve: d3.curveBasis,
        arrowhead: "vee"
      });
    });
  }

  setStartNodes(nodes) {
    this.g.setNode("__start__", { label: "start", shape: "circle" });
    nodes.forEach(node => {
      this.g.setEdge("__start__", node, {
        curve: d3.curveBasis,
        arrowhead: "vee"
      });
    });
  }

  setEndNodes(nodes) {
    this.g.setNode("__end__", { label: "end", shape: "circle" });
    nodes.forEach(node => {
      this.g.setEdge(node, "__end__", {
        curve: d3.curveBasis,
        arrowhead: "vee"
      });
    });
  }

  setParents(parents) {
    parents.forEach(p => {
      this.g.setNode(p.parent, {
        label: "parallel",
        clusterLabelPos: "top"
      });
      // console.log(this.g.node(p.parent));
      // this.g.node(p.parent).rx = this.g.node(p.parent).ry = 12;
      this.g.setParent(p.child, p.parent);
    });
  }

  redraw() {
    this.g.nodes().forEach(v => {
      let node = this.g.node(v);
      node.rx = node.ry = 8;
    });

    let render = new dagre.render();
    render(this.inner, this.g);

    // if (tooltip) {
    //   this.g.nodes().forEach(v => {
    //     let node = this.g.node(v);
    //     if (node.elem != null) {
    //       tippy(node.elem);
    //     }
    //   });
    // }
    // this.inner.attr(
    //   "transform",
    //   `translate(${(this.svg.node().clientWidth - this.g.graph().width) /
    //     2}, ${(this.svg.node().clientHeight - this.g.graph().height) / 2})`
    // );
    this.translateX = (this.svg.node().clientWidth - this.g.graph().width) / 2;
    this.translateY =
      (this.svg.node().clientHeight - this.g.graph().height) / 2;
    // console.log(this.svg.node().clientWidth, this.svg.node().clientHeight);
    // console.log(this.g.graph().width, this.g.graph().height);
    this.scale = 1;
    this.transformInner();
  }

  transformInner() {
    // this.inner.attr(
    //   "transform",
    //   `translate(${(this.svg.node().clientWidth - this.g.graph().width) /
    //     2}, ${(this.svg.node().clientHeight - this.g.graph().height) /
    //     2}) scale(${this.scale})`
    // );
    this.inner.attr(
      "transform",
      `translate(${this.translateX}, ${this.translateY}) scale(${this.scale})`
    );
  }
}

class Workflow {
  constructor(definition) {
    this.definition = definition;
    this.tasks = this.parseTasks();
  }

  parseTasks() {
    let tasks = {};

    function _r(states) {
      Object.keys(states).forEach(k => {
        tasks[k] = states[k];
        if (states[k].Type === "Parallel") {
          let parallel = states[k];
          for (let b of parallel.Branches) _r(b.States);
        }
      });
    }

    _r(this.definition.States);
    return tasks;
  }

  toDAG() {
    let nodes = Object.keys(this.tasks);
    let startNodes = [this.definition.StartAt];
    let endNodes = [];
    let parents = [];
    let edges = [];

    let parallelBlockId = 0;

    nodes.forEach(k => {
      let task = this.tasks[k];
      if (task.Type === "Choice") {
        for (let c of task.Choices) {
          edges.push({ from: k, to: c.Next, label: c.Condition });
        }
        if (task.Default !== undefined)
          edges.push({ from: k, to: task.Default, label: "default" });
      } else if (task.Type === "Parallel") {
        let parallelBlock = "__parallel" + parallelBlockId + "__";
        parallelBlockId += 1;
        task.Branches.forEach(b => {
          edges.push({ from: k, to: b.StartAt, label: "" });
          let subWorkflow = new Workflow(b);
          Object.keys(subWorkflow.tasks).forEach(t => {
            parents.push({ parent: parallelBlock, child: t });
          });
        });
        if (task.Next !== undefined) {
          task.Branches.forEach(b => {
            edges.push({ from: b.StartAt, to: task.Next, label: "" });
          });
        }
      } else {
        if (task.Next !== undefined) {
          edges.push({ from: k, to: task.Next, label: "" });
        } else {
          endNodes.push(k);
        }
      }
    });

    return { nodes, edges, startNodes, endNodes, parents };
  }
}

class WorkflowUpdater {
  constructor(workflowVis, workflow) {
    this.workflowVis = workflowVis;
    this.workflow = workflow;
    this.tippyInstances = {};
  }

  update(role, status, ip, info) {
    console.log(info);
    // let state = this.workflow.tasks[role];
    let node = this.workflowVis.g.node(role);
    let rect = node.elem.getElementsByTagName("rect")[0];
    if (status === "succeed") rect.style.fill = "lightgreen";
    else if (status === "running") rect.style.fill = "lightblue";
    else rect.style.fill = "orangered";

    if (info.length > 200) info = info.slice(0, 200);
    if (this.tippyInstances[role] != null)
      this.tippyInstances[role].setContent(`node: ${ip}<br>info: ${info}`);
    else this.tippyInstances[role] = tippy(node.elem);
  }

  clear() {
    this.workflowVis.g.nodes().forEach(v => {
      let node = this.workflowVis.g.node(v);
      // console.log(node.elem);
      if (node.elem != null && node.elem.getElementsByTagName != null) {
        if (this.tippyInstances[v] != null)
          this.tippyInstances[v].setContent("");
        // node.elem.setAttribute("data-tippy-content", "");
        let list = node.elem.getElementsByTagName("rect");
        if (list.length > 0) list[0].style.fill = "white";
        // node.elem.getElementsByTagName("rect").forEach(rect => {
        //   rect.style.fill = "white";
        // });
      }
    });
  }
}

export { WorkflowVis, Workflow, WorkflowUpdater };
// module.exports = { WorkflowVis, Workflow };
// export default {
//   WorkflowVis: WorkflowVis
// };
