const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs/promises'),os=require('node:os'),path=require('node:path');const {Engine}=require('../electron/engine.cjs');
test('Switching tetra to brick preserves physics and unsupported geometry preserves accepted mesh',{timeout:30000},async()=>{
 const root=await fs.mkdtemp(path.join(os.tmpdir(),'brick-test-')),e=new Engine({runtime:require('../runtime.json'),root});const act=(name,a={})=>e.action(name,{expectedVersion:e.project.version,...a});
 try{
  await e.create(path.resolve('../fixtures/axial-bar.step'),root+'/bar');await act('set_mesh_recipe',{globalSize:4,local:[{faceId:'f2',size:2,distance:8}]});await act('generate_mesh');
  await act('set_material',{E:210000,nu:.3});await act('set_support',{id:'fixed',faceId:'f1',dofs:[1,2,3],values:[0,0,0]});await act('set_load',{id:'force',faceId:'f2',type:'force',vector:[750,0,0]});const physics=JSON.stringify(e.project.setup),old=e.project.selectedRevision;
  await assert.rejects(()=>act('set_mesh_recipe',{globalSize:4,elementType:'C3D8'}),/Clear local/);assert.equal(e.project.recipe.elementType,'C3D10');assert.equal(e.project.selectedRevision,old);
  await act('set_mesh_recipe',{globalSize:4,elementType:'C3D8',local:[]});await act('generate_mesh');assert.equal(e.revision().report.elementType,'C3D8');assert.equal(JSON.stringify(e.project.setup),physics);
  const out=await act('export_inp',{mode:'analysis',filename:'bricks.inp'});assert.equal(out.fileCheck.elementType,'C3D8');assert.equal(out.totalForceN[0],750);
  await act('select_revision',{id:old});assert.equal(e.project.recipe.elementType,'C3D10');assert.equal(JSON.stringify(e.project.setup),physics);
  await e.create(path.resolve('../fixtures/holed-plate.step'),root+'/holed');await act('set_mesh_recipe',{globalSize:4});await act('generate_mesh');const accepted=e.project.selectedRevision;await act('set_mesh_recipe',{globalSize:4,elementType:'C3D8',local:[]});await assert.rejects(()=>act('generate_mesh'),/six planar/);assert.equal(e.project.selectedRevision,accepted);assert.equal(e.project.revisions.length,1);
 }finally{e.close();await fs.rm(root,{recursive:true,force:true});}
});
