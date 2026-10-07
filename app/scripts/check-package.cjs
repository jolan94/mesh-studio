const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),asar=require('@electron/asar'),assert=require('node:assert/strict');
const appPath=fs.existsSync(path.resolve(__dirname,'../dist/mac-arm64/Mesh Studio.app'))?path.resolve(__dirname,'../dist/mac-arm64/Mesh Studio.app'):path.resolve(__dirname,'../dist/mac-arm64/Mesh & Load Studio.app');
const app=appPath,archive=path.join(app,'Contents/Resources/app.asar'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const exact=['electron/engine.cjs','electron/contract.cjs','electron/agent.cjs','electron/main.cjs','electron/preload.cjs','ui/index.html','ui/app.js','ui/message-format.mjs','ui/style.css','ui/viewport.js','ui/vendor/OrbitControls.js','ui/vendor/THREE_LICENSE','python/kernel.py','python/bricks.py','python/solver.py','python/worker.py','python/deck_check.py','assets/icon.png'];
for(const file of exact)assert.equal(sha(asar.extractFile(archive,file)),sha(fs.readFileSync(path.resolve(__dirname,'..',file))),file+' must match tested source');
for(const file of ['node_modules/three/build/three.module.js','node_modules/three/build/three.core.js'])assert.ok(asar.extractFile(archive,file).length>1000,file);
for(const file of ['fixtures/axial-bar.step','fixtures/cantilever.step','fixtures/holed-plate.step','runtime.json'])assert.ok(fs.existsSync(path.join(app,'Contents/Resources',file)),file);
console.log('Packaged source, viewer dependencies, samples and runtime paths verified.');

assert.equal(sha(fs.readFileSync(path.join(app,'Contents/Resources/icon.icns'))),sha(fs.readFileSync(path.resolve(__dirname,'../assets/icon.icns'))),'Finder/Dock icon must match the selected asset');
