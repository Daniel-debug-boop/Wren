from __future__ import annotations

from datetime import datetime

from sqlalchemy import and_, desc, select
from storage.database import a_session_maker
from storage.wren_pr import WrenPR

from wren.app_server.integrations.service_types import ProviderType
from wren.app_server.utils.logger import wren_logger as logger


class WrenPRStore:
    async def insert_pr(self, pr: WrenPR) -> None:
        """
        Insert a new PR or delete and recreate if repo_id and pr_number already exist.
        """
        async with a_session_maker() as session:
            # Check if PR already exists
            result = await session.execute(
                select(WrenPR).filter(
                    WrenPR.repo_id == pr.repo_id,
                    WrenPR.pr_number == pr.pr_number,
                    WrenPR.provider == pr.provider,
                )
            )
            existing_pr = result.scalars().first()

            if existing_pr:
                # Delete existing PR
                await session.delete(existing_pr)
                await session.flush()

            session.add(pr)
            await session.commit()

    async def increment_process_attempts(self, repo_id: str, pr_number: int) -> bool:
        """
        Increment the process attempts counter for a PR.

        Args:
            repo_id: Repository identifier
            pr_number: Pull request number

        Returns:
            True if PR was found and updated, False otherwise
        """
        async with a_session_maker() as session:
            result = await session.execute(
                select(WrenPR).filter(
                    WrenPR.repo_id == repo_id, WrenPR.pr_number == pr_number
                )
            )
            pr = result.scalars().first()

            if pr:
                pr.process_attempts += 1
                await session.merge(pr)
                await session.commit()
                return True
            return False

    async def update_pr_wren_stats(
        self,
        repo_id: str,
        pr_number: int,
        original_updated_at: datetime,
        wren_helped_author: bool,
        num_wren_commits: int,
        num_wren_review_comments: int,
        num_wren_general_comments: int,
    ) -> bool:
        """
        Update OpenHands statistics for a PR with row-level locking and timestamp validation.

        Args:
            repo_id: Repository identifier
            pr_number: Pull request number
            original_updated_at: Original updated_at timestamp to check for concurrent modifications
            wren_helped_author: Whether OpenHands helped the author (1+ commits)
            num_wren_commits: Number of commits by OpenHands
            num_wren_review_comments: Number of review comments by OpenHands
            num_wren_general_comments: Number of PR comments (not review comments) by OpenHands

        Returns:
            True if PR was found and updated, False if not found or timestamp changed
        """
        async with a_session_maker() as session:
            # Use row-level locking to prevent concurrent modifications
            result = await session.execute(
                select(WrenPR)
                .filter(
                    WrenPR.repo_id == repo_id, WrenPR.pr_number == pr_number
                )
                .with_for_update()
            )
            pr: WrenPR | None = result.scalars().first()

            if not pr:
                # Current PR snapshot is stale
                logger.warning('Did not find PR {pr_number} for repo {repo_id}')
                return False

            # Check if the updated_at timestamp has changed (indicating concurrent modification)
            if pr.updated_at != original_updated_at:
                # Abort transaction - the PR was modified by another process
                await session.rollback()
                return False

            # Update the OpenHands statistics
            pr.wren_helped_author = wren_helped_author
            pr.num_wren_commits = num_wren_commits
            pr.num_wren_review_comments = num_wren_review_comments
            pr.num_wren_general_comments = num_wren_general_comments
            pr.processed = True

            await session.merge(pr)
            await session.commit()
            return True

    async def get_unprocessed_prs(
        self, limit: int = 50, max_retries: int = 3
    ) -> list[WrenPR]:
        """
        Get unprocessed PR entries from the WrenPR table.

        Args:
            limit: Maximum number of PRs to retrieve (default: 50)

        Returns:
            List of WrenPR objects that need processing
        """
        async with a_session_maker() as session:
            result = await session.execute(
                select(WrenPR)
                .filter(
                    and_(
                        ~WrenPR.processed,
                        WrenPR.process_attempts < max_retries,
                        WrenPR.provider == ProviderType.GITHUB.value,
                    )
                )
                .order_by(desc(WrenPR.updated_at))
                .limit(limit)
            )
            unprocessed_prs = list(result.scalars().all())

            return unprocessed_prs

    @classmethod
    def get_instance(cls) -> WrenPRStore:
        """Get an instance of the WrenPRStore."""
        return WrenPRStore()
