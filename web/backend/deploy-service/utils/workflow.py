import os


def gen_runtime_id():
    return os.urandom(16).hex()


class WorkflowHelper:
    def __init__(self, definition):
        self.definition = definition

    def get_state(self, role):
        return self.definition['States'][role]

    def all_tasks(self):
        tasks = dict()

        def _r(t):
            if tasks.get(t) is not None:
                return
            state = self.get_state(t)
            if state['Type'] == 'Task':
                # tasks[t] = state['Resource']
                tasks[t] = state
                if state.get('Next') is not None:
                    _r(state['Next'])
            elif state['Type'] == 'Choice':
                for i in state['Choices']:
                    _r(i['Next'])
                if state.get('Default') is not None:
                    _r(state['Default'])
            elif state['Type'] == 'Parallel':
                sub_workflows = [WorkflowHelper(d) for d in state['Branches']]
                for sw in sub_workflows:
                    tasks.update(sw.all_tasks())
            else:
                if state.get('Next') is not None:
                    _r(state['Next'])
        _r(self.definition['StartAt'])
        return tasks

    def all_successors(self, role):
        tasks = dict()

        def _r(t):
            if tasks.get(t) is not None:
                return
            state = self.get_state(t)
            if state['Type'] == 'Task':
                tasks[t] = state
            elif state['Type'] == 'Choice':
                for i in state['Choices']:
                    _r(i['Next'])
                if state.get('Default') is not None:
                    _r(state['Default'])
            elif state['Type'] == 'Parallel':
                tasks[t] = state
            else:
                if state.get('Next') is not None:
                    _r(state['Next'])
        state = self.get_state(role)
        if state.get('Next') is not None:
            _r(state['Next'])
        return tasks

    def schedule(self, workflow_runtime_id, schedule_callback, start_ip, function_info_dict):
        # results item: (fog_ip, runtime_id)
        results = dict()
        # runtime_id_table time: (generated_runtime_id, scheduled_runtime_id)
        # ERROR: 这里没有考虑到每个runtime_id的container其目的地是不一样的，简单起见，工作流就不复用了
        runtime_id_table = dict()

        def _r(batch):
            next_batch = []
            # batch item: (state_name, predecessor_ip)
            for t in batch:
                if results.get(t[0]) is not None:
                    continue
                state = self.get_state(t[0])
                if state['Type'] == 'Task':
                    resource = state['Resource']
                    runtime_id = gen_runtime_id()
                    runtime_id_table[t[0]] = [runtime_id, runtime_id]
                    results[t[0]] = schedule_callback(runtime_id, t[1],
                                                      workflow_runtime_id + t[0] +
                                                      function_info_dict[resource]['uri'],
                                                      function_info_dict[resource]['cpu_limit'],
                                                      function_info_dict[resource]['memory_limit'])
                    runtime_id_table[t[0]][1] = results[t[0]][1]
                    successors = self.all_successors(t[0])
                    for k, v in successors.items():
                        if results.get(k) is None:
                            next_batch.append((k, results[t[0]][0]))
                elif state['Type'] == 'Parallel':
                    for b in state['Branches']:
                        sub_workflow = WorkflowHelper(b)
                        sub_results, sub_runtime_table = sub_workflow.schedule(
                            schedule_callback, t[1], function_info_dict)
                        results.update(sub_results)
                        runtime_id_table.update(sub_runtime_table)
                else:
                    raise RuntimeError('invalid state')
            if len(next_batch) > 0:
                _r(next_batch)
        _r([(self.definition['StartAt'], start_ip)])
        return results, runtime_id_table
