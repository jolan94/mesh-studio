const fs=require('node:fs/promises'),path=require('node:path'),assert=require('node:assert/strict');const {Engine}=require('../electron/engine.cjs');
(async()=>{const runtime=require('../runtime.json');const root=path.resolve('../pilot-projects/agent-followup');await fs.mkdir(root,{recursive:true});const e=new Engine({runtime,root,onEvent:s=>{if(s.status!==e.last){e.last=s.status;console.log(s.status);}}});try{
 const oldRoot=path.resolve('../../pilot-projects/agent');const folders=await fs.readdir(oldRoot);const source=path.join(oldRoot,folders.at(-1));const dest=path.join(root,'saved-bar-'+Date.now()+'.meshstudio');await fs.cp(source,dest,{recursive:true});await e.open(dest);await e.connect();if(!e.connected)throw Error(e.error);
 await e.action('set_load',{expectedVersion:e.project.version,id:'pull',faceId:'f2',type:'force',vector:[750,0,0]});
 // Use the existing agent-created load ID; the manual edit must replace its force, not add another.
 const existing=e.project.setup.loads.find(l=>l.id!=='pull');if(existing){await e.action('remove_setup',{expectedVersion:e.project.version,id:'pull'});await e.action('set_load',{expectedVersion:e.project.version,id:existing.id,faceId:'f2',type:'force',vector:[750,0,0]});}
 const initialRevisions=e.project.revisions.length;
 await e.chat('Refine the maximum-X face to 2 mm with an 8 mm transition, keeping the existing global target and every existing material/support/load unchanged. I manually changed the total force to 750 N. Generate the mesh, check with CalculiX and export the exact checked analysis as refined.inp.');
 assert.ok(e.project.revisions.length>initialRevisions);assert.equal(e.project.setup.loads.length,1);assert.equal(e.project.setup.loads[0].vector[0],750);assert.ok(e.project.solver?.passed);assert.ok(e.project.exports.some(x=>x.path.endsWith('refined.inp')));
 const r=e.project.selectedRevision,version=e.project.version;
 await e.chat('Prepare this for nonlinear contact between two parts and automatically improve stress convergence.');
 assert.equal(e.project.selectedRevision,r);assert.equal(e.project.version,version);assert.match(e.project.messages.at(-1).text,/not|unavailable|unsupported|Option 2|cannot/i);
 await fs.writeFile(path.resolve('../docs/verification/agent-results.json'),JSON.stringify({project:e.project.folder,revisions:e.project.revisions.length,setup:e.project.setup,solver:e.project.solver,exports:e.project.exports,messages:e.project.messages},null,2));console.log(JSON.stringify({passed:true,project:e.project.folder,solver:e.project.solver,latestReply:e.project.messages.at(-1).text},null,2));
 }finally{e.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
