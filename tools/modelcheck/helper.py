# BSMP Model Check helper — lets the QC app (in the browser) run a model check in the
# SolidWorks that is open on this PC. Listens on 127.0.0.1 only; the QC page calls it.
#
#   GET  /status  -> {ok, solidworks, version}
#   GET  /parts   -> parts open in SolidWorks [{title, path}]
#   POST /check   {ours:{path} | {name,b64}, theirs:{path} | {name,b64}} -> compare.compare()
#
# Start it with "Start Model Check helper.bat" (or pythonw helper.py). One request at a
# time on purpose: SolidWorks does one thing at a time anyway.
import json, os, sys, traceback, http.server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare

VERSION = 1
PORT = 8767
ORIGINS = ('https://bsmpinc.github.io', 'http://localhost:8123', 'http://127.0.0.1:8123')
LOG = os.path.join(os.environ.get('LOCALAPPDATA', '.'), 'BSMP', 'ModelCheck.log')

def log(msg):
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, 'a', encoding='utf-8') as f:
            import datetime; f.write(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S ') + msg + '\n')
    except Exception: pass

class H(http.server.BaseHTTPRequestHandler):
    def _cors(self):
        o = self.headers.get('Origin', '')
        if o in ORIGINS:
            self.send_header('Access-Control-Allow-Origin', o)
            self.send_header('Vary', 'Origin')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        # Chrome/Brave "private network access": a public page calling localhost needs this
        self.send_header('Access-Control-Allow-Private-Network', 'true')
    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code); self._cors()
        self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def log_message(self, *a): pass
    def do_OPTIONS(self):
        self.send_response(204); self._cors(); self.end_headers()
    def _allowed(self):
        o = self.headers.get('Origin', '')
        if o and o not in ORIGINS:
            self._json(403, {'ok': False, 'error': 'origin not allowed'}); return False
        return True
    def do_GET(self):
        if not self._allowed(): return
        try:
            if self.path.startswith('/status'):
                try: compare.sw_app(); sw = True
                except Exception: sw = False
                return self._json(200, {'ok': True, 'solidworks': sw, 'version': VERSION})
            if self.path.startswith('/parts'):
                return self._json(200, {'ok': True, 'parts': compare.open_parts()})
            self._json(404, {'ok': False, 'error': 'not found'})
        except Exception as e:
            log('GET %s failed: %s' % (self.path, traceback.format_exc()))
            self._json(500, {'ok': False, 'error': str(e)})
    def do_POST(self):
        if not self._allowed(): return
        if not self.path.startswith('/check'): return self._json(404, {'ok': False, 'error': 'not found'})
        try:
            req = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')
            def path_of(side, prefix):
                s = req.get(side) or {}
                if s.get('path'):
                    if not os.path.isfile(s['path']): raise RuntimeError('File not found: ' + s['path'])
                    return s['path']
                if s.get('b64'): return compare.save_upload(s.get('name') or side, s['b64'], prefix)
                raise RuntimeError('No %s model given.' % ('customer' if side == 'theirs' else 'your'))
            ours, theirs = path_of('ours', 'OURS_'), path_of('theirs', 'CUST_')
            log('check: %s  vs  %s' % (ours, theirs))
            res = compare.compare(ours, theirs, pictures=True)
            log('done: %d findings' % len(res.get('findings', [])))
            self._json(200, dict(res, ok=True))
        except Exception as e:
            log('check failed: ' + traceback.format_exc())
            self._json(200, {'ok': False, 'error': str(e)})

if __name__ == '__main__':
    log('helper start v%d on 127.0.0.1:%d' % (VERSION, PORT))
    try:
        http.server.HTTPServer(('127.0.0.1', PORT), H).serve_forever()
    except OSError as e:
        log('could not start (already running?): %s' % e)
