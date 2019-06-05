<script>
import { Scatter } from "vue-chartjs";
export default {
  extends: Scatter,
  name: "StatsLineChart",
  props: ["title", "color", "url"],
  data() {
    return {
      data: {
        datasets: [
          {
            data: [],
            lineTension: 0,
            borderColor: this.color,
            fill: false,
            showLine: true
          }
        ]
      },
      options: {
        title: {
          display: true,
          text: this.title
        },
        // responsive: true,
        maintainAspectRatio: false,
        legend: {
          display: false
        },
        scales: {
          xAxes: [
            {
              type: "time",
              time: {
                unit: "second"
              }
            }
          ],
          yAxes: [
            {
              ticks: {
                beginAtZero: true
              }
            }
          ]
        }
      }
    };
  },
  created() {
    let wsConnection = new WebSocket(this.url);
    //   `ws://${window.location.host}/stats/ws/function/asdlfkjaslkdfj`
    // );
    wsConnection.onmessage = msg => {
      let data = JSON.parse(msg.data);
      if (this.data.datasets[0].data.length > 8)
        this.data.datasets[0].data.shift();
      this.data.datasets[0].data.push({
        x: new Date(data.timestamp * 1000),
        y: data.number
      });
      this.$data._chart.update();
    };
    wsConnection.onerror = err => console.error(err);
    wsConnection.onclose = () => console.log("ws clsoe");
  },
  mounted() {
    this.renderChart(this.data, this.options);
  }
};
</script>
