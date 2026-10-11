from pathlib import Path
import json
from rhino_mcp import Client

with Client() as client:
    script = (Path(__file__).resolve().parents[1] / 'rhino' / 'StartDemo.py').read_text()
    print(json.dumps(client.call('run_python', {'script': script}), ensure_ascii=False))
