const { spawn } = require('child_process');

let cmd = 'python';
let wrapper = '/data/main.py';
// let wrapper = 'main.py';
let file = '/data/function/main.py';
let handler = 'handler';
let initializer = '';

let workerPool = [];
let idles = [];
let workings = [];

function changeEntry(f, h, i) {
    file = f;
    handler = h;
    initializer = i;
    console.error(f, h, i);
}

function spawnWorker() {
    console.log('spawning... current:', workerPool.length);
    let p;
    // p = spawn(cmd, [wrapper, file, handler]);
    if (initializer === '')
        p = spawn(cmd, [wrapper, file, handler]);
    else
        p = spawn(cmd, [wrapper, file, handler, '--initializer', initializer]);
    p.stdout.on('data', data => {
        if (p.responseWriter !== undefined) {
            console.log('finish');
            p.responseWriter.writeHead(200, {
                'Content-Type': 'application/json'
            });
            p.responseWriter.write(data.toString());
            p.responseWriter.end();
            delete p.responseWriter;
            workings.splice(workings.indexOf(p), 1);
            idles.push(p);
        }
        else if (data.toString() === 'ready' && p.readyCallback !== undefined) {
            console.log('ready');
            p.readyCallback(p);
            delete p.readyCallback;
        }
        else
            console.log('other', data.toString());
        // if (p.resp_cb !== undefined) {
        //     p.resp_cb(data);
        //     delete p.resp_cb;
        // }
    });
    p.stderr.on('data', data => {
        if (p.responseWriter !== undefined) {
            p.responseWriter.writeHead(200, {
                'Content-Type': 'application/json'
            });
            p.responseWriter.writeError(data.toString());
            p.responseWriter.end();
            delete p.responseWriter;
            workings.splice(workings.indexOf(p), 1);
            idles.push(p);
        }
        else {
            idles.splice(workings.indexOf(p), 1);
            workerPool.splice(workerPool.indexOf(p), 1);
        }
        // if (p.resp_cb !== undefined) {
        //     p.resp_cb(JSON.stringify({status: 'fail', info: data.toString()}));
        //     delete p.resp_cb;
        // }
        console.log('error:', data.toString());
    });
    p.on('close', (code, signal) => {
        // if (p.resp_cb !== undefined) {
        //     p.resp_cb(JSON.stringify({status: 'fail'}));
        // }
        console.error('close', code, signal);
        // console.log('close');
        /* search using strict comparison === */
        let index = idles.indexOf(p);
        if (index >= 0)
            idles.splice(index, 1);
        workerPool.splice(workerPool.indexOf(p), 1);
        index = workings.indexOf(p);
        if (index >= 0)
            workings.splice(index, 1);
    });
    p.on('error', err => {
        console.error('error', err);
    });
    p.on('exit', (code, string) => {
        console.error('exit', code, string);
    })
    workerPool.push(p);
    idles.push(p);
}

function getWorker() {
    let isNew = false;
    if (idles.length === 0) {
        spawnWorker();
        isNew = true;
    }

    let index = Math.floor(Math.random() * idles.length);
    let p = idles[index];
    idles.splice(index, 1);
    workings.push(p);
    return { isNew: isNew, worker: p };
}

function idleDeamon() {
    if (workerPool.length < (idles.length - 1) * 2) {
        // let index = Math.floor(Math.random() * idles.length);
        // let p = idles.splice(index, 1);
        // workerPool.splice(workerPool.indexOf(p), 1);
        // p.kill(9);
        idles[Math.floor(Math.random() * idles.length)].kill(9);
        console.log('shutting down one process... current:', workerPool.length);
    }
}

setInterval(idleDeamon, 10000);

module.exports = {
    name: 'Process Control',
    getWorker: getWorker,
    changeEntry: changeEntry
};
