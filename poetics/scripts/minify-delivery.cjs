// Pinned browser UMD build: no runtime dependency installation or source maps.
const fs=require('fs'),vm=require('vm'),path=require('path');
const context={};vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname,'vendor/terser/bundle.min.js'),'utf8'),context);
let input='';process.stdin.setEncoding('utf8');process.stdin.on('data',s=>input+=s);
process.stdin.on('end',async()=>{try{
 const result={};for(const [name,source] of Object.entries(JSON.parse(input))){
  const output=await context.Terser.minify({[name]:source},{compress:false,mangle:true,format:{comments:/^!/}});
  result[name]=output.code+'\n';
 }process.stdout.write(JSON.stringify(result));
}catch(error){console.error(error);process.exitCode=1;}});
