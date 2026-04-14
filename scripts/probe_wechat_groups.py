import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from watcher.windows_wechat import WeChatWindowProbe


def main():
    probe = WeChatWindowProbe()
    names = probe.list_conversation_names()
    print('Conversation candidates:')
    for i, name in enumerate(names, 1):
        print(f'{i}. {name}')


if __name__ == '__main__':
    main()
