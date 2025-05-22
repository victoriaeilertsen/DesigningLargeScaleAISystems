from schemas.a2a_message import A2ATask, A2AMessage
from typing import Dict

class A2AHandler:
    def __init__(self, agents: Dict[str, object]):
        self.agents = agents  # {'dialogue': agent, 'shopping': agent, ...}
        self.tasks: Dict[str, A2ATask] = {}

    def submit_task(self, sender: str, receiver: str, content: str, task_id: str = None) -> A2ATask:
        if task_id and task_id in self.tasks:
            task = self.tasks[task_id]
            # Add new message to existing task
            task.messages.append(A2AMessage(sender=sender, receiver=receiver, content=content, debug={
                'sender': sender,
                'receiver': receiver,
                'agent_used': None,
                'tool_used': None
            }))
            return self.route_task(task)
        else:
            task = A2ATask.create(sender, receiver, content)
            if task_id:
                task.task_id = task_id  # force the use of the provided ID
            # Add debug info to the first message
            task.messages[0].debug = {
                'sender': sender,
                'receiver': receiver,
                'agent_used': None,
                'tool_used': None
            }
            self.tasks[task.task_id] = task
            return self.route_task(task)

    def route_task(self, task: A2ATask) -> A2ATask:
        while True:
            agent = self.agents.get(task.messages[-1].receiver)
            if agent:
                response = agent.process_message(
                    task.messages[-1].content,
                    task.task_id,
                    messages=task.messages
                )
                # Add agent's response to task history
                task.messages.append(
                    A2AMessage(
                        sender=task.messages[-1].receiver,
                        receiver=task.messages[-1].sender,
                        content=response['response'],
                        debug={
                            'sender': task.messages[-1].receiver,
                            'receiver': task.messages[-1].sender,
                            'agent_used': getattr(agent, 'name', str(agent)),
                            'tool_used': response.get('tool_used')
                        }
                    )
                )
                task.status = response.get('status', 'completed')
                # Handle forwarding to another agent
                if response.get('status') == 'forward':
                    forward_to = response.get('forward_to')
                    forward_content = response.get('forward_content')
                    if forward_to and forward_content:
                        # Add forward_content only if it differs from the previous response
                        last_response = task.messages[-1].content if task.messages else None
                        if forward_content != last_response:
                            task.messages.append(
                                A2AMessage(
                                    sender=task.messages[-1].sender,
                                    receiver=forward_to,
                                    content=forward_content,
                                    debug={
                                        'sender': task.messages[-1].sender,
                                        'receiver': forward_to,
                                        'agent_used': getattr(agent, 'name', str(agent)),
                                        'tool_used': response.get('tool_used')
                                    }
                                )
                            )
                        continue  # Forward to the next agent
                break
            else:
                task.status = 'error'
                break
        return task

    def get_task(self, task_id: str) -> A2ATask:
        return self.tasks.get(task_id)
