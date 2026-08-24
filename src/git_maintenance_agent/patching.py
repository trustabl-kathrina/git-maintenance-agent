"""Approval-time validation and application of proposed text patches."""

from __future__ import annotations

import re

from .errors import PatchRejectedError
from .models import CommandResult, PatchProposal
from .safety import resolve_safe_path, sha256_file
from .workspace import Workspace

PATCH_PATH = re.compile(r"^(---|\+\+\+) ([ab]/[^\t\n ]+)(?:\t.*)?$", re.MULTILINE)


class PatchApplier:
    """Refuses stale, unsafe, binary, create, or delete operations before Git applies a diff."""

    def prepare(self, workspace: Workspace, proposal: PatchProposal) -> PatchProposal:
        """Attach current content hashes to every touched file."""

        paths = self._target_paths(proposal.unified_diff)
        hashes = {path: sha256_file(resolve_safe_path(workspace.root, path)) for path in paths}
        return proposal.model_copy(update={"target_hashes": hashes})

    def apply(self, workspace: Workspace, proposal: PatchProposal) -> CommandResult:
        """Validate all preconditions, dry-run Git, then atomically apply the candidate diff."""

        paths = self._target_paths(proposal.unified_diff)
        if not proposal.target_hashes:
            raise PatchRejectedError(
                "Patch proposal has no local freshness hashes. Re-run the investigation."
            )
        if set(paths) != set(proposal.target_hashes):
            raise PatchRejectedError("Patch target set changed. Re-run the investigation.")
        for path in paths:
            target = resolve_safe_path(workspace.root, path)
            if sha256_file(target) != proposal.target_hashes[path]:
                raise PatchRejectedError(f"Target changed after investigation: {path}")
        check = workspace.git(
            "apply", "--check", "--whitespace=nowarn", "-", input_text=proposal.unified_diff
        )
        if check.exit_code != 0:
            raise PatchRejectedError(
                f"Git rejected the proposed patch:\n{check.stderr or check.stdout}"
            )
        applied = workspace.git(
            "apply", "--whitespace=nowarn", "-", input_text=proposal.unified_diff
        )
        if applied.exit_code != 0:
            raise PatchRejectedError(
                f"Git failed to apply the patch:\n{applied.stderr or applied.stdout}"
            )
        return applied

    @staticmethod
    def _target_paths(unified_diff: str) -> list[str]:
        if (
            not unified_diff.strip()
            or "/dev/null" in unified_diff
            or "GIT binary patch" in unified_diff
        ):
            raise PatchRejectedError(
                "Only non-empty text patches that modify existing files are supported."
            )
        pairs = PATCH_PATH.findall(unified_diff)
        old_paths = [path[2:] for marker, path in pairs if marker == "---"]
        new_paths = [path[2:] for marker, path in pairs if marker == "+++"]
        if not old_paths or old_paths != new_paths:
            raise PatchRejectedError(
                "Patch must modify existing files with matching a/ and b/ paths."
            )
        return list(dict.fromkeys(new_paths))
