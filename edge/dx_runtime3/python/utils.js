const crypto = require('crypto');
const http = require('http');
const jsonata = require('jsonata');
const redis = require('redis');

const infoData = require('./info.js');

const hostIP = process.env.HOST_IP;
const fogIP = process.env.FOG_IP;

let client = redis.createClient({ host: '172.17.42.1', port: 6380 })

function uuidv4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

class WorkflowTopology {
    constructor(workflow) {
        this.workflow = workflow;

        this.allStates = {};
        function _r(t) {
            if (this.allStates[t] !== undefined)
                return;
            let state = this.getState(t);
            if (state.Type === 'Task') {
                this.allStates[t] = state;
                if (state.Next !== undefined)
                    _r.call(this, state.Next);
            }
            else if (state.Type === 'Choice') {
                state.Choices.forEach(i => {
                    _r.call(this, i.Next);
                });
                if (state.Default !== undefined)
                    _r.call(this, state.Default);
            }
            else if (state.Type === 'Parallel') {
                state.Branches.forEach(b => {
                    let sub = new WorkflowTopology(b);
                    Object.keys(sub.allStates).forEach(k => {
                        this.allStates[k] = sub.allStates[k];
                    });
                })
            }
            else {
                if (state.Next !== undefined)
                    _r.call(this, state.Next);
            }
        }
        _r.call(this, this.workflow.StartAt);
    }
    setRecordId(recordId) {
        this.recordId = recordId;
    }
    getState(role) {
        return this.workflow.States[role];
    }
    executeState(role, data) {
        try {
            let state = this.workflow.States[role];
            this['do' + state.Type](state, data);
            this.reporter(role, 'succeed');
        } catch (err) {
            this.reporter(role, 'fail', err.message);
        }
    }
    doTask(state, data) {
        console.log('***** doTask *****');
        // console.log(state.runtime.ip, state.runtime.runtime_id);
        let postData = JSON.stringify({ 'recordId': this.recordId, 'data': JSON.stringify(data) });
        this.request = http.request({
            method: 'POST',
            host: hostIP,
            port: 6999,
            path: '/' + state.runtime.ip + '/' + state.runtime.runtime_id,
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(postData)
            },
            timeout: 3000
        });
        this.request.on('response', response => {
            let body = [];
            response.on('error', err => {
                console.error(err);
            }).on('data', data => {
                body.push(data);
            }).on('end', () => {
                console.log('send to next', Buffer.concat(body).toString());
            })
        });
        this.request.on('error', err => {
            console.error(err);
        });
        this.request.write(postData);
    }
    doParallel(state, data) {
        console.log('***** doParallel *****');
        console.log(state.Branches);
        for (let b of state.Branches) {
            let branchTopology = new WorkflowTopology(b);
            branchTopology.reporter = this.reporter;
            branchTopology.setRecordId(this.recordId);
            branchTopology.executeState(b.StartAt, data);
        }
    }
    doChoice(state, data) {
        console.log('***** doChoice *****');
        let hit = false;
        for (let c of state.Choices) {
            let expression = jsonata(c.Condition);
            if (expression.evaluate(data)) {
                hit = true;
                this.executeState(c.Next, data);
            }
            if (hit)
                break;
        }
        if (!hit) {
            if (state.Default !== undefined)
                this.executeState(state.Default, data);
            else {
                // report error to cloud
            }
        }
    }
    doSucceed() {
        console.log('***** doSucceed *****');
        // report succeed to cloud
        console.log('succeed');
    }
    doFail(state) {
        console.log('***** doFail *****');
        // report fail to cloud
        console.log('fail');
    }
    doWait(state, data) { }
    doPass(state, data) { }
}

class ResponseWriter {
    constructor(response, isWorkflow) {
        this.isWorkflow = isWorkflow
        if (isWorkflow) {
            response.writeHead(200, { 'Content-Type': 'application/json' });
            response.write(JSON.stringify({ status: 'success', info: 'pushed into working queue' }));
            response.end();
        }
        else
            this.response = response;
    }
    setRecordId(recordId) {
        if (recordId == null)
            this.recordId = crypto.randomBytes(16).toString('hex');
        else
            this.recordId = recordId;
    }
    setRole(role) {
        this.role = role;
    }
    setWorkflow(workflowTopology) {
        workflowTopology.setRecordId(this.recordId);
        this.workflowTopology = workflowTopology;
        workflowTopology.reporter = (_role, _status, _info = '') => {
            let info = { role: _role, status: _status, ip: fogIP, info: _info };
            client.rpush(`workflow_record_${this.recordId}`, JSON.stringify(info));
        };
        this.workflowTopology.reporter(this.role, 'running');
    }
    writeHead(code, headers) {
        if (!this.isWorkflow)
            this.response.writeHead(code, headers);
    }
    write(data) {
        if (this.isWorkflow) {
            this.workflowTopology.reporter(this.role, 'succeed', data);
            data = JSON.parse(data);
            console.log(data);
            // let state = this.workflowTopology.getState(this.role);
            let state = this.workflowTopology.allStates[this.role];
            if (state.Next !== undefined)
                this.workflowTopology.executeState(state.Next, data);
        }
        else
            this.response.write(JSON.stringify({ status: 'success', data: data }));
    }
    writeError(data) {
        if (this.isWorkflow) {
            console.error(data);
            this.workflowTopology.reporter(this.role, 'fail', data);
            // and process catch statement
        }
        else
            this.response.write(JSON.stringify({ status: 'fail', data: data }));
    }
    end() {
        if (this.isWorkflow) {
            // this.request.end();
        }
        else
            this.response.end();
    }
}

module.exports = {
    ResponseWriter: ResponseWriter,
    WorkflowTopology: WorkflowTopology
};
