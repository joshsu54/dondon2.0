"""Restore pointer files through the repository's public LFS endpoint, verifying every SHA256.
Preserves edited files; does not print temporary signed download URLs or credentials.
"""
import json,re,subprocess,hashlib,urllib.request,time,os,concurrent.futures
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'work/lfs_restore_report.json'
files=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).split(b'\0')
objects={};errors=[]
for raw in set(files):
    if not raw:continue
    p=ROOT/raw.decode('utf-8')
    if not p.is_file() or p.stat().st_size>1024:continue
    data=p.read_bytes();match=re.fullmatch(rb'version https://git-lfs.github.com/spec/v1\r?\noid sha256:([a-f0-9]{64})\r?\nsize (\d+)\r?\n?',data)
    if match:
        oid=match[1].decode();row=objects.setdefault(oid,{'oid':oid,'size':int(match[2]),'paths':[]});row['paths'].append(str(p.relative_to(ROOT)))
report={'status':'running','objects':len(objects),'pointer_files':sum(len(x['paths']) for x in objects.values()),'objects_restored':0,'files_restored':0,'errors':errors}
def save():OUT.write_text(json.dumps(report,indent=2),encoding='utf-8')
def request(url,data=None,headers=None):return urllib.request.urlopen(urllib.request.Request(url,data=data,headers=headers or {}),timeout=60)
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def restore(item):
    oid=item['oid'];cache=ROOT/'.git/lfs/objects'/oid[:2]/oid[2:4]/oid;cache.parent.mkdir(parents=True,exist_ok=True)
    if not cache.exists() or cache.stat().st_size!=item['size'] or digest(cache)!=oid:
        action=item.get('actions',{}).get('download');assert action, 'No download action'
        tmp=cache.with_suffix('.download')
        for attempt in range(3):
            try:
                with request(action['href'],headers=action.get('header',{})) as response,tmp.open('wb') as out:
                    while True:
                        block=response.read(1048576)
                        if not block:break
                        out.write(block)
                assert tmp.stat().st_size==item['size'] and digest(tmp)==oid,'Downloaded content hash mismatch'
                os.replace(tmp,cache);break
            except Exception:
                if attempt==2:raise
                time.sleep(1)
    n=0
    for rel in objects[oid]['paths']:
        p=ROOT/rel
        if p.stat().st_size<1024 and ('oid sha256:'+oid).encode() in p.read_bytes():
            temp=p.with_name(p.name+'.lfs-restoring')
            with cache.open('rb') as source,temp.open('wb') as target:
                for block in iter(lambda:source.read(1048576),b''):target.write(block)
            os.replace(temp,p);n+=1
    return n
save();rows=list(objects.values());downloads=[]
for start in range(0,len(rows),50):
    batch=rows[start:start+50]
    body={'operation':'download','transfers':['basic'],'objects':[{'oid':r['oid'],'size':r['size']} for r in batch]}
    with request('https://github.com/joshsu54/dondon2.0.git/info/lfs/objects/batch',json.dumps(body).encode(),{'Content-Type':'application/vnd.git-lfs+json','Accept':'application/vnd.git-lfs+json'}) as response:data=json.load(response)
    downloads.extend(data['objects'])
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
    futures={pool.submit(restore,item):item['oid'] for item in downloads}
    for f in concurrent.futures.as_completed(futures):
        try:report['files_restored']+=f.result();report['objects_restored']+=1
        except Exception as e:errors.append({'oid':futures[f],'error_type':type(e).__name__})
        save()
        if report['objects_restored']%25==0:print(json.dumps(report),flush=True)
report['status']='passed' if not errors and report['objects_restored']==len(objects) else 'incomplete';save()
print(json.dumps(report),flush=True)
