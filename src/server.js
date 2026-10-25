import http from 'node:http';
import { DatabaseSync } from 'node:sqlite';
import { randomBytes, scryptSync, timingSafeEqual, createHash } from 'node:crypto';
import { mkdirSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { tradeProfit, businessProfit, freeReward } from './finance.js';
const root=fileURLToPath(new URL('../',import.meta.url));
mkdirSync(process.env.DATA_DIR||root+'data',{recursive:true});
const db=new DatabaseSync((process.env.DATA_DIR||root+'data')+'/omnia.sqlite');
db.exec(`PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL,role TEXT NOT NULL,country TEXT NOT NULL,receiver_type TEXT);
CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id INTEGER REFERENCES users(id),expires INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS listings(id INTEGER PRIMARY KEY,title TEXT NOT NULL,category TEXT NOT NULL,country TEXT NOT NULL,price INTEGER NOT NULL,description TEXT NOT NULL,owner INTEGER REFERENCES users(id));
CREATE TABLE IF NOT EXISTS requests(id INTEGER PRIMARY KEY,title TEXT NOT NULL,description TEXT NOT NULL,country TEXT NOT NULL,owner INTEGER REFERENCES users(id),accepted_by INTEGER REFERENCES users(id),created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY,buyer INTEGER REFERENCES users(id),listing INTEGER REFERENCES listings(id),total INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'sandbox_reserved',created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,actor INTEGER,event TEXT NOT NULL,entity INTEGER,created TEXT DEFAULT CURRENT_TIMESTAMP);`);
if(!db.prepare('SELECT id FROM listings LIMIT 1').get()) {
 const ins=db.prepare('INSERT INTO listings(title,category,country,price,description) VALUES(?,?,?,?,?)');
 for(const x of [['Studio ceramic collection','Home & Living','Portugal',4800,'Hand-finished stoneware from an independent Portuguese studio. Set of four cups.'],['Linen everyday tote','Fashion','France',3200,'Durable natural linen tote. Made in small batches.'],['Oak desk essentials','Home & Living','Germany',6900,'Thoughtfully crafted solid oak desk organizer.'],['Extra virgin olive oil','Food & Agriculture','Spain',2400,'Cold-pressed olive oil from a family producer. 500 ml.'],['Reclaimed timber panels','Materials','Netherlands',1800,'Reclaimed wood for your next interior project. Price per panel.'],['Solar garden light','Technology','Italy',3900,'Rechargeable outdoor lighting for shared spaces.']])ins.run(...x);
}
const countries=['Austria','Belgium','Croatia','Cyprus','Estonia','Finland','France','Germany','Greece','Ireland','Italy','Latvia','Lithuania','Luxembourg','Malta','Netherlands','Portugal','Slovakia','Slovenia','Spain','Bulgaria'];
const roles=['Customer','Procurer','Manufacturer','Seller','Receiver'];
const hash=t=>createHash('sha256').update(t).digest('hex');
const audit=(actor,event,entity)=>db.prepare('INSERT INTO audit(actor,event,entity) VALUES(?,?,?)').run(actor,event,entity);
const safeUser=u=>u?{id:u.id,name:u.name,role:u.role,country:u.country,receiverType:u.receiver_type}:null;
const text=(v,min=1,max=300)=>typeof v==='string'&&v.trim().length>=min&&v.trim().length<=max;
const fail=(status,message)=>{throw Object.assign(new Error(message),{status});};
const attempts=new Map();
const server=http.createServer(async(req,res)=>{
 res.setHeader('Content-Security-Policy',"default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'");
 res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Referrer-Policy','same-origin');res.setHeader('Cache-Control','no-store');
 const json=(status,data)=>{res.writeHead(status,{'Content-Type':'application/json'});res.end(JSON.stringify(data));};
 try {
 const url=new URL(req.url,'http://localhost');
 if(!url.pathname.startsWith('/api/')) {
  if(req.method!=='GET')return fail(405,'Method not allowed');
  const files={'/':['index.html','text/html'],'/app.js':['app.js','text/javascript'],'/style.css':['style.css','text/css']};
  const f=files[url.pathname];if(!f)return fail(404,'Not found');res.setHeader('Content-Type',f[1]);return res.end(readFileSync(root+'public/'+f[0]));
 }
 const cookie=(req.headers.cookie||'').match(/(?:^|;\s*)session=([a-f0-9]{64})(?:;|$)/)?.[1];
 const user=cookie?db.prepare('SELECT u.* FROM users u JOIN sessions s ON u.id=s.user_id WHERE s.token=? AND s.expires>?').get(hash(cookie),Date.now()):null;
 const needUser=()=>{if(!user)fail(401,'Please sign in');return user;};
 let body={};
 if(req.method==='POST') {
  if(req.headers.origin&&req.headers.origin!==(process.env.PUBLIC_ORIGIN||`http://${req.headers.host}`))fail(403,'Origin rejected');
  if(!req.headers['content-type']?.startsWith('application/json'))fail(415,'JSON required');
  let raw='';for await(const chunk of req){raw+=chunk;if(raw.length>16384)fail(413,'Request too large');}
  try{body=JSON.parse(raw);}catch{fail(400,'Invalid JSON');}if(!body||Array.isArray(body)||typeof body!=='object')fail(400,'Invalid body');
 }
 if(req.method==='GET'&&url.pathname==='/api/health')return json(200,{status:'ok',mode:'sandbox',currency:'EUR'});
 if(req.method==='GET'&&url.pathname==='/api/config')return json(200,{countries,roles,receiverTypes:['Home','Warehouse','Store'],mode:'sandbox'});
 if(req.method==='GET'&&url.pathname==='/api/me')return json(200,{user:safeUser(user)});
 if(req.method==='POST'&&['/api/register','/api/login'].includes(url.pathname)) {
  const key=req.socket.remoteAddress;const a=attempts.get(key)||{count:0,until:Date.now()+60000};if(Date.now()>a.until){a.count=0;a.until=Date.now()+60000;}if(++a.count>20)fail(429,'Try again in a minute');attempts.set(key,a);
  if(!text(body.email,3,254)||!/^\S+@\S+\.\S+$/.test(body.email)||!text(body.password,12,128))fail(400,'Valid email and password of 12–128 characters required');
  const email=body.email.trim().toLowerCase();let u;
  if(url.pathname==='/api/register') {
   if(!text(body.name,2,80)||!roles.includes(body.role)||!countries.includes(body.country)||(body.role==='Receiver'&&!['Home','Warehouse','Store'].includes(body.receiverType)))fail(400,'Complete your name, role, geography and receiver type');
   const salt=randomBytes(16).toString('hex');const password=salt+':'+scryptSync(body.password,salt,64).toString('hex');
   try{const result=db.prepare('INSERT INTO users(name,email,password,role,country,receiver_type) VALUES(?,?,?,?,?,?)').run(body.name.trim(),email,password,body.role,body.country,body.role==='Receiver'?body.receiverType:null);u=db.prepare('SELECT * FROM users WHERE id=?').get(result.lastInsertRowid);audit(u.id,'user_registered',u.id);}catch(e){if(e.code?.includes('SQLITE_CONSTRAINT'))fail(409,'Account already exists');throw e;}
  }else{
   u=db.prepare('SELECT * FROM users WHERE email=?').get(email);const [salt,digest]=(u?.password||'dummy:'+ '00'.repeat(64)).split(':');const actual=scryptSync(body.password,salt,64);if(!u||!timingSafeEqual(actual,Buffer.from(digest,'hex')))fail(401,'Invalid email or password');
  }
  const token=randomBytes(32).toString('hex');db.prepare('INSERT INTO sessions VALUES(?,?,?)').run(hash(token),u.id,Date.now()+86400000);res.setHeader('Set-Cookie',`session=${token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=86400${process.env.PUBLIC_ORIGIN?.startsWith('https:')?'; Secure':''}`);return json(200,{user:safeUser(u)});
 }
 if(req.method==='POST'&&url.pathname==='/api/logout'){if(cookie)db.prepare('DELETE FROM sessions WHERE token=?').run(hash(cookie));res.setHeader('Set-Cookie','session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0');return json(200,{ok:true});}
 if(req.method==='GET'&&url.pathname==='/api/listings') {
  const q=(url.searchParams.get('q')||'').slice(0,100),country=url.searchParams.get('country')||'',category=url.searchParams.get('category')||'';
  return json(200,{items:db.prepare("SELECT id,title,category,country,price,description FROM listings WHERE title LIKE ? AND (?='' OR country=?) AND (?='' OR category=?) ORDER BY id DESC LIMIT 100").all('%'+q+'%',country,country,category,category)});
 }
 if(req.method==='POST'&&url.pathname==='/api/listings') {
  needUser();if(!['Seller','Manufacturer','Procurer'].includes(user.role))fail(403,'A supplier role is required');
  if(!text(body.title,3,120)||!text(body.description,10,2000)||!['Home & Living','Fashion','Food & Agriculture','Materials','Technology'].includes(body.category)||!Number.isSafeInteger(body.price)||body.price<0||body.price>100000000||!countries.includes(body.country))fail(400,'Invalid listing');
  const r=db.prepare('INSERT INTO listings(title,category,country,price,description,owner) VALUES(?,?,?,?,?,?)').run(body.title.trim(),body.category,body.country,body.price,body.description.trim(),user.id);audit(user.id,'listing_created',r.lastInsertRowid);return json(201,{id:Number(r.lastInsertRowid)});
 }
 if(req.method==='GET'&&url.pathname==='/api/requests')return json(200,{items:db.prepare('SELECT r.*,u.name FROM requests r JOIN users u ON u.id=r.owner ORDER BY r.id DESC LIMIT 100').all()});
 if(req.method==='POST'&&url.pathname==='/api/requests'){
  needUser();if(!text(body.title,3,120)||!text(body.description,10,2000)||!countries.includes(body.country))fail(400,'Complete all request fields');
  const r=db.prepare('INSERT INTO requests(title,description,country,owner) VALUES(?,?,?,?)').run(body.title.trim(),body.description.trim(),body.country,user.id);audit(user.id,'request_created',r.lastInsertRowid);return json(201,{id:Number(r.lastInsertRowid)});
 }
 if(req.method==='POST'&&/^\/api\/requests\/\d+\/accept$/.test(url.pathname)){
  needUser();if(!['Procurer','Manufacturer','Seller','Receiver'].includes(user.role))fail(403,'A participant role is required');const id=Number(url.pathname.split('/')[3]);
  const r=db.prepare('UPDATE requests SET accepted_by=? WHERE id=? AND accepted_by IS NULL AND owner<>? AND country=?').run(user.id,id,user.id,user.country);if(!r.changes)fail(409,'Request unavailable or outside your geography');audit(user.id,'request_voluntarily_accepted',id);return json(200,{ok:true});
 }
 if(req.method==='POST'&&url.pathname==='/api/orders'){
  needUser();const item=db.prepare('SELECT * FROM listings WHERE id=?').get(Number(body.listingId));if(!item)fail(404,'Listing not found');if(item.owner===user.id)fail(400,'Cannot reserve your own listing');
  const r=db.prepare('INSERT INTO orders(buyer,listing,total) VALUES(?,?,?)').run(user.id,item.id,item.price);audit(user.id,'sandbox_reservation_created',r.lastInsertRowid);return json(201,{id:Number(r.lastInsertRowid),status:'sandbox_reserved',total:item.price,paymentCollected:false});
 }
 if(req.method==='GET'&&url.pathname==='/api/dashboard'){
  needUser();return json(200,{user:safeUser(user),orders:db.prepare('SELECT o.*,l.title FROM orders o JOIN listings l ON l.id=o.listing WHERE buyer=? ORDER BY o.id DESC').all(user.id),requests:db.prepare('SELECT * FROM requests WHERE owner=? OR accepted_by=?').all(user.id,user.id),audit:db.prepare('SELECT event,entity,created FROM audit WHERE actor=? ORDER BY id DESC LIMIT 30').all(user.id)});
 }
 if(req.method==='POST'&&url.pathname==='/api/finance/preview'){
  if(!Number.isSafeInteger(body.cents)||body.cents<0||body.cents>100000000)fail(400,'Amount must be integer cents');
  let result;if(body.kind==='trade')result=tradeProfit(body.cents);else if(body.kind==='business')result=businessProfit(body.cents);else if(body.kind==='free'&&Number.isInteger(body.participants)&&body.participants>=1&&body.participants<=100)result=freeReward(body.cents,body.participants);else fail(400,'Invalid calculation');return json(200,{mode:'preview',currency:'EUR',result});
 }
 fail(404,'Not found');
 }catch(e){json(e.status||500,{error:e.status?e.message:'Internal server error'});if(!e.status)console.error(e.code||e.name);}
});
server.listen(Number(process.env.PORT)||3000,process.env.HOST||'127.0.0.1',()=>console.log('Omnia-Mundi sandbox listening on port '+(process.env.PORT||3000)));
