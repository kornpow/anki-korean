#!/usr/bin/env python3
"""Check gallery interactions with Obscura, driven by Python (no Playwright).

Run: media/.venv/bin/python media/scripts/check_reviewer.py
Override the local executable with OBSCURA_BINARY if needed.
These DOM checks do not replace visual checks in a full browser.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import socket
import time
import websocket

root = Path(__file__).resolve().parents[1]
binary = Path(os.environ.get('OBSCURA_BINARY', root / '.tools/obscura/obscura'))
checks = root / '_research/reviewer-checks'
checks.mkdir(parents=True, exist_ok=True)
from functools import partial
from http.server import ThreadingHTTPServer
import threading
import urllib.request
from serve_review import Handler, COLLECTIONS

script = r"""
(async()=>{
 const get=id=>document.getElementById(id),passed=[];
 const check=(name,test)=>{if(!test)throw Error(name);passed.push(name);};
 const settle=async()=>{for(let n=0;n<100;n++){if(get('save-message').textContent.startsWith('Saved'))return;await new Promise(r=>setTimeout(r,100));}throw Error(get('save-message').textContent);};
 await settle();
 check('10 cards',document.querySelectorAll('.card').length===10);
 check('No feedback export/import controls',!get('export')&&!get('import'));
 document.querySelector('.card .image-button').click();
 get('notes').value='Automatic Korean notes — 한글';get('notes').dispatchEvent(new Event('input'));
 document.querySelector('#review-decisions [data-decision="maybe"]').click();
 await settle();
 const remote=await fetch('/api/reviews?collection=korean-useful-language-10').then(r=>r.json());
 check('Decision saved to server',remote.reviews['88146689'].decision==='maybe');
 check('Korean notes saved to server',remote.reviews['88146689'].notes==='Automatic Korean notes — 한글');
 check('Cropped dialog',get('review').open&&get('large-image').querySelector('.crop-region'));
 get('close').click();
 return JSON.stringify({passed,limitations:['DOM interaction checks; browser layout was checked separately.']});
})()
"""
with tempfile.TemporaryDirectory(prefix='obscura-review-') as storage:
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(root / 'starter-50')))
    server.feedback_dir = Path(storage) / 'feedback'
    server.feedback_dir.mkdir()
    server.manifests = {name: json.loads((root / 'starter-50' / folder / 'manifest.json').read_text()) for name, folder in COLLECTIONS.items()}
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f'http://127.0.0.1:{server.server_port}/sample-10/gallery.html'
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    with (checks / 'obscura-output.txt').open('w') as log:
        process = subprocess.Popen([str(binary), 'serve', '--host', '127.0.0.1',
            '--port', str(port), '--allow-private-network', '--storage-dir', storage],
            stdout=log, stderr=log)
        connection = None
        try:
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                try:
                    connection = websocket.create_connection(f'ws://127.0.0.1:{port}/devtools/browser', timeout=20, suppress_origin=True)
                    break
                except OSError:
                    time.sleep(.1)
            if connection is None:
                raise RuntimeError('Obscura server did not start')
            sequence = 0
            def call(method, params=None, session=None):
                global sequence
                sequence += 1
                message = dict(id=sequence, method=method, params=params or {})
                if session:
                    message['sessionId'] = session
                connection.send(json.dumps(message))
                while True:
                    reply = json.loads(connection.recv())
                    if reply.get('id') == sequence:
                        if 'error' in reply:
                            raise RuntimeError(reply['error'])
                        return reply.get('result', {})
            target = call('Target.createTarget', {'url': 'about:blank'})['targetId']
            session = call('Target.attachToTarget', {'targetId': target, 'flatten': True})['sessionId']
            call('Page.navigate', {'url': url}, session)
            result = call('Runtime.evaluate', {'expression': script, 'awaitPromise': True, 'returnByValue': True}, session)
            if 'exceptionDetails' in result:
                raise RuntimeError(result['exceptionDetails'])
            report = json.loads(result['result']['value'])
            saved_file = server.feedback_dir / 'korean-useful-language-10.json'
            assert json.loads(saved_file.read_text())['reviews']['88146689']['notes'] == 'Automatic Korean notes — 한글'
            report['passed'].append('Feedback durable on disk')
            # The next navigation must restore the server value even without local cache.
            call('Runtime.evaluate', {'expression': 'localStorage.clear()'}, session)
            call('Page.navigate', {'url': url}, session)
            recheck = call('Runtime.evaluate', {'expression': """(async()=>{for(let i=0;i<100;i++){if(document.getElementById('save-message').textContent.startsWith('Saved'))break;await new Promise(r=>setTimeout(r,100));}document.querySelector('.card .image-button').click();return document.getElementById('notes').value;})()""", 'awaitPromise': True, 'returnByValue': True}, session)
            assert recheck['result']['value'] == 'Automatic Korean notes — 한글', recheck
            report['passed'].append('Reload restores server feedback without local cache')
            # Import old browser-only feedback automatically on page load.
            legacy = "localStorage.setItem('korean-useful-language-review-v1',JSON.stringify({'24269980':{decision:'keep',notes:'Previously saved browser review',updated_at:new Date().toISOString()}}))"
            call('Page.addScriptToEvaluateOnNewDocument', {'source': legacy}, session)
            call('Page.navigate', {'url': url}, session)
            migrated = call('Runtime.evaluate', {'expression': """(async()=>{for(let i=0;i<100;i++){if(document.getElementById('save-message').textContent.startsWith('Saved'))break;await new Promise(r=>setTimeout(r,100));}return await fetch('/api/reviews?collection=korean-useful-language-10').then(r=>r.json());})()""", 'awaitPromise': True, 'returnByValue': True}, session)
            assert migrated['result']['value']['reviews']['24269980']['notes'] == 'Previously saved browser review', migrated
            report['passed'].append('Old browser-only reviews migrate automatically')
            report['engine'] = subprocess.check_output([str(binary), '--version'], text=True).strip()
            (checks / 'obscura-results.json').write_text(json.dumps(report, indent=2) + '\n')
            print(json.dumps(report, indent=2))
        finally:
            server.shutdown()
            server.server_close()
            if connection:
                connection.close()
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
