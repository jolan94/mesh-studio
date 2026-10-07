const fs=require('node:fs/promises'),path=require('node:path'),assert=require('node:assert/strict');const {Engine}=require('../electron/engine.cjs');
(async()=>{const root=path.resolve('../pilot-projects/agent-clarify');await fs.mkdir(root,{recursive:true});const e=new Engine({runtime:require('../runtime.json'),root});try{
 await e.create(path.resolve('../fixtures/axial-bar.step'),root+'/bar-'+Date.now()+'.meshstudio');await e.connect();if(!e.connected)throw Error(e.error);
 await e.action('name_region',{expectedVersion:e.project.version,faceId:'f1',name:'Mount'});await e.action('name_region',{expectedVersion:e.project.version,faceId:'f2',name:'Mount'});
 await e.chat('Prepare an analysis INP: mesh at 4 mm, fix the region named Mount, and apply a force at the opposite end.');
 assert.equal(e.project.setup.material,null);assert.equal(e.project.setup.supports.length,0);assert.equal(e.project.setup.loads.length,0);assert.equal(e.project.exports.length,0);
 const reply=e.project.messages.at(-1).text;assert.match(reply,/material|modulus|Young|MPa|Poisson/i);assert.match(reply,/force|load|magnitude/i);assert.match(reply,/Mount|f1|f2|ambig/i);
 await fs.writeFile(path.resolve('../docs/verification/agent-clarification.json'),JSON.stringify({passed:true,project:e.project.folder,setup:e.project.setup,messages:e.project.messages},null,2));console.log(JSON.stringify({passed:true,reply},null,2));
 }finally{e.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
