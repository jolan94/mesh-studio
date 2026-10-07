const fs=require('node:fs/promises'),path=require('node:path'),os=require('node:os'),crypto=require('node:crypto');
const {spawn,execFile}=require('node:child_process');const {CodexAgent}=require('./agent.cjs');const {tools,instructions}=require('./contract.cjs');
const clone=x=>JSON.parse(JSON.stringify(x));const hash=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const atomic=async(file,v)=>{await fs.writeFile(file+'.tmp',JSON.stringify(v,null,2));await fs.rename(file+'.tmp',file);};
const kill=child=>{if(child?.pid&&child.exitCode===null){try{process.kill(-child.pid,'SIGTERM');}catch{child.kill('SIGTERM');}const t=setTimeout(()=>{try{process.kill(-child.pid,'SIGKILL');}catch{}},1000);t.unref();}};
class Engine{
 constructor({runtime,root,onEvent=()=>{}}){this.runtime=runtime;this.root=root;this.onEvent=onEvent;this.status='Ready';this.connected=false;this.workerPath=path.resolve(__dirname,'../python/worker.py').replace(/app\.asar(?=\/)/,'app.asar.unpacked');}
 snapshot(){return clone({project:this.project||null,busy:!!this.workerBusy,agentBusy:!!this.agentBusy,status:this.status,error:this.error||null,connected:this.connected,plan:this.plan||null,stream:this.stream||'',runtime:this.runtime});}
 emit(status){if(status)this.status=status;this.onEvent(this.snapshot());}
 async connect(){this.agent?.close();this.connected=false;this.error=null;this.agent=new CodexAgent(this.runtime,this.root,e=>{if(e.type==='disconnected'){this.connected=false;if(this.agentBusy){this.cancelled=true;kill(this.child);}}if(e.type==='delta')this.stream=(this.stream||'')+e.text;if(e.type==='message')this.stream=e.text;this.emit();},(name,args)=>{if(this.cancelled)throw Error('Cancelled.');return this.action(name,args,'agent');});try{const a=await this.agent.connect();this.connected=true;this.plan=a.plan;this.emit('Codex connected');}catch(e){this.error=e.message;this.emit('Manual workspace ready');}return this.snapshot();}
 async save(){if(this.project)await atomic(path.join(this.project.folder,'project.json'),this.project);}
 async commit(label){this.project.version++;this.project.history.push({time:new Date().toISOString(),label,version:this.project.version});this.project.check=null;this.project.solver=null;await this.save();this.emit(label);return this.context();}
 context(){const p=this.project;if(!p)return{error:'Import STEP to create a project.'};return clone({...p,messages:p.messages.slice(-16),revisions:p.revisions.map(r=>({id:r.id,recipe:r.recipe,report:r.report,time:r.time})),folder:p.folder});}
 revision(){return this.project?.revisions.find(r=>r.id===this.project.selectedRevision);}
 async verify(file,expected){const bytes=await fs.readFile(file);if(hash(bytes)!==expected)throw Error('An accepted artifact changed on disk. Restore its original file.');return bytes;}
 async verifySource(){await this.verify(path.join(this.project.folder,'source.step'),this.project.geometry.sourceHash);}
 async meshFile(){const r=this.revision();if(!r)throw Error('Generate a checked mesh first.');const f=path.join(this.project.folder,'revisions',r.id,'mesh.json');await this.verify(f,r.meshHash);return f;}
 async scene(){if(!this.project)return null;await this.verifySource();const r=this.revision();const file=r?await this.meshFile():path.join(this.project.folder,'geometry','scene.json');if(!r)await this.verify(file,this.project.sceneHash);return JSON.parse(await fs.readFile(file,'utf8'));}
 async newProject(){
  if(this.workerBusy||this.agentBusy||this.actionActive)throw Error('Stop the current operation before starting a new project.');
  await this.save();this.project=null;this.error=null;this.cancelled=false;this.stream='';this.emit('Ready for a new project');return this.snapshot();
 }
 async create(source,folder){
  if(this.workerBusy||this.agentBusy)throw Error('Stop the current operation before changing projects.');
  if(!/\.(step|stp)$/i.test(source))throw Error('Choose a STEP file.');
  await fs.mkdir(folder,{recursive:true});if((await fs.readdir(folder)).length)throw Error('Choose a new empty project folder, or open its existing project.');
  this.cancelled=false;this.error=null;await fs.copyFile(source,path.join(folder,'source.step'));
  let geometry;try{({geometry}=await this.worker({action:'inspect',source:path.join(folder,'source.step'),out:path.join(folder,'geometry')}));}catch(e){this.error=e.message;this.emit('Import failed');throw e;}
  if(this.cancelled)throw Error('Cancelled.');
  this.project={schema:1,version:1,folder,title:path.basename(source).replace(/\.(step|stp)$/i,''),geometry,sceneHash:hash(await fs.readFile(path.join(folder,'geometry','scene.json'))),recipe:{globalSize:Math.max(.1,Number((Math.max(...[0,1,2].map(i=>geometry.bounds[i+3]-geometry.bounds[i]))/12).toPrecision(3))),algorithm:'delaunay',elementType:'C3D10',local:[],unitsConfirmed:geometry.sourceUnit!=='unrecognized'},setup:{material:null,supports:[],loads:[]},selectedFace:null,faceNames:{},revisions:[],selectedRevision:null,messages:[],history:[{time:new Date().toISOString(),label:'Imported STEP',version:1}],exports:[],check:null,solver:null};await this.save();this.emit('Geometry inspected');return this.snapshot();
 }
 async open(folder){
  if(this.workerBusy||this.agentBusy)throw Error('Stop the current operation before changing projects.');
  const p=JSON.parse(await fs.readFile(path.join(folder,'project.json'),'utf8'));
  if(p.schema!==1||!Number.isInteger(p.version)||!Array.isArray(p.revisions)||!Array.isArray(p.messages)||!p.geometry||!p.setup)throw Error('Unsupported Mesh Studio project.');
  for(const r of p.revisions)if(!/^[a-f0-9-]{36}$/.test(r.id)||!/^[a-f0-9]{64}$/.test(r.meshHash))throw Error('Invalid revision manifest.');
  if(p.selectedRevision&&!p.revisions.some(r=>r.id===p.selectedRevision))throw Error('Selected revision is missing.');
  await this.verify(path.join(folder,'source.step'),p.geometry.sourceHash);await this.verify(path.join(folder,'geometry','scene.json'),p.sceneHash);
  for(const r of p.revisions)await this.verify(path.join(folder,'revisions',r.id,'mesh.json'),r.meshHash);
  this.project={...p,folder};this.error=null;this.cancelled=false;this.emit('Project reopened');return this.snapshot();
 }
 assertVersion(a){if(!this.project)throw Error('Import a STEP first.');if(!Number.isInteger(a.expectedVersion)||a.expectedVersion!==this.project.version)throw Error(`Stale project version. Current version is ${this.project.version}; read the project before retrying.`);if(this.workerBusy)throw Error('The geometry worker is running. Wait or stop it first.');}
 face(id){const f=this.project.geometry.faces.find(f=>f.id===id);if(!f)throw Error('Unknown CAD face.');return f;}
 resolve(selector){const direct=this.project.geometry.faces.filter(f=>f.id===selector||(this.project.faceNames[f.id]||f.name).toLowerCase()===selector.toLowerCase());if(direct.length===1)return direct[0];if(direct.length>1)throw Error(`Region name is ambiguous: ${direct.map(f=>f.id).join(', ')}. Select an exact face ID.`);const m=/^([xyz])(min|max)$/.exec(selector.toLowerCase())||/^\b(min|max)[- ]?([xyz])$/.exec(selector.toLowerCase())?.slice().map((x,i,arr)=>i===1?arr[2]:i===2?arr[1]:x);if(!m)throw Error('Select an exact face ID or xmin/xmax/ymin/ymax/zmin/zmax.');const axis='xyz'.indexOf(m[1]);const value=this.project.geometry.bounds[axis+(m[2]==='max'?3:0)];const span=Math.max(...[0,1,2].map(i=>this.project.geometry.bounds[i+3]-this.project.geometry.bounds[i]));const tolerance=Math.max(1e-5,span*1e-7);const matches=this.project.geometry.faces.filter(f=>f.type==='Plane'&&Math.abs(f.center[axis]-value)<tolerance&&Math.abs(f.bounds[axis+3]-f.bounds[axis])<tolerance*2);if(matches.length!==1)throw Error(`Region ${selector} is ambiguous or unavailable. Candidates: ${matches.map(f=>f.id).join(', ')||'none'}. Pick a face.`);return matches[0];}
 async action(name,a={},origin='manual'){
  if(name==='read_project')return this.context();if(this.actionActive)throw Error('Another application action is finishing. Read the project and retry.');this.assertVersion(a);this.actionActive=true;if(origin==='manual')this.cancelled=false;
  this.error=null;const p=this.project;
  try{
   if(name==='select_region'){p.selectedFace=this.resolve(a.selector).id;return await this.commit('Region selected');}
   if(name==='name_region'){this.face(a.faceId);if(typeof a.name!=='string'||!a.name.trim()||a.name.length>80)throw Error('Enter a region name up to 80 characters.');p.faceNames[a.faceId]=a.name.trim();return await this.commit('Region named');}
   if(name==='set_mesh_recipe'){
    if(typeof a.globalSize!=='number'||!Number.isFinite(a.globalSize)||a.globalSize<.02||a.globalSize>10000)throw Error('Global size must be 0.02–10000 mm.');
    if(a.algorithm&&!['delaunay','hxt'].includes(a.algorithm))throw Error('Unsupported algorithm.');
    if(a.local){if(!Array.isArray(a.local)||a.local.length>12)throw Error('At most 12 refinement regions.');for(const r of a.local){this.face(r.faceId);if(!Number.isFinite(r.size)||r.size<.02||r.size>a.globalSize||!Number.isFinite(r.distance)||r.distance<r.size)throw Error('Local sizes and transition distances are invalid.');}}
    const elementType=a.elementType||p.recipe.elementType||'C3D10';if(!['C3D10','C3D8'].includes(elementType))throw Error('Choose C3D10 tetrahedra or C3D8 bricks.');if(elementType==='C3D8'&&(a.local||p.recipe.local).length)throw Error('C3D8 uses a global structured grid. Clear local refinements explicitly before switching.');
    p.recipe={...p.recipe,elementType,globalSize:a.globalSize,...(a.algorithm?{algorithm:a.algorithm}:{}),...(a.local?{local:clone(a.local)}:{}),...(typeof a.unitsConfirmed==='boolean'?{unitsConfirmed:a.unitsConfirmed}:{})};return await this.commit('Mesh settings updated');
   }
   if(name==='set_material'){if(!Number.isFinite(a.E)||a.E<.000001||a.E>1e12||!Number.isFinite(a.nu)||a.nu<-.99||a.nu>=.5)throw Error('Enter finite E > 0 MPa and -0.99 ≤ nu < 0.5.');p.setup.material={name:typeof a.name==='string'?a.name.slice(0,80):'Elastic material',E:a.E,nu:a.nu};return await this.commit('Material updated');}
   if(name==='set_support'||name==='set_load'){
    this.face(a.faceId);if(!/^[A-Za-z][A-Za-z0-9_-]{0,39}$/.test(a.id))throw Error('Use a short item ID starting with a letter.');
    const key=name==='set_support'?'supports':'loads';const other=key==='supports'?'loads':'supports';if(p.setup[other].some(x=>x.id===a.id))throw Error('A load/support already uses that ID.');
    let item;
    if(key==='supports'){if(!Array.isArray(a.dofs)||!a.dofs.length||new Set(a.dofs).size!==a.dofs.length||a.dofs.some(d=>![1,2,3].includes(d))||!Array.isArray(a.values)||a.values.length!==a.dofs.length||a.values.some(v=>!Number.isFinite(v)||Math.abs(v)>1e6))throw Error('Choose translation directions with matching finite displacements.');item={id:a.id,faceId:a.faceId,dofs:a.dofs,values:a.values};}
    else{if(a.type==='force'){if(!Array.isArray(a.vector)||a.vector.length!==3||a.vector.some(v=>!Number.isFinite(v)||Math.abs(v)>1e12))throw Error('Enter [Fx,Fy,Fz] in N.');item={id:a.id,faceId:a.faceId,type:'force',vector:a.vector};}else if(a.type==='pressure'&&Number.isFinite(a.value)&&Math.abs(a.value)<=1e9)item={id:a.id,faceId:a.faceId,type:'pressure',value:a.value};else throw Error('Enter a supported force or pressure.');}
    const i=p.setup[key].findIndex(x=>x.id===a.id);i<0?p.setup[key].push(clone(item)):p.setup[key][i]=clone(item);return await this.commit(key==='supports'?'Support updated':'Load updated');
   }
   if(name==='remove_setup'){for(const key of ['supports','loads'])p.setup[key]=p.setup[key].filter(x=>x.id!==a.id);return await this.commit('Setup item removed');}
   if(name==='inspect_geometry'){
    await this.verifySource();const tmp=await fs.mkdtemp(path.join(os.tmpdir(),'mesh-inspect-'));try{const r=await this.worker({action:'inspect',source:path.join(p.folder,'source.step'),geometry:p.geometry,out:tmp});return{version:p.version,geometry:r.geometry};}finally{await fs.rm(tmp,{recursive:true,force:true});}
   }
   if(name==='generate_mesh'){
    await this.verifySource();const id=crypto.randomUUID(),folder=path.join(p.folder,'revisions',id);await fs.mkdir(folder,{recursive:true});
    try{const r=await this.worker({action:'mesh',source:path.join(p.folder,'source.step'),geometry:p.geometry,recipe:p.recipe,out:folder});if(this.cancelled)throw Error('Cancelled.');p.revisions.push({id,recipe:clone(p.recipe),report:r.report,meshHash:r.meshHash,time:new Date().toISOString()});p.selectedRevision=id;return await this.commit('Mesh checked');}catch(e){await fs.rm(folder,{recursive:true,force:true});throw e;}
   }
   if(name==='select_revision'){const r=p.revisions.find(r=>r.id===a.id);if(!r)throw Error('Unknown mesh revision.');await this.verify(path.join(p.folder,'revisions',r.id,'mesh.json'),r.meshHash);p.selectedRevision=r.id;p.recipe=clone(r.recipe);return await this.commit('Mesh revision restored');}
   if(['check_project','export_inp','check_solver'].includes(name)){
    await this.verifySource();const mesh=await this.meshFile();if(JSON.stringify(p.recipe)!==JSON.stringify(this.revision().recipe))throw Error('Mesh settings changed. Generate a mesh before checking or exporting.');
    const mode=name==='check_solver'?'analysis':a.mode;if(!['mesh','analysis'].includes(mode))throw Error('Choose mesh or analysis export.');const tmp=await fs.mkdtemp(path.join(os.tmpdir(),'mesh-deck-'));
    try{
     const report=await this.worker({action:'export',mesh,setup:p.setup,mode,out:tmp});if(p.solver?.passed&&p.solver.deckHash===report.sha256&&p.solver.version===p.version){report.solver='Balance passed';report.solverCheck=clone(p.solver);}if(this.cancelled)throw Error('Cancelled.');
     p.check={...report,version:p.version,meshRevision:p.selectedRevision};
     if(name==='export_inp'){
      if(typeof a.filename!=='string'||!/^[A-Za-z0-9][A-Za-z0-9_. -]{0,79}\.inp$/.test(a.filename))throw Error('Enter an INP basename up to 80 characters.');
      const dir=path.join(p.folder,'exports');await fs.mkdir(dir,{recursive:true});let filename=a.filename;
      try{await fs.access(path.join(dir,filename));filename=path.basename(filename,'.inp')+'-'+crypto.randomUUID().slice(0,8)+'.inp';}catch(e){if(e.code!=='ENOENT')throw e;}
      const file=path.join(dir,filename);await fs.copyFile(path.join(tmp,'model.inp'),file);await atomic(file+'.report.json',p.check);p.exports.push({path:file,sha256:report.sha256,version:p.version,meshRevision:p.selectedRevision,mode,time:new Date().toISOString()});await this.save();this.emit('INP exported');return{version:p.version,path:file,...report};
     }
     if(name==='check_solver'){
      if(!this.runtime.ccx)throw Error('Choose a CalculiX executable in Runtime settings.');this.emit('Checking with CalculiX');const log=await this.process(this.runtime.ccx,['model'],tmp,90000);await fs.writeFile(path.join(tmp,'solver.log'),log);
      const result=await this.worker({action:'solver_report',mesh,setup:p.setup,export:report,out:tmp});p.solver={...result,version:p.version,meshRevision:p.selectedRevision};const dir=path.join(p.folder,'solver-checks',crypto.randomUUID());await fs.mkdir(path.dirname(dir),{recursive:true});await fs.cp(tmp,dir,{recursive:true});p.solver.folder=dir;p.check.solver='Balance passed';p.check.solverCheck=clone(p.solver);
     }
     await this.save();this.emit(name==='check_solver'?'Solver balance checked':'INP checked');return{version:p.version,check:p.check,solver:p.solver};
    }finally{await fs.rm(tmp,{recursive:true,force:true});}
   }
   throw Error('Unsupported application action.');
  }catch(e){this.error=e.message;this.emit(this.cancelled?'Cancelled':'Action failed');throw e;}finally{this.actionActive=false;}
 }
 async worker(request){await fs.mkdir(request.out,{recursive:true});const file=path.join(request.out,'request.json');await atomic(file,request);this.emit(request.action==='mesh'?'Meshing':request.action==='inspect'?'Inspecting geometry':'Checking INP');const output=await this.process(this.runtime.python,[this.workerPath,file],request.out,120000);let r;try{r=JSON.parse(output.trim().split('\n').at(-1));}catch{throw Error('Worker returned no structured result.');}if(!r.ok)throw Error(r.error||'Worker failed.');return r.result;}
 async process(executable,args,cwd,timeout){
  if(this.workerBusy)throw Error('A worker is already running.');if(this.cancelled)throw Error('Cancelled.');this.workerBusy=true;this.emit();
  try{return await new Promise((resolve,reject)=>{const child=spawn(executable,args,{cwd,detached:true,env:{...process.env,OMP_NUM_THREADS:'1',NUMBER_OF_CPUS:'1',CCX_NPROC_RESULTS:'1',CCX_NPROC_STIFFNESS:'1',CCX_NPROC_EQUATION_SOLVER:'1',PYTHONDONTWRITEBYTECODE:'1'},stdio:['ignore','pipe','pipe']});this.child=child;let stdout='',stderr='',buffer='';let timedOut=false,memoryExceeded=false,peakMiB=0,measuring=false;const monitor=setInterval(()=>{if(measuring||child.exitCode!==null)return;measuring=true;try{execFile('/bin/ps',['-o','rss=','-p',String(child.pid)],{timeout:1000},(err,out)=>{measuring=false;if(err)return;const rss=Number(out.trim())/1024;if(Number.isFinite(rss))peakMiB=Math.max(peakMiB,rss);if(rss>2048){memoryExceeded=true;kill(child);}});}catch{measuring=false;}},500);monitor.unref();const timer=setTimeout(()=>{timedOut=true;kill(child);},timeout);child.stdout.on('data',d=>{stdout=(stdout+d).slice(-100000);buffer+=d;let i;while((i=buffer.indexOf('\n'))>=0){const line=buffer.slice(0,i);buffer=buffer.slice(i+1);try{const e=JSON.parse(line);if(e.event==='stage'&&!this.cancelled)this.emit(e.stage);}catch{}}});child.stderr.on('data',d=>stderr=(stderr+d).slice(-3000));child.once('error',e=>{clearTimeout(timer);clearInterval(monitor);reject(e);});child.once('exit',code=>{clearTimeout(timer);clearInterval(monitor);this.lastPeakMiB=peakMiB;this.child=null;if(memoryExceeded)return reject(Error('Worker exceeded the 2 GiB memory budget. Accepted mesh is preserved.'));if(timedOut)return reject(Error('Worker exceeded its time budget. Accepted mesh is preserved.'));if(this.cancelled)return reject(Error('Cancelled.'));if(code!==0){try{const r=JSON.parse(stdout.trim().split('\n').at(-1));return reject(Error(r.error||'Worker failed.'));}catch{return reject(Error(stderr||`Worker exited ${code}.`));}}resolve(stdout);});});}finally{this.workerBusy=false;this.emit();}
 }
 async chat(text){if(this.agentBusy)throw Error('Codex is already working.');if(!this.project)throw Error('Import STEP first.');if(!this.connected)throw Error('Connect your installed Codex first.');if(typeof text!=='string'||!text.trim()||text.length>12000)throw Error('Enter a request up to 12,000 characters.');this.agentBusy=true;this.cancelled=false;this.error=null;this.stream='';this.project.messages.push({role:'user',text,time:new Date().toISOString()});await this.save();this.emit('Codex working');try{const reply=await this.agent.run(JSON.stringify({request:text,project:this.context()}),instructions,tools);this.project.messages.push({role:'assistant',text:reply,time:new Date().toISOString()});this.emit('Codex finished');}catch(e){this.error=e.message;this.project.messages.push({role:'system',text:e.message,time:new Date().toISOString()});this.emit(this.cancelled?'Cancelled':'Codex needs attention');}finally{this.agentBusy=false;this.stream='';await this.save();this.emit();}return this.snapshot();}
 async cancel(){this.cancelled=true;kill(this.child);await this.agent?.interrupt();this.emit('Stopping');}
 close(){this.cancelled=true;kill(this.child);this.agent?.close();}
}
module.exports={Engine};
