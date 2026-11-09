"""Wait for the branch-based Pages build before publishing the application.
Only reads workflow status. It does not modify Pages settings or credentials.
"""
import json,os,time,urllib.parse,urllib.request

def wait_for_branch_build(fetch_runs,current_id,sleep=time.sleep,clock=time.monotonic,timeout=240):
    start=clock();absent=0
    while clock()-start<timeout:
        branch=[r for r in fetch_runs() if int(r['id'])!=int(current_id) and (r.get('path','').startswith('dynamic/pages/') or r.get('name')=='pages build and deployment')]
        if not branch:
            absent+=1
            if absent>=3:return 'not-configured'
        else:
            absent=0
            if all(r.get('status')=='completed' for r in branch):return 'finished'
        sleep(5)
    raise RuntimeError('Branch Pages build has not finished; refusing to race its deployment.')

def main():
    repo=os.environ['GITHUB_REPOSITORY'];sha=os.environ['GITHUB_SHA'];run=os.environ['GITHUB_RUN_ID'];token=os.environ['GH_TOKEN']
    url='https://api.github.com/repos/'+repo+'/actions/runs?'+urllib.parse.urlencode({'head_sha':sha,'per_page':100})
    def fetch():
        req=urllib.request.Request(url,headers={'Accept':'application/vnd.github+json','Authorization':'Bearer '+token,'X-GitHub-Api-Version':'2022-11-28','User-Agent':'chetsupro-pages-publish'})
        with urllib.request.urlopen(req,timeout=30) as response:return json.load(response)['workflow_runs']
    print('Branch Pages build:',wait_for_branch_build(fetch,run))
if __name__=='__main__':main()
