#!/usr/bin/env python3
# run_parallel_agents.py
"""Run multiple Wren agents in parallel with shared Fable memory.

This entrypoint wires up the ParallelAgentOrchestrator with a memory-backed
context manager, spawns several tasks concurrently, and streams granular
events until all tasks complete or a shutdown signal is received.
"""
import asyncio
import logging
import os
import signal
from pathlib import Path
from typing import List

from wren.server.orchestrator import (
    ParallelAgentOrchestrator,
    TaskSpec,
    TaskPriority,
    EventKind,
)
from wren.server.memory.fable_memory import FableMemoryManager

# Ensure structlog or standard logging is configured beautifully
try:
    import structlog

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt='iso'),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ]
    )
    logger = structlog.get_logger(__name__)
except ImportError:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
class Config:
    """Runtime configuration sourced from environment variables."""
    API_KEY: str = os.getenv('LLM_API_KEY', 'your-personal-api-key')
    MODEL_NAME: str = os.getenv('LLM_MODEL', 'deepseek/deepseek-chat')
    # Defaulting to a localized workspace directory, configurable via env
    REPO_PATH: str = os.getenv('WORKSPACE_DIR', str(Path.home() / 'foundry'))
    MAX_CONCURRENT: int = 4
    SHUTDOWN_TIMEOUT_S: int = 30

    def to_dict(self) -> dict:
        """Return the configuration as a plain dictionary."""
        return {
            'API_KEY': self.API_KEY,
            'MODEL_NAME': self.MODEL_NAME,
            'REPO_PATH': self.REPO_PATH,
            'MAX_CONCURRENT': self.MAX_CONCURRENT,
            'SHUTDOWN_TIMEOUT_S': self.SHUTDOWN_TIMEOUT_S,
        }

    def describe(self) -> str:
        """Return a short human-readable summary of the configuration."""
        return (
            f"Config(model={self.MODEL_NAME}, repo={self.REPO_PATH}, "
            f"max_concurrent={self.MAX_CONCURRENT})"
        )


async def event_streamer(
    orchestrator: ParallelAgentOrchestrator, task_ids: List[str]
) -> None:
    """
    Subscribes to the orchestrator's event bus for real-time, granular updates.
    Runs concurrently for all active tasks.
    """
    queues = [await orchestrator.stream(tid) for tid in task_ids]

    async def pipe_events(tid: str, q: asyncio.Queue) -> None:
        while True:
            try:
                event = await q.get()
                if event.kind in (
                    EventKind.COMPLETED,
                    EventKind.FAILED,
                    EventKind.CANCELLED,
                    EventKind.TIMED_OUT,
                ):
                    logger.info(
                        'task.terminated',
                        task_id=tid,
                        kind=event.kind.value,
                        payload=event.payload,
                    )
                    break
                # Only log significant events to prevent terminal spam
                if event.kind not in (EventKind.HEARTBEAT,):
                    logger.info('task.event', task_id=tid, kind=event.kind.value)
            except asyncio.CancelledError:
                break

    await asyncio.gather(*(pipe_events(tid, q) for tid, q in zip(task_ids, queues)))


async def _seed_memory(memory: FableMemoryManager) -> None:
    """Populate the shared memory with baseline preferences and lessons."""
    await memory.set_preference(key='auth', value='JWT-only')
    await memory.set_preference(key='styling', value='TailwindCSS')
    await memory.update_lesson(
        "Always run 'npm install' inside the workspace root before compiling."
    )


def _install_signal_handlers() -> asyncio.Event:
    """Register SIGINT/SIGTERM handlers and return the shutdown event."""
    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    def _trigger_shutdown():
        logger.warning('Shutdown signal received via OS...')
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _trigger_shutdown)

    return shutdown_event


async def execute_runs() -> None:
    """Main execution flow for the memory-backed parallel agents."""
    cfg = Config()

    if cfg.API_KEY == 'your-personal-api-key':
        logger.warning(
            'Using default API key. '
            'Set LLM_API_KEY environment variable for production.'
        )

    # 1. Initialize async persistent memory
    logger.info('Initializing Fable Memory Manager...')
    memory = FableMemoryManager(token_budget=1500)
    await memory.initialize()
    await _seed_memory(memory)

    # 2. Initialize Orchestrator
    orchestrator = ParallelAgentOrchestrator(max_concurrent=cfg.MAX_CONCURRENT)

    # 3. Setup graceful signal handling for Linux native environments
    shutdown_event = _install_signal_handlers()

    try:
        await orchestrator.start()
        logger.info('Orchestrator started successfully.')

        # 4. Dynamically compile memory context (RAG)
        context_1 = await memory.compile_system_instruction(
            context_query='Implement a new login screen component using Tailwind'
        )
        context_2 = await memory.compile_system_instruction(
            context_query='Write comprehensive Jest unit tests for utility helpers'
        )

        # 5. Define structured Task Specifications
        specs = _build_specs(cfg, context_1, context_2)

        # 6. Spawn tasks concurrently
        task_ids = await orchestrator.spawn_many(specs)
        logger.info('Tasks spawned successfully', task_ids=task_ids)

        # 7. Monitor execution
        stream_task = asyncio.create_task(event_streamer(orchestrator, task_ids))
        shutdown_watcher = asyncio.create_task(shutdown_event.wait())

        # Group task waits together so we don't exit when the *first* one finishes
        all_tasks_completed = asyncio.gather(
            *(orchestrator.wait(tid) for tid in task_ids)
        )

        # Wait for either ALL tasks to finish OR a shutdown signal
        await asyncio.wait(
            [all_tasks_completed, shutdown_watcher],
            return_when=asyncio.FIRST_COMPLETED,
        )

        if shutdown_event.is_set():
            logger.warning('Draining orchestrator due to shutdown signal...')
            stream_task.cancel()
            all_tasks_completed.cancel()
            # Suppress CancelledError so cleanup proceeds cleanly
            await asyncio.gather(
                stream_task, all_tasks_completed, return_exceptions=True
            )

        # Fetch final statuses
        for tid in task_ids:
            final_status = await orchestrator.status(tid)
            logger.info(
                'Final task status',
                task_id=tid,
                status=final_status.get('status'),
                cost_usd=final_status.get('cost_usd', 0.0),
            )

    except (RuntimeError, ValueError, asyncio.TimeoutError) as exc:
        logger.error('Fatal execution error', error=str(exc), exc_info=True)
    finally:
        # 8. Guaranteed cleanup
        logger.info('Initiating orchestrator graceful shutdown...')
        await orchestrator.shutdown(drain=True, timeout_s=cfg.SHUTDOWN_TIMEOUT_S)
        logger.info('Execution complete. Goodbye.')


def _build_specs(cfg: Config, context_1: str, context_2: str) -> list:
    """Construct the list of TaskSpec objects for this run."""
    return [
        TaskSpec(
            prompt=(
                f'{context_1}\n\n'
                'Implement a new login screen component using Tailwind.'
            ),
            repo_path=cfg.REPO_PATH,
            api_key=cfg.API_KEY,
            model_name=cfg.MODEL_NAME,
            runtime_cls='memory',
            priority=TaskPriority.HIGH,
            tenant_id='daniboss-1',
            tags=['frontend', 'auth', 'ui'],
            timeout_s=1800.0,
            max_retries=2,
        ),
        TaskSpec(
            prompt=(
                f'{context_2}\n\n'
                'Write comprehensive Jest unit tests for utility helpers.'
            ),
            repo_path=cfg.REPO_PATH,
            api_key=cfg.API_KEY,
            model_name=cfg.MODEL_NAME,
            runtime_cls='memory',
            priority=TaskPriority.NORMAL,
            tenant_id='daniboss-1',
            tags=['testing', 'jest', 'backend'],
            timeout_s=900.0,
            max_retries=3,
        ),
    ]


if __name__ == '__main__':
    try:
        asyncio.run(execute_runs())
    except KeyboardInterrupt:
        print('\nForced exit.')
