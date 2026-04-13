from .base import KickExecutor


class DesktopWeChatKickExecutor(KickExecutor):
    """
    Placeholder for real desktop WeChat UI automation.
    Review must approve before this is called.
    """

    def kick(self, group_name: str, sender: str) -> None:
        raise NotImplementedError(
            'Desktop WeChat kick flow is not implemented yet. '
            'Planned: open group -> locate member -> open menu -> remove after approval.'
        )
