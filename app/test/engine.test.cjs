const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs/promises'),os=require('node:os'),path=require('node:path');const {Engine}=require('../electron/engine.cjs');const runtime=require('../runtime.json');
const fixture=name=>path.resolve(__dirname,'../../fixtures',name+'.step');
const setup=async e=>{const doAction=(n,a={})=>e.action(n,{expectedVersion:e.project.version,...a});await doAction('set_mesh_recipe',{globalSize:4});await doAction('generate_mesh');await doAction('set_material',{E:210000,nu:.3});await doAction('set_support',{id:'fixed',faceId:'f1',dofs:[1,2,3],values:[0,0,0]});await doAction('set_load',{id:'force',faceId:'f2',type:'force',vector:[1000,0,0]});return doAction;};
test('Real worker: revisions, stale writes, bounded failure, restored mesh, export integrity, save/reopen',{timeout:30000},async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'mesh-test-')),e=new Engine({runtime,root});
 try{
  await e.create(fixture('axial-bar'),root+'/bar');const act=await setup(e);const first=e.project.selectedRevision;
  const version=e.project.version;await act('set_load',{id:'force',faceId:'f2',type:'force',vector:[750,0,0]});
  await assert.rejects(()=>e.action('set_material',{expectedVersion:version,E:123,nu:.3}),/Stale project version/);assert.equal(e.project.setup.material.E,210000);
  await act('set_mesh_recipe',{globalSize:4,local:[{faceId:'f2',size:2,distance:8}]});await act('generate_mesh');assert.notEqual(e.project.selectedRevision,first);assert.equal(e.project.setup.loads[0].vector[0],750);
  const out=await act('export_inp',{mode:'analysis',filename:'ready.inp'});assert.ok(out.passed);assert.equal(out.totalForceN[0],750);assert.equal(out.fileCheck.rigidBodyRestraintRank,6);
  const accepted=e.project.selectedRevision;await act('set_mesh_recipe',{globalSize:.02});await assert.rejects(()=>act('generate_mesh'),/budget/);assert.equal(e.project.selectedRevision,accepted);assert.equal(e.project.revisions.length,2);
  await assert.rejects(()=>act('export_inp',{mode:'analysis',filename:'bad.inp'}),/settings changed/);
  await act('select_revision',{id:first});assert.equal(e.project.setup.loads[0].vector[0],750);
  const reopened=new Engine({runtime,root});await reopened.open(root+'/bar');assert.equal(reopened.project.selectedRevision,first);assert.equal(reopened.project.setup.loads[0].vector[0],750);assert.deepEqual(reopened.project.geometry.faces,e.project.geometry.faces);assert.ok((await reopened.scene()).nodes.length);
  const mesh=await reopened.meshFile();await fs.appendFile(mesh,' ');await assert.rejects(()=>reopened.scene(),/changed on disk/);reopened.close();
 }finally{e.close();await fs.rm(root,{recursive:true,force:true});}
});
test('Missing setup exports mesh only, underconstraint fails and incorrect references cannot write',{timeout:20000},async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'mesh-test-')),e=new Engine({runtime,root});try{
  await e.create(fixture('axial-bar'),root+'/bar');const act=(n,a={})=>e.action(n,{expectedVersion:e.project.version,...a});await act('set_mesh_recipe',{globalSize:5});await act('generate_mesh');
  assert.ok((await act('export_inp',{mode:'mesh',filename:'mesh.inp'})).passed);
  await assert.rejects(()=>act('export_inp',{mode:'analysis',filename:'full.inp'}),/Define/);
  await assert.rejects(()=>act('set_support',{id:'fixed',faceId:'f99',dofs:[1,2,3],values:[0,0,0]}),/Unknown CAD face/);
  await assert.rejects(()=>act('export_inp',{mode:'mesh',filename:'../escape.inp'}),/basename/);
  await act('select_region',{selector:'xmin'});assert.equal(e.project.selectedFace,'f1');await act('name_region',{faceId:'f1',name:'Mounting face'});await act('select_region',{selector:'Mounting face'});assert.equal(e.project.selectedFace,'f1');
  const saved=await fs.readFile(root+'/bar/project.json','utf8');e.agentBusy=true;await assert.rejects(()=>e.newProject(),/Stop/);e.agentBusy=false;assert.equal(e.project.selectedFace,'f1');await e.newProject();assert.equal(e.snapshot().project,null);assert.equal(await e.scene(),null);assert.equal(await fs.readFile(root+'/bar/project.json','utf8'),saved);await e.open(root+'/bar');assert.equal(e.project.selectedFace,'f1');assert.ok((await e.scene()).nodes.length);
 }finally{e.close();await fs.rm(root,{recursive:true,force:true});}
});
test('Cancellation interrupts the real worker and preserves accepted mesh',{timeout:30000},async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'mesh-cancel-')),e=new Engine({runtime,root});try{
  await e.create(fixture('holed-plate'),root+'/part');const act=(n,a={})=>e.action(n,{expectedVersion:e.project.version,...a});await act('set_mesh_recipe',{globalSize:4});await act('generate_mesh');const accepted=e.project.selectedRevision;
  await act('set_mesh_recipe',{globalSize:1.4});const job=act('generate_mesh');const rejected=assert.rejects(()=>job,/Cancelled/);
  for(let i=0;i<100&&!e.child;i++)await new Promise(r=>setTimeout(r,5));assert.ok(e.child,'Actual worker process started');await e.cancel();await rejected;assert.equal(e.project.selectedRevision,accepted);assert.equal(e.project.revisions.length,1);assert.equal(e.workerBusy,false);
 }finally{e.close();await fs.rm(root,{recursive:true,force:true});}
});
