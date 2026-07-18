"""DEPRECATED: Adapter bridging ParallelAgentOrchestrator into live conversation sessions.

Used by scripts/run_parallel_agents.py only. Will be migrated to
wren.harness or a standalone scripts/ module in a future release.
Do NOT add new imports from this module.
"""

import warnings

warnings.warn(
    'wren.server.conversation_agent is deprecated and will be moved to scripts/. '
    'Use wren.harness for new code.',
    DeprecationWarning,
    stacklevel=2,
)

import asyncio
from typing import Any, Mapping
from uuid import uuid4
from wren.app_server.app_conversation.live_status_app_conversation_service import (
    LiveStatusAppConversationService,
)
from wren.app_server.app_conversation.app_conversation_models import (
    AppConversationStartRequest,
    AppSendMessageRequest,
    AgentType,
    ConversationTrigger,
)


class ConversationAgentAdapter:
    """Bridges ParallelAgentOrchestrator tasks into LiveStatusAppConversationService sessions."""

    def __init__(self, runtime: Any, h: Any, env: Mapping[str, str], orchestrator: Any):
        self.runtime = runtime
        self.h = h
        self.env = env
        self._orchestrator = orchestrator
        self.on_event = None

    async def run_horizon_task(self, prompt: str) -> str:
        # 1. Build the text content block for the initialization message payload
        # Using structured list matching the content requirements
        initial_msg = AppSendMessageRequest(
            role='user', content=[{'type': 'text', 'text': prompt}]
        )

        # 2. Build the standard conversation starter request
        request = AppConversationStartRequest(
            conversation_id=uuid4(),
            initial_message=initial_msg,
            llm_model=self.h.spec.model_name,
            selected_repository=self.h.spec.repo_path,
            agent_type=AgentType.DEFAULT,
            trigger=ConversationTrigger.GUI,
        )

        # 3. Instantiate the execution service context
        service = LiveStatusAppConversationService()

        # 4. Consume the async generator execution steps
        final_task_status = 'completed'
        try:
            async for task_update in service.start_app_conversation(request):
                # Pipe lifecycle status updates directly to our event emitter if wired
                if self.on_event and hasattr(task_update, 'status'):
                    self.on_event('task.progress', {'status': str(task_update.status)})

                # Yield execution thread briefly to avoid blockages
                await asyncio.sleep(0.01)
        except Exception as err:
            final_task_status = f'failed: {str(err)}'
            raise err

        return f'conversation_result: status={final_task_status} id={request.conversation_id}'
