<script>
import { Scatter } from "vue-chartjs";
export default {
  extends: Scatter,
  name: "LineChart",
  // props: ["chartData", "chartOptions"],
  data() {
    return {
      // seqData: [],
      data: {
        // labels: ["Red", "Blue", "Yellow", "Green", "Purple", "Orange"],
        datasets: [
          {
            label: "# of Votes",
            data: [],
            // data: [1,2,3,4,5,6],
            // data: [
            //   { x: new Date(new Date().getTime() - 1), y: 19 },
            //   { x: new Date(new Date().getTime()), y: 15 },
            //   { x: new Date(new Date().getTime() + 1) + 1, y: 3 }
            // ],
            lineTension: 0,
            borderColor: "rgba(255, 99, 132, 0.2)",
            fill: false,
            showLine: true
            // backgroundColor: [
            //   "rgba(255, 99, 132, 0.2)",
            //   "rgba(54, 162, 235, 0.2)",
            //   "rgba(255, 206, 86, 0.2)",
            //   "rgba(75, 192, 192, 0.2)",
            //   "rgba(153, 102, 255, 0.2)",
            //   "rgba(255, 159, 64, 0.2)"
            // ],
            // borderColor: [
            //   "rgba(255, 99, 132, 1)",
            //   "rgba(54, 162, 235, 1)",
            //   "rgba(255, 206, 86, 1)",
            //   "rgba(75, 192, 192, 1)",
            //   "rgba(153, 102, 255, 1)",
            //   "rgba(255, 159, 64, 1)"
            // ],
            // borderWidth: 1
          }
          // {
          //   // data: [1,2,3,4,5,6],
          //   data: this.randomData(),
          //   // data: [
          //   //   { x: new Date(new Date().getTime() - 1), y: 9 },
          //   //   { x: new Date(new Date().getTime()), y: 5 },
          //   //   { x: new Date(new Date().getTime() + 1) + 1, y: 3 }
          //   // ],
          //   borderColor: "rgba(54, 162, 235, 0.2)",
          //   fill: false
          // }
        ]
      },
      options: {
        title: {
          display: true,
          text: "aaa"
        },
        // responsive: true,
        maintainAspectRatio: false,
        legend: {
          display: false
        },
        scales: {
          xAxes: [
            {
              // type: "linear",
              type: "time",
              time: {
                unit: "second"
              }
              // ticks: {
              //   suggestedMin: 0,
              //   suggestedMax: 20
              // }
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
    // this.data.datasets[0].data = [];
    let wsConnection = new WebSocket(
      `ws://${window.location.host}/stats/ws/function/asdlfkjaslkdfj`
    );
    wsConnection.onmessage = msg => {
      let data = JSON.parse(msg.data);
      if (this.data.datasets[0].data.length > 8)
        this.data.datasets[0].data.shift();
      this.data.datasets[0].data.push({
        x: new Date(data.timestamp * 1000),
        y: data.number
      });
      this.$data._chart.update();
      // this.renderChart(this.data, this.options);
      // console.log(this.data.datasets[0].data);
    };
    wsConnection.onerror = err => console.error(err);
    wsConnection.onclose = () => console.log("ws clsoe");
  },
  mounted() {
    this.renderChart(this.data, this.options);
  },
  watch: {
    // data: function(oldValue, newValue) {}
  },
  methods: {
    randomData() {
      let date = new Date().getTime();
      return [
        { x: new Date(date - 1000), y: Math.random() },
        { x: new Date(date), y: Math.random() },
        { x: new Date(date + 1000), y: Math.random() }
      ];
    }
  }
};
</script>
