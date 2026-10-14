# BSMP model check — compare the customer's 3D model to ours in SolidWorks.
#
# Runs against the SolidWorks session already open on this PC (COM). It never saves or
# changes a document: the two solids are COPIED in memory, the customer copy is turned
# and shifted onto ours, then each copy is subtracted from the other. Whatever is left
# is a real difference: material only in our model, or only in theirs.
#
#   alignment  best of the 24 proper axis rotations (a mirror image is a real
#              difference, so reflections are never tried), scored by matching hole
#              centres; then the shift comes from the big flat faces, one axis at a
#              time. Hole centres are too sloppy for the shift on imported models
#              (split faces) — on the first test that left a .003" skin = 1.36 in3 of
#              false difference.
#   findings   leftover pieces grouped by shape, so 4 identical tabs read as one row
#              "4x". Hairline pieces (volume < MINVOL, or average thickness < THIN_AVG)
#              are counted but not listed — a .001 bend-radius difference makes
#              hundreds of them.
#   labels     suggestions only, the user signs every row off:
#              masking  = a pad <= .010 thick that only the customer has (paint masking)
#              turret   = customer material sitting inside one of OUR holes (a half
#                         shear / form they model and we cut as a hole)
#
# Owner-confirmed on Absolute 11207-001 (2026-10-14): tabs + flange reliefs = his
# flattening clearances, the .005 disc = paint masking, the 9 hole plugs = half shears.
import os, math, base64, tempfile, itertools, collections
import pythoncom, win32com.client
from win32com.client import gencache, VARIANT

IN = 39.37007874          # metres -> inches
MINVOL = 0.0002           # in3: smaller leftover pieces are slivers
THIN_AVG = 0.004          # in: average thickness (2V/A) below this = a skin, not a feature
MASK_THK = 0.010          # in: thinner customer-only pads are paint masking

_mod = None
def sw_app():
    global _mod
    pythoncom.CoInitialize()
    _mod = _mod or gencache.EnsureModule('{83A33D31-27C5-11CE-BFD4-00400513BB57}', 0, 30, 0)
    try:
        raw = win32com.client.GetActiveObject('SldWorks.Application')
    except Exception:
        raise RuntimeError('SolidWorks is not running on this PC - open SolidWorks and try again.')
    return _mod, _mod.ISldWorks(raw._oleobj_)

def open_parts():
    mod, sw = sw_app()
    out = []
    for d in (sw.GetDocuments() or []):
        m = mod.IModelDoc2(d._oleobj_)
        if m.GetType() == 1:   # part
            out.append({'title': m.GetTitle(), 'path': m.GetPathName()})
    return out

def _open(mod, sw, path):
    """-> (IModelDoc2, opened_by_us). A document already open is used as is and never closed."""
    d = sw.GetOpenDocumentByName(path)
    if d: return mod.IModelDoc2(d._oleobj_), False
    ext = os.path.splitext(path)[1].lower()
    if ext == '.sldprt':
        e = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0); w = VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
        d = sw.OpenDoc6(path, 1, 1 | 2, '', e, w)          # part, silent + read-only
    else:                                                  # STEP / IGES / Parasolid / ...
        r = sw.LoadFile4(path, '', sw.GetImportFileData(path), 0)
        d = r[0] if isinstance(r, tuple) else r
    if not d: raise RuntimeError('SolidWorks could not open ' + os.path.basename(path))
    return mod.IModelDoc2(d._oleobj_), True

def save_upload(name, b64, prefix):
    """an uploaded file -> a temp copy. The prefix keeps it from clashing with a document of
    the same name that is already open (SolidWorks refuses two documents with one name)."""
    folder = os.path.join(tempfile.gettempdir(), 'bsmp-modelcheck'); os.makedirs(folder, exist_ok=True)
    safe = ''.join(c if c.isalnum() or c in '._-' else '_' for c in os.path.basename(name or 'model'))
    p = os.path.join(folder, prefix + safe)
    with open(p, 'wb') as f: f.write(base64.b64decode(b64))
    return p

def _solid(mod, m):
    bodies = mod.IPartDoc(m._oleobj_).GetBodies2(0, True) or []
    if not bodies: raise RuntimeError(m.GetTitle() + ' has no solid body.')
    if len(bodies) > 1:
        # several bodies (multibody part, or a STEP of an assembly) -> join them
        b = mod.IBody2(bodies[0].Copy()._oleobj_)
        for x in bodies[1:]:
            rr = b.Operations2(15903, mod.IBody2(x.Copy()._oleobj_)); r = rr[0] if isinstance(rr, tuple) else rr
            if r: b = mod.IBody2(r[0]._oleobj_)
        return b, len(bodies)
    return mod.IBody2(bodies[0]._oleobj_), 1

def _fingerprint(mod, m, b):
    mp = b.GetMassProperties(1.0)                # [cx,cy,cz, vol, area, mass, ...] SI
    box = b.GetBodyBox()
    size = [(box[i+3]-box[i])*IN for i in range(3)]
    return {'title': m.GetTitle(), 'volume': mp[3]*IN**3, 'area': mp[4]*IN**2,
            'size': [round(v, 4) for v in size], 'config': m.ConfigurationManager.ActiveConfiguration.Name}

def _holes(mod, b):
    """unique hole axes: short cylinders (through the sheet), as (dia, centre)"""
    out = {}
    for fc in b.GetFaces():
        f = mod.IFace2(fc._oleobj_); s = mod.ISurface(f.GetSurface()._oleobj_)
        if not s.IsCylinder(): continue
        p = s.CylinderParams; ax = p[3:6]; r = p[6]
        fb = f.GetBox(); ext = [(fb[i+3]-fb[i]) for i in range(3)]
        if abs(sum(ext[i]*abs(ax[i]) for i in range(3)))*IN > 0.2: continue     # a bend, not a hole
        mid = [(fb[i]+fb[i+3])/2 for i in range(3)]
        o = p[0:3]; t = sum((mid[i]-o[i])*ax[i] for i in range(3)); c = [o[i]+t*ax[i] for i in range(3)]
        key = (round(2*r*IN, 3),) + tuple(round(v*IN, 2) for v in c)
        out[key] = (2*r*IN, [v*IN for v in c], [abs(a) for a in ax])
    return list(out.values())

def _rotations():
    rs = []
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1, -1), repeat=3):
            R = [[0]*3 for _ in range(3)]
            for i in range(3): R[i][perm[i]] = signs[i]
            det = (R[0][0]*(R[1][1]*R[2][2]-R[1][2]*R[2][1]) - R[0][1]*(R[1][0]*R[2][2]-R[1][2]*R[2][0])
                   + R[0][2]*(R[1][0]*R[2][1]-R[1][1]*R[2][0]))
            if det == 1: rs.append(R)
    return rs

def _overlap(a, b, g):
    return all(a[i] - g <= b[i+3] and b[i] - g <= a[i+3] for i in range(3))

def _apply(R, t, p): return [sum(R[i][j]*p[j] for j in range(3)) + t[i] for i in range(3)]

def _big_planes(mod, b):
    out = []
    for fc in b.GetFaces():
        f = mod.IFace2(fc._oleobj_); s = mod.ISurface(f.GetSurface()._oleobj_)
        if not s.IsPlane(): continue
        n = list(f.Normal); k = max(range(3), key=lambda i: abs(n[i]))
        if abs(n[k]) < 0.999: continue
        fb = f.GetBox(); out.append((k, 1 if n[k] > 0 else -1, f.GetArea()*IN*IN, fb[k]*IN))
    return out

def _xform(mod, sw, R, t):
    mu = mod.IMathUtility(sw.GetMathUtility()._oleobj_)
    arr = [R[0][0], R[1][0], R[2][0], R[0][1], R[1][1], R[2][1], R[0][2], R[1][2], R[2][2],
           t[0]/IN, t[1]/IN, t[2]/IN, 1.0, 0, 0, 0]
    return mu.CreateTransform(VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, arr))

def _cut(mod, a, b):
    rr = mod.IBody2(a.Copy()._oleobj_).Operations2(15902, mod.IBody2(b.Copy()._oleobj_))
    r = rr[0] if isinstance(rr, tuple) else rr
    return [mod.IBody2(x._oleobj_) for x in (r or [])]

def compare(ours_path, theirs_path, pictures=True):
    mod, sw = sw_app()
    mo, oo = _open(mod, sw, ours_path)
    mt, ot = _open(mod, sw, theirs_path)
    try:
        bo, nbo = _solid(mod, mo); bt, nbt = _solid(mod, mt)
        fo, ft = _fingerprint(mod, mo, bo), _fingerprint(mod, mt, bt)
        fo['bodies'], ft['bodies'] = nbo, nbt
        ho, ht = _holes(mod, bo), _holes(mod, bt)
        xo = bo.GetBodyBox(); xt = bt.GetBodyBox()
        co = [(xo[i]+xo[i+3])/2*IN for i in range(3)]; ct = [(xt[i]+xt[i+3])/2*IN for i in range(3)]
        so = sorted(fo['size']); st = sorted(ft['size'])
        best = None
        for R in _rotations():
            # the turned box must match ours (within .1") before hole scoring is worth doing
            rs = [abs(sum(R[i][j]*(xt[j+3]-xt[j]) for j in range(3)))*IN for i in range(3)]
            if any(abs(rs[i]-fo['size'][i]) > 0.1 for i in range(3)): continue
            rc = _apply(R, [0, 0, 0], ct); t = [co[i]-rc[i] for i in range(3)]
            score = 0
            for dia, c, _ in ht:
                q = _apply(R, t, c)
                cand = [math.dist(q, c2) for d2, c2, _ in ho if abs(d2-dia) < 0.01]
                score += min(min(cand) if cand else 1.0, 1.0)
            if best is None or score < best[0]: best = (score, R, t)
        if best is None:
            raise RuntimeError('The two models are not the same size in any orientation (yours %s, theirs %s) - wrong file?'
                               % (' x '.join('%.3f' % v for v in fo['size']), ' x '.join('%.3f' % v for v in ft['size'])))
        _, R, t = best
        moved = mod.IBody2(bt.Copy()._oleobj_); moved.ApplyTransform(_xform(mod, sw, R, t))
        po, pt = _big_planes(mod, bo), _big_planes(mod, moved)
        adj = [0.0, 0.0, 0.0]; plane_deltas = []
        for k in range(3):
            ds = []
            for (kk, sg, area, pos) in sorted([p for p in po if p[0] == k], key=lambda p: -p[2])[:6]:
                c = [q for q in pt if q[0] == k and q[1] == sg and abs(q[2]-area) < 0.02*area]
                if c:
                    q = min(c, key=lambda q: abs(q[3]-pos))
                    if abs(q[3]-pos) < 0.02: ds.append(pos - q[3])
            if ds: ds.sort(); adj[k] = ds[len(ds)//2]
            plane_deltas.append([round(d, 5) for d in ds])
        if any(abs(a) > 1e-7 for a in adj):
            moved.ApplyTransform(_xform(mod, sw, [[1, 0, 0], [0, 1, 0], [0, 0, 1]], adj))
            t = [t[i]+adj[i] for i in range(3)]
        # ---- subtract both ways ----
        findings = []; slivers = {'ours': [0, 0.0], 'theirs': [0, 0.0]}; real_vol = {'ours': 0.0, 'theirs': 0.0}
        keep_bodies = {'ours': [], 'theirs': []}
        for side, A, B in (('ours', bo, moved), ('theirs', moved, bo)):
            pieces = []
            for x in _cut(mod, A, B):
                mp = x.GetMassProperties(1.0); v = mp[3]*IN**3; a = mp[4]*IN**2
                bb = x.GetBodyBox(); sz = [(bb[i+3]-bb[i])*IN for i in range(3)]
                avg = 2*v/a if a > 0 else 0
                if v < MINVOL or avg < THIN_AVG:
                    slivers[side][0] += 1; slivers[side][1] += v; continue
                real_vol[side] += v
                pieces.append({'vol': v, 'c': [mp[i]*IN for i in range(3)], 'size': sz, 'avg': avg,
                               'box': [bb[i]*IN for i in range(6)]})
                keep_bodies[side].append(x)
            groups = collections.OrderedDict()
            for p in sorted(pieces, key=lambda p: -p['vol']):
                k = (round(p['vol'], 4), tuple(round(s, 2) for s in sorted(p['size'])))
                groups.setdefault(k, []).append(p)
            for (v, _), ps in groups.items():
                f = {'side': side, 'count': len(ps), 'vol': round(ps[0]['vol'], 5), 'size': [round(s, 3) for s in ps[0]['size']],
                     'avgThk': round(ps[0]['avg'], 4), 'at': [[round(c, 3) for c in p['c']] for p in ps],
                     'boxes': [[round(c, 3) for c in p['box']] for p in ps]}
                thin = min(ps[0]['size'])
                if side == 'theirs' and thin <= MASK_THK:
                    f['suggest'] = 'masking'
                    f['why'] = 'only %.3f" thick, only on the customer model' % thin
                elif side == 'theirs':
                    inside = 0
                    for p in ps:
                        for dia, c, ax in ho:
                            # distance from the piece centre to our hole axis
                            d = [p['c'][i]-c[i] for i in range(3)]; along = sum(d[i]*ax[i] for i in range(3))
                            radial = math.sqrt(max(sum(x*x for x in d) - along*along, 0))
                            if radial < dia/2 and max(p['size']) <= dia + 0.03: inside += 1; break
                    if inside == len(ps):
                        f['suggest'] = 'turret'
                        f['why'] = 'customer material inside %d of your holes' % inside
                findings.append(f)
        # pair "ours-only" with "theirs-only" pieces at the same spots = one feature, different shape
        used = set()
        for i, a in enumerate(findings):
            if a['side'] != 'ours' or i in used: continue
            for j, b in enumerate(findings):
                if b['side'] != 'theirs' or j in used or b['count'] != a['count'] or b.get('suggest'): continue
                # same spot = their boxes overlap (grown by .05"); a changed cutout leaves a ring on
                # each side whose centres can sit an inch apart, so centre distance alone misses it
                if all(any(_overlap(p, q, 0.05) for q in b['boxes']) for p in a['boxes']):
                    a['pair'] = j; used.add(j); b['pairedWith'] = i; break
        out = {'ours': fo, 'theirs': ft, 'rotation': R, 'shift': [round(v, 5) for v in t], 'planeDeltas': plane_deltas,
               'holesOurs': len(ho), 'holesTheirs': len(ht), 'findings': findings,
               'slivers': {k: {'count': v[0], 'vol': round(v[1], 5)} for k, v in slivers.items()},
               'diffVol': {k: round(v, 5) for k, v in real_vol.items()},
               'limits': {'minVol': MINVOL, 'thinAvg': THIN_AVG, 'maskThk': MASK_THK}}
        if pictures: out['pictures'] = _pictures(mod, sw, bo, keep_bodies)
        return out
    finally:
        if ot: sw.CloseDoc(mt.GetTitle())
        if oo: sw.CloseDoc(mo.GetTitle())

def _pictures(mod, sw, bo, keep):
    """our part in grey, red = only in ours, blue = only in theirs. Drawn in a throwaway part
    document (never in the user's own windows), saved as JPG, document closed unsaved."""
    nd = sw.NewDocument(sw.GetUserPreferenceStringValue(8), 0, 0, 0)
    if not nd: return {}
    pm = mod.IModelDoc2(nd._oleobj_); title = pm.GetTitle(); pics = {}
    rgb = lambda r, g, b: r | (g << 8) | (b << 16)
    try:
        mod.IBody2(bo.Copy()._oleobj_).Display3(pm, rgb(190, 190, 190), 1)
        for x in keep['ours']: x.Display3(pm, rgb(220, 30, 30), 1)
        for x in keep['theirs']: x.Display3(pm, rgb(20, 90, 230), 1)
        folder = os.path.join(tempfile.gettempdir(), 'bsmp-modelcheck'); os.makedirs(folder, exist_ok=True)
        for v, name in ((7, 'iso'), (5, 'top'), (1, 'front')):
            pm.ShowNamedView2('', v); pm.ViewZoomtofit2(); pm.GraphicsRedraw2()
            p = os.path.join(folder, 'pic_%s.jpg' % name)
            pm.Extension.SaveAs(p, 0, 1, None, 0, 0)
            with open(p, 'rb') as f: pics[name] = base64.b64encode(f.read()).decode()
    finally:
        sw.CloseDoc(title)
    return pics

if __name__ == '__main__':
    import sys, json
    r = compare(os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), pictures='--pics' in sys.argv)
    r.pop('pictures', None)
    print(json.dumps(r, indent=1))
