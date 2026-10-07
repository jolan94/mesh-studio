// Installed Codex owns authentication; no token files or inference API keys.
const {spawn}=require('node:child_process');
const readline=require('node:readline');const path=require('node:path');
class CodexAgent{
 constructor(runtime,cwd,onEvent,execute){this.runtime=runtime;this.cwd=cwd;this.onEvent=onEvent;this.execute=execute;this.pending=new Map();this.sequence=0;}
 send(v){if(this.child?.stdin.writable)this.child.stdin.write(JSON.stringify(v)+'\n');}
 call(method,params,timeout=30000){const id=++this.sequence;return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{this.pending.delete(id);reject(Error(`Codex did not answer ${method}.`));},timeout);this.pending.set(id,{resolve,reject,timer});this.send({id,method,params});});}
 async connect(){
  const PATH=[path.dirname(this.runtime.node||process.execPath),path.dirname(this.runtime.codex),'/opt/homebrew/bin','/usr/local/bin',process.env.PATH].filter(Boolean).join(path.delimiter);
  this.child=spawn(this.runtime.codex,['app-server'],{cwd:this.cwd,env:{...process.env,PATH},stdio:['pipe','pipe','pipe']});
  readline.createInterface({input:this.child.stdout}).on('line',line=>{try{void this.receive(JSON.parse(line));}catch{}});this.child.stderr.on('data',()=>{});
  this.child.on('error',e=>this.fail(e));this.child.on('exit',()=>{this.fail(Error('Codex disconnected. Your project is saved.'));this.onEvent({type:'disconnected'});});
  await this.call('initialize',{clientInfo:{name:'mesh_studio',title:'Mesh Studio',version:'0.1.0'},capabilities:{experimentalApi:true,requestAttestation:false}});this.send({method:'initialized'});
  const {account}=await this.call('account/read',{refreshToken:false});
  if(account?.type!=='chatgpt'){this.close();throw Error('Sign in with ChatGPT using codex login, then reconnect.');}
  return {plan:account.planType||'ChatGPT'};
 }
 async receive(m){
  if(m.id!==undefined&&!m.method){const p=this.pending.get(m.id);if(!p)return;clearTimeout(p.timer);this.pending.delete(m.id);m.error?p.reject(Error(m.error.message)):p.resolve(m.result);return;}
  if(m.id!==undefined&&m.method){
   if(m.method==='item/tool/call'&&this.turn&&m.params.threadId===this.turn.threadId){
    try{const value=await this.execute(m.params.tool,m.params.arguments);this.send({id:m.id,result:{success:true,contentItems:[{type:'inputText',text:JSON.stringify(value)}]}});}
    catch(e){this.send({id:m.id,result:{success:false,contentItems:[{type:'inputText',text:JSON.stringify({error:e.message,needsRead:true})}]}});}return;
   }
   if(m.method==='currentTime/read'){this.send({id:m.id,result:{currentTime:new Date().toISOString()}});return;}
   this.send({id:m.id,error:{code:-32601,message:'Only the supported Mesh Studio tools are available. Ask in the conversation for missing details.'}});return;
  }
  const {method,params:p={}}=m;if(!this.turn||(p.threadId&&p.threadId!==this.turn.threadId))return;
  if(method==='item/agentMessage/delta')this.onEvent({type:'delta',text:p.delta});
  if(method==='item/completed'&&p.item?.type==='agentMessage'){this.turn.text=p.item.text;this.onEvent({type:'message',text:p.item.text});}
  if(method==='turn/started'){this.turn.id=p.turn.id;if(this.cancelled)void this.interrupt();}
  if(method==='turn/completed'){const t=this.turn;this.turn=null;clearTimeout(t.timer);p.turn.status==='completed'?t.resolve(t.text||'Completed.'):t.reject(Error(p.turn.error?.message||(p.turn.status==='interrupted'?'Cancelled.':'Codex request failed.')));}
 }
 async run(prompt,instructions,dynamicTools){
  if(this.turn)throw Error('A Codex request is already running.');this.cancelled=false;
  const {thread}=await this.call('thread/start',{cwd:this.cwd,sandbox:'read-only',approvalPolicy:'never',ephemeral:true,baseInstructions:instructions,dynamicTools,config:{tools:{shell:false},features:{multi_agent:false},model_reasoning_effort:'medium'}});
  if(this.cancelled)throw Error('Cancelled.');
  return new Promise((resolve,reject)=>{const timer=setTimeout(()=>{void this.interrupt();this.fail(Error('Codex request exceeded eight minutes. Your accepted mesh is preserved.'));},480000);this.turn={threadId:thread.id,resolve,reject,text:'',timer};this.call('turn/start',{threadId:thread.id,input:[{type:'text',text:prompt}],effort:'medium'}).then(r=>{if(this.turn){this.turn.id=r.turn.id;if(this.cancelled)void this.interrupt();}}).catch(e=>this.fail(e));});
 }
 async interrupt(){this.cancelled=true;if(this.turn?.id)await this.call('turn/interrupt',{threadId:this.turn.threadId,turnId:this.turn.id}).catch(()=>{});}
 fail(e){for(const p of this.pending.values()){clearTimeout(p.timer);p.reject(e);}this.pending.clear();if(this.turn){clearTimeout(this.turn.timer);this.turn.reject(e);this.turn=null;}}
 close(){this.fail(Error('Cancelled.'));this.child?.kill('SIGTERM');}
}
module.exports={CodexAgent};
