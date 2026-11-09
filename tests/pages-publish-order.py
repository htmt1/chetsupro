import importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('wait',Path(__file__).parents[1]/'scripts/wait-for-legacy-pages.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def check(states,expected,timeout=240):
    now=[0];calls=[0]
    def fetch():
        i=min(calls[0],len(states)-1);calls[0]+=1;return states[i]
    def sleep(n):now[0]+=n
    try:result=m.wait_for_branch_build(fetch,1,sleep,lambda:now[0],timeout)
    except RuntimeError:result='timeout'
    assert result==expected,(result,expected)
    return calls[0]
self_run={'id':1,'path':'.github/workflows/pages.yml','status':'in_progress'}
branch=lambda status:{'id':2,'path':'dynamic/pages/pages-build-deployment','status':status,'event':'dynamic'}
assert check([[self_run]],'not-configured')==3
assert check([[self_run],[branch('queued')],[branch('in_progress')],[branch('completed')]],'finished')==4
check([[branch('in_progress')]],'timeout',11)
print('PASS deployment ordering: self-run excluded, dynamic build awaited, absent build and timeout handled')
