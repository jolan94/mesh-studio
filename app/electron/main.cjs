const {app,BrowserWindow,ipcMain,dialog,Menu,shell}=require('electron');const fs=require('node:fs/promises'),path=require('node:path');const {Engine}=require('./engine.cjs');
let window,engine,settings,settingsFile;
if(process.env.MESH_STUDIO_DATA)app.setPath('userData',path.resolve(process.env.MESH_STUDIO_DATA));
const saveSettings=()=>fs.writeFile(settingsFile,JSON.stringify(settings,null,2));
const publish=s=>{if(window&&!window.isDestroyed())window.webContents.send('state',s);};
const register=(channel,fn)=>ipcMain.handle(channel,async(event,...args)=>{if(event.sender!==window.webContents||event.senderFrame!==window.webContents.mainFrame)throw Error('Untrusted application request.');return fn(...args);});
async function remember(){settings.lastProject=engine.project.folder;await saveSettings();return engine.snapshot();}
app.on('window-all-closed',()=>app.quit());app.on('before-quit',()=>engine?.close());
app.whenReady().then(async()=>{
 await fs.mkdir(app.getPath('userData'),{recursive:true});settingsFile=path.join(app.getPath('userData'),'settings.json');
 let runtime={};try{runtime=JSON.parse(await fs.readFile(app.isPackaged?path.join(process.resourcesPath,'runtime.json'):path.resolve(__dirname,'../runtime.json'),'utf8'));}catch{}
 try{settings=JSON.parse(await fs.readFile(settingsFile,'utf8'));}catch{settings={runtime,lastProject:null};}
 app.dock?.setIcon(path.resolve(__dirname,'../assets/icon.png'));
 engine=new Engine({runtime:settings.runtime,root:app.getPath('userData'),onEvent:publish});
window=new BrowserWindow({width:1520,height:1000,minWidth:1100,minHeight:740,title:'Mesh & Load Studio',backgroundColor:'#f3f4f1',titleBarStyle:'hiddenInset',webPreferences:{preload:path.join(__dirname,'preload.cjs'),nodeIntegration:false,contextIsolation:true,sandbox:true}});
window.webContents.setWindowOpenHandler(()=>({action:'deny'}));window.webContents.on('will-navigate',(e,url)=>{if(url!==window.webContents.getURL())e.preventDefault();});
Menu.setApplicationMenu(Menu.buildFromTemplate([{label:'Mesh & Load Studio',submenu:[{role:'about'},{role:'hide'},{role:'quit'}]},{label:'File',submenu:[{label:'New project',accelerator:'CmdOrCtrl+N',click:()=>window.webContents.send('command','new')},{label:'Import STEP…',click:()=>window.webContents.send('command','import')},{label:'Open project…',accelerator:'CmdOrCtrl+O',click:()=>window.webContents.send('command','open')},{label:'Export INP…',accelerator:'CmdOrCtrl+E',click:()=>window.webContents.send('command','export')}]},{role:'editMenu'},{label:'View',submenu:[{role:'reload'},{role:'toggleDevTools'},{role:'togglefullscreen'}]}]));
window=new BrowserWindow({width:1520,height:1000,minWidth:1100,minHeight:740,title:'Mesh Studio',backgroundColor:'#f3f4f1',titleBarStyle:'hiddenInset',webPreferences:{preload:path.join(__dirname,'preload.cjs'),nodeIntegration:false,contextIsolation:true,sandbox:true}});
window.webContents.setWindowOpenHandler(()=>({action:'deny'}));window.webContents.on('will-navigate',(e,url)=>{if(url!==window.webContents.getURL())e.preventDefault();});
Menu.setApplicationMenu(Menu.buildFromTemplate([{label:'Mesh Studio',submenu:[{role:'about'},{role:'hide'},{role:'quit'}]},{label:'File',submenu:[{label:'New project',accelerator:'CmdOrCtrl+N',click:()=>window.webContents.send('command','new')},{label:'Import STEP…',click:()=>window.webContents.send('command','import')},{label:'Open project…',accelerator:'CmdOrCtrl+O',click:()=>window.webContents.send('command','open')},{label:'Export INP…',accelerator:'CmdOrCtrl+E',click:()=>window.webContents.send('command','export')}]},{role:'editMenu'},{label:'View',submenu:[{role:'reload'},{role:'toggleDevTools'},{role:'togglefullscreen'}]}]));
 register('new',async()=>{await engine.newProject();settings.lastProject=null;await saveSettings();return engine.snapshot();});
 register('state',()=>engine.snapshot());register('scene',()=>engine.scene());
 register('import',async()=>{
  if(engine.workerBusy||engine.agentBusy)throw Error('Stop the active operation before importing.');
  const selected=await dialog.showOpenDialog(window,{title:'Import STEP geometry',properties:['openFile'],filters:[{name:'STEP',extensions:['step','stp']}]});if(selected.canceled)return engine.snapshot();
  const folder=await dialog.showSaveDialog(window,{title:'Create a mesh project folder',buttonLabel:'Create project',defaultPath:path.join(app.getPath('documents'),path.basename(selected.filePaths[0]).replace(/\.(step|stp)$/i,'')+'.meshstudio')});if(folder.canceled)return engine.snapshot();
  await engine.create(selected.filePaths[0],folder.filePath);return remember();
 });
 register('sample',async name=>{if(!['axial-bar','cantilever','pressure-block','holed-plate'].includes(name))throw Error('Unknown sample.');const fixture=app.isPackaged?path.join(process.resourcesPath,'fixtures',name+'.step'):path.resolve(__dirname,'../../fixtures',name+'.step');await engine.create(fixture,path.join(app.getPath('userData'),'projects',name+'-'+Date.now()+'.meshstudio'));return remember();});
 register('open',async()=>{const result=await dialog.showOpenDialog(window,{title:'Open mesh project folder',properties:['openDirectory']});if(!result.canceled){await engine.open(result.filePaths[0]);return remember();}return engine.snapshot();});
 register('action',async(name,args)=>{await engine.action(name,args);return engine.snapshot();});register('chat',text=>engine.chat(text));register('cancel',()=>engine.cancel());
 register('connect',()=>{if(engine.workerBusy||engine.agentBusy)throw Error('Stop before reconnecting.');engine.runtime=settings.runtime;return engine.connect();});
 register('runtime',async key=>{if(!['python','codex','node','ccx'].includes(key))throw Error('Unsupported runtime.');if(engine.workerBusy||engine.agentBusy)throw Error('Stop before changing runtime.');const r=await dialog.showOpenDialog(window,{title:'Choose '+key+' executable',properties:['openFile','showHiddenFiles','noResolveAliases'],defaultPath:settings.runtime[key]||app.getPath('home'),showsHiddenFiles:true});if(!r.canceled){settings.runtime[key]=r.filePaths[0];engine.runtime=settings.runtime;await saveSettings();}return engine.snapshot();});
 register('export',async mode=>{
  const report=await engine.action('export_inp',{expectedVersion:engine.project?.version,mode,filename:(engine.project?.title.replace(/[^A-Za-z0-9_-]/g,'-')||'mesh')+'.inp'});
  const r=await dialog.showSaveDialog(window,{title:'Export checked '+mode+' INP',defaultPath:path.basename(report.path),filters:[{name:'CalculiX input',extensions:['inp']}]});if(r.canceled)return{projectPath:report.path,canceled:true};
  const dest=path.resolve(r.filePath),realParent=await fs.realpath(path.dirname(dest));const projectRoot=await fs.realpath(engine.project.folder);if(realParent===projectRoot||realParent.startsWith(projectRoot+path.sep))throw Error('Choose a destination outside the project to protect its accepted artifacts.');
  const bytes=await engine.verify(report.path,report.sha256);await fs.writeFile(dest,bytes);await fs.writeFile(dest+'.report.json',JSON.stringify(report,null,2));return{path:dest,sha256:report.sha256};
 });
 register('reveal',()=>{if(engine.project)shell.showItemInFolder(path.join(engine.project.folder,'project.json'));});
 await window.loadFile(path.resolve(__dirname,'../ui/index.html'));
 if(settings.lastProject){try{await engine.open(settings.lastProject);}catch(e){engine.error=e.message;engine.emit('Could not reopen project');}}
 await engine.connect();
});
