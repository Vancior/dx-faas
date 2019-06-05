const http = require('http');
const control = require('./process_control.js');
const info = require('./info.js');
const { ResponseWriter, WorkflowTopology } = require('./utils.js');

const runtimeInfo = JSON.parse(process.env.DX_RUNTIME);
const hostIP = process.env.HOST_IP;  /* in case it's d in d */

let client = redis.createClient({ host: '172.17.42.1', port: 6380 })
let workflowMode = false;
// let isStart = false;
if (runtimeInfo.workflow != null) {
    workflowMode = true;
    // if (runtimeInfo.workflow.role === runtimeInfo.workflow.start_at)
    //     isStart = true;
}

const handler = (request, response) => {
    let body = [];
    // let startTime = new Date().getTime();
    request.on('error', err => {
        response.writeHead(200, {
            'Content-Type': 'application/json'
        });
        response.write(JSON.stringify({ status: 'fail', info: err.toString() }));
        response.end();
    }).on('data', data => {
        body.push(data);
    }).on('end', () => {
        body = Buffer.concat(body).toString();
        // let now = new Date().getTime();
        // console.log('time travel:', now - (JSON.parse(body).time) * 1000);

        let writer = new ResponseWriter(response, workflowMode)

        if (workflowMode) {
            let recordId = null;
            console.log(runtimeInfo.workflow.role, runtimeInfo.workflow.definition.StartAt);
            if (runtimeInfo.workflow.role !== runtimeInfo.workflow.definition.StartAt)
                client.incr('request/' + runtimeInfo.workflow.uri);
            // if (runtimeInfo.workflow.role !== runtimeInfo.workflow.definition.StartAt) {
            //     body = JSON.parse(body);
            //     recordId = body.recordId;
            //     body = body.data;  // data直接以string存储
            // }
            let tmpBody = JSON.parse(body);
            if (tmpBody.recordId != null) {
                recordId = tmpBody.recordId;
            }
            body = tmpBody.data;
            console.log(recordId);
            writer.setRecordId(recordId);
            writer.setRole(runtimeInfo.workflow.role);
            let topo = new WorkflowTopology(runtimeInfo.workflow.definition);
            writer.setWorkflow(topo);
        }
        else {
            client.incr('request/' + runtimeInfo.uri);
            let tmpBody = JSON.parse(body);
            if (tmpBody.recordId != null)
                console.log(tmpBody.recordId);
            body = tmpBody.data;
        }

        let result = control.getWorker();
        if (result.isNew) {
            result.worker.readyCallback = _p => {
                _p.responseWriter = writer;
                _p.stdin.write(JSON.stringify(request.headers));
                _p.stdin.write('\n');
                // _p.stdin.write(Buffer.concat(body).toString());
                _p.stdin.write(body);
                _p.stdin.write('\n');
            }
        }
        else {
            result.worker.responseWriter = writer;
            result.worker.stdin.write(JSON.stringify(request.headers));
            result.worker.stdin.write('\n');
            // result.worker.stdin.write(Buffer.concat(body).toString());
            result.worker.stdin.write(body);
            result.worker.stdin.write('\n');
        }
        // p.resp_cb = data => {
        // response.writeHead(200, {
        //     'Content-Type': 'application/json'
        // });
        // response.write(data.toString());
        // response.end();
        // console.log('serving time', new Date().getTime() - startTime);
        // }
        // console.log(Buffer.concat(body).toString());
        // data = { 'headers': request.headers, 'body': Buffer.concat(body).toString() }
    });
}

const server = http.createServer(handler);

server.listen(80, err => {
    if (err) {
        console.log('error: ' + err);
        let recordId = null;
        return;
    }
    const postData = JSON.stringify({ runtime_id: runtimeInfo.runtime_id, ip: info.ip });
    const request = http.request({
        method: 'POST',
        host: hostIP,
        port: 10008,
        path: '/',
        headers: {
            'Content-Type': 'application/json',
            'Content-Length': Buffer.byteLength(postData)
        },
        timeout: 3000
    });
    request.on('response', response => {
        let body = [];
        response.on('error', err => {
            console.error(err);
            server.close();
        }).on('data', data => {
            body.push(data);
        }).on('end', () => {
            console.log(Buffer.concat(body).toString());
            body = JSON.parse(Buffer.concat(body).toString());
            if (body.status !== 'success')
                server.close();
        })
    })
    request.on('error', err => {
        console.error(err);
    })
    // request.write(JSON.stringify({ runtime_id: runtimeInfo.runtime_id, ip: info.ip }));
    request.write(postData);
    request.end();

    let entrypoint = runtimeInfo.entrypoint.split('.');
    let initializer = runtimeInfo.initializer.split('.');
    if (initializer.length < 2)
        initializer = '';
    else
        initializer = initializer[1];
    control.changeEntry(`/data/function/${entrypoint[0]}.py`, entrypoint[1], initializer);
    control.getWorker();
    console.log('serving');
});
