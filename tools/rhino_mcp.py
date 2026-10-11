"""Local Rhino MCP router client. Defaults to a read-only context check."""
import json
import selectors
import subprocess
import sys
import time

ROUTER = '/Users/zionw/Library/Application Support/McNeel/Rhinoceros/packages/8.0/Rhino-MCP-Platform/0.3.0/router/osx-arm64/rhino-mcp-router'

class Client:
    def __enter__(self):
        self.process = subprocess.Popen([ROUTER, '--default-version', '8'], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ, 'out')
        self.selector.register(self.process.stderr, selectors.EVENT_READ, 'err')
        self.request_id = 0
        self.request('initialize', {'protocolVersion': '2025-03-26', 'capabilities': {},
                     'clientInfo': {'name': 'NakedEye3D-Test', 'version': '0.1'}})
        self.send({'jsonrpc': '2.0', 'method': 'notifications/initialized', 'params': {}})
        return self

    def send(self, value):
        self.process.stdin.write(json.dumps(value) + '\n')
        self.process.stdin.flush()

    def request(self, method, params):
        self.request_id += 1
        self.send({'jsonrpc': '2.0', 'id': self.request_id, 'method': method, 'params': params})
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            for key, _ in self.selector.select(.2):
                line = key.fileobj.readline()
                if not line:
                    raise RuntimeError('Router closed stream')
                if key.data == 'err':
                    print(line.rstrip(), file=sys.stderr)
                    continue
                value = json.loads(line)
                if value.get('id') == self.request_id:
                    if 'error' in value:
                        raise RuntimeError(value['error'])
                    return value['result']
        raise TimeoutError(method)

    def call(self, name, arguments):
        return self.request('tools/call', {'name': name, 'arguments': arguments})

    def __exit__(self, *args):
        self.process.terminate()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.selector.close()

if __name__ == '__main__':
    with Client() as client:
        if len(sys.argv) > 1 and sys.argv[1] == 'list':
            print(json.dumps(client.request('tools/list', {}), ensure_ascii=False))
        else:
            print(json.dumps(client.call('get_context', {}), ensure_ascii=False))
