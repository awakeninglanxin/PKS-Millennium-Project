
/* ============================================================
   文档物理公式引擎 + CSV质量推荐 + 双视图渲染
   ============================================================ */
const TAN22_5=Math.tan(22.5*Math.PI/180),ISO_COS=Math.cos(Math.PI/6),ISO_SIN=Math.sin(Math.PI/6);
const DEVICE={SEG:{key:'SEG',name:'SEG(4层材料)',rings:3,matLayers:4},IGV:{key:'IGV',name:'IGV(6层材料)',rings:3,matLayers:6}};
const MATERIALS_SEG=[{name:'集电层',color:'#3a4a5a'},{name:'绝缘层',color:'#e8ddd0'},{name:'磁层',color:'mag'},{name:'发射层',color:'#e8a040'}];
const MATERIALS_IGV=[{name:'集电层',color:'#3a4a5a'},{name:'绝缘层',color:'#e8ddd0'},{name:'钼层',color:'#c0c8d0'},{name:'谐波层',color:'#9ab84a'},{name:'磁层',color:'mag'},{name:'发射层',color:'#e8a040'}];
function getMat(k){return k==='SEG'?MATERIALS_SEG:MATERIALS_IGV;}
const SCHEMES=[{id:1,name:'方案1 已知尺寸求体积',ctrl:'size',adj:true},{id:2,name:'方案2 已知体积求高度',ctrl:'volume',adj:true},{id:3,name:'方案3 已知参数求b系数',ctrl:'size',adj:true},{id:4,name:'方案4 体积等差+等厚',ctrl:'derived',adj:false},{id:5,name:'方案5 等差+等厚等间距',ctrl:'derived',adj:false},{id:6,name:'方案6 三角函数定子半径',ctrl:'size',adj:true},{id:7,name:'方案7 质量密度体积',ctrl:'mass',adj:true}];
function getScheme(id){return SCHEMES.find(s=>s.id===id);}
const ALL_CFGS=[{id:'ce_fib',name:'💰Fib 34/21/13 P22/26/38',sp:[7594,12286,19882],rp:[22,26,38],num:[13,21,34],st:'good'},{id:'ce_mix',name:'💰混合32/21/13 P34/26/38',sp:[7594,12286,19882],rp:[34,26,38],num:[13,21,32],st:'good'},{id:'ce_orig',name:'💰原版Searl 32/22/12 P34/34/34',sp:[7594,12286,19882],rp:[34,34,34],num:[12,22,32],st:'good'},{id:'ce_mini',name:'💰极简20/14/8 P22/26/38',sp:[7594,12286,19882],rp:[22,26,38],num:[8,14,20],st:'good'},{id:'u34_mix',name:'🏭统一34极 混合32/21/13 P34',sp:[7594,12286,19882],rp:[34,34,34],num:[13,21,32],st:'good'},{id:'best87',name:'⚡7594/12286/19882 P22/26/38',sp:[7594,12286,19882],rp:[22,26,38],st:'good'},{id:'new',name:'📋1680/2730/4410 P34',sp:[1680,2730,4410],rp:[34,34,34],st:'good'},{id:'orig',name:'📋原版4410/11466/18522 P34',sp:[4410,11466,18522],rp:[34,34,34],st:'good'},{id:'c01',name:'📋4410/4830/5250 P34',sp:[4410,4830,5250],rp:[34,34,34],st:'good'},{id:'c02',name:'✗4290/4950/5610 P34',sp:[4290,4950,5610],rp:[34,34,34],st:'fail'}];
const MASS_SEG="4410,4830,5250;4290,4950,5610;4410,5130,5850;3990,5130,6270;4410,5250,6090;4290,5250,6210;3990,5250,6510;4950,5610,6270;4590,5610,6630;4290,5850,7410;4830,6090,7350;4590,6090,7590;4410,6090,7770;5130,6270,7410;4950,6270,7590;4290,6270,8250;5610,6510,7410;5250,6510,7770;3990,6510,9030;5610,6630,7650;6090,7350,8610;4950,7350,9750;4830,7350,9870;4410,7350,10290;6210,7410,8610;5850,7410,8970;6210,7590,8970;6270,7650,9030;6630,7770,8910;6510,7770,9030;7350,8610,9870;7770,9030,10290;7770,9750,11730;9030,10890,12750;10890,7594,15210";
const MASS_IGV="2205,6405,10605;2835,6885,10935;2835,7035,11235;4935,9315,13695;5265,9675,14085;7371,11529,15687;7605,11745,15885;7695,11925,16155;10449,14769,19089;10665,15015,19365;10701,14979,19257;10935,15195,19455;11115,15375,19635;11295,15555,19815;7686,10656,13626;8208,11088,13968;9738,11790,13842;11640,16800,21960;14880,21600,28320;11970,17430,22890;11460,16800,22140;28800,40800,52800;34650,47400,60150";
let MASSDATA={SEG:[],IGV:[]};
(function initMass(){MASSDATA.SEG=MASS_SEG.split(";").map(r=>{const p=r.split(",");return{sp:[+p[0],+p[1],+p[2]]};});MASSDATA.IGV=MASS_IGV.split(";").map(r=>{const p=r.split(",");return{sp:[+p[0],+p[1],+p[2]]};});})();

// Globals
let devKey='SEG',schemeId=4,cfg=ALL_CFGS[0],geo,angle=0,viewYaw=0,viewYawAuto=true,speed=1,paused=false,showTrajectory=true;
let heightOverrides={s:[50,34,18],r:[42,30,18]},heightAuto=true;
let paramOverrides={Yr:[2,2,2],Br0:4,n:[1,1,1]},paramAuto=true;
let volumeOverrides={Bv:[2293,2512,2731]},volumeAuto=true;
let massOverrides={m:[500,800,1200],rho:2.5},massAuto=true,minRollerVol=3;
let rollerNumOverrides={num:[12,22,32]},rollerNumAuto=true;
let volumeThreshold=10,eFactor=2.4,kFactor=1.2,minRollerH=6;
let particles=[];
const LAYER_COLORS=['#1d9e75','#378add','#ba7517','#c90','#9b59b6','#e67e22'];

function gcd(a,b){a=Math.abs(a);b=Math.abs(b);while(b){[a,b]=[b,a%b];}return a;}
function lcm(a,b){return a*b/gcd(a,b);}
function layerSpeed(i){return Math.pow(2.5,i);}

function computeGeometry(dk,si,cf){
  const dev=DEVICE[dk];const rings=dev.rings,matLayers=dev.matLayers;
  const sp=cf.sp,rp=cf.rp,ctrl=getScheme(si).ctrl,adj=getScheme(si).adj;
  const defNum=(cf.num&&cf.num.length===3)?cf.num:[12,22,32];
  const num=[],nFac=[],Yr=[],su=[],sd=[];
  for(let i=0;i<rings;i++){
    num[i]=(!rollerNumAuto&&rollerNumOverrides.num&&rollerNumOverrides.num[i])?rollerNumOverrides.num[i]:defNum[i];
    nFac[i]=adj&&paramOverrides.n?paramOverrides.n[i]:1;
    Yr[i]=adj&&paramOverrides.Yr?paramOverrides.Yr[i]:2;
    su[i]=1;sd[i]=1;
  }
  if(!adj){switch(si){case 4:for(let i=0;i<rings;i++)nFac[i]=2;break;case 5:for(let i=0;i<rings;i++){su[i]=1.6;sd[i]=1.6;}break;case 7:for(let i=0;i<rings;i++)Yr[i]=1.5*(1+i*0.18);break;}}
  const Br0=(adj&&paramOverrides.Br0!==undefined)?paramOverrides.Br0:4;
  const Br=[],BR=[],orbit=[];Br[0]=Br0;
  for(let i=0;i<rings;i++){
    const D=2*Yr[i];
    BR[i]=(si===6)?(D+nFac[i])/(2*Math.sin(Math.PI/num[i])):Yr[i]*num[i]*nFac[i];
    if(i<rings-1)Br[i+1]=BR[i]+su[i]+sd[i]+D;
  }
  for(let i=0;i<rings;i++){const ni=(i<rings-1)?Br[i+1]:BR[i]+su[i]+sd[i]+2*Yr[i];orbit[i]=(BR[i]+ni)/2;}
  const hS=[],hR=[];
  for(let i=0;i<rings;i++){
    const D=2*Yr[i];let Bh,Yh;
    if(ctrl==='volume'){if(volumeAuto||!volumeOverrides.Bv)volumeOverrides={Bv:[2293,2512,2731]};const Bv=volumeOverrides.Bv[i]||[2293,2512,2731][i],ra=Math.PI*(BR[i]*BR[i]-Br[i]*Br[i]);Bh=ra>0?Bv/ra:D*eFactor;Yh=Math.max(1,Bh/1-1.2);}
    else if(ctrl==='mass'){if(massAuto||!massOverrides.m)massOverrides={m:[500,800,1200],rho:2.5};const rho=massOverrides.rho||2.5,mass=massOverrides.m[i]||[500,800,1200][i],Bv=mass/rho,ra=Math.PI*(BR[i]*BR[i]-Br[i]*Br[i]);Bh=ra>0?Bv/ra:D*eFactor;Yh=Math.max(1,Bh/1-1.2);}
    else{Bh=D*eFactor;Yh=D/TAN22_5;}
    hS[i]=(heightOverrides.s[i]!==undefined)?heightOverrides.s[i]:Bh;
    hR[i]=(heightOverrides.r[i]!==undefined)?heightOverrides.r[i]:Yh;
  }
  const maxR=orbit[rings-1]+Yr[rings-1],layers=[];
  for(let i=0;i<rings;i++)layers.push({k:i,Br:Br[i],BR:BR[i],orbit:orbit[i],Yr:Yr[i],hStator:hS[i],hRoller:hR[i],num:num[i],statorPoles:sp[i],rollerPoles:rp[i],matLayers:matLayers});
  return{rings,matLayers,layers,maxR,devKey:dk};
}
function calcVolumes(geo){const vs=[],vr=[];for(let i=0;i<geo.rings;i++){const l=geo.layers[i];vs.push(Math.PI*(l.BR*l.BR-l.Br*l.Br)*l.hStator);vr.push(Math.PI*l.Yr*l.Yr*l.hRoller);}const minV=Math.min(...vs,...vr);return{stator:vs,roller:vr,minV,feasible:minV>=volumeThreshold};}

// RENDER
const c2d=document.getElementById('c2d'),x2=c2d.getContext('2d'),c3d=document.getElementById('c3d'),x3=c3d.getContext('2d');
function scale2d(){return 200/geo.maxR;}function scale3dR(){return 150/geo.maxR;}function scale3dZ(){return 4.5;}

function drawStator2D(cx,cy,Ri,Ro,nP,col,mats){
  const ml=mats.length,dr=(Ro-Ri)/ml;
  for(let m=0;m<ml;m++){const r1=Ri+m*dr,r2=Ri+(m+1)*dr,mc=mats[m];if(mc.color==='mag'){x2.beginPath();x2.arc(cx,cy,r2,0,2*Math.PI);x2.arc(cx,cy,r1,0,2*Math.PI,true);x2.fillStyle='rgba(80,80,120,0.15)';x2.fill('evenodd');const da=2*Math.PI/nP,vis=Math.min(nP,180),step=nP/vis;for(let i=0;i<vis;i++){const a=2*Math.PI*i/vis,isN=Math.floor(i*step)%2===0;x2.beginPath();x2.arc(cx,cy,r2,a,a+2*Math.PI/vis*0.85);x2.arc(cx,cy,r1,a+2*Math.PI/vis*0.85,a,true);x2.closePath();x2.fillStyle=isN?'rgba(255,70,70,0.55)':'rgba(70,120,255,0.55)';x2.fill();}}else{x2.beginPath();x2.arc(cx,cy,r2,0,2*Math.PI);x2.arc(cx,cy,r1,0,2*Math.PI,true);x2.fillStyle=mc.color;x2.fill('evenodd');}}
  x2.fillStyle=col;x2.font='bold 7px system-ui';x2.textAlign='center';x2.fillText(nP.toLocaleString()+'极',cx,cy-(Ro+9));
}
function drawRoller2D(cx,cy,orbitR,nR,pPerRoller,col,rot,layIdx){
  const sc=scale2d();x2.beginPath();x2.arc(cx,cy,orbitR,0,2*Math.PI);x2.setLineDash([3,5]);x2.strokeStyle=col+'40';x2.lineWidth=1;x2.stroke();x2.setLineDash([]);
  for(let j=0;j<nR;j++){const th=rot+2*Math.PI*j/nR,rcx=cx+orbitR*Math.cos(th),rcy=cy+orbitR*Math.sin(th),TR=geo.layers[layIdx].Yr*sc;x2.beginPath();x2.arc(rcx,rcy,TR,0,2*Math.PI);x2.fillStyle=col+'88';x2.fill();x2.strokeStyle=col;x2.lineWidth=1.5;x2.stroke();const spA=th*(orbitR/(TR||1));for(let k=0;k<pPerRoller;k++){const pa=spA+2*Math.PI*k/pPerRoller,px=rcx+(TR-2)*Math.cos(pa),py=rcy+(TR-2)*Math.sin(pa),sz=pPerRoller>30?1.2:2;x2.fillStyle=k%2===0?'#ff5050':'#5080ff';x2.fillRect(px-sz/2,py-sz/2,sz,sz);}}
}

let drawTrajectory=function(ctx,cx,cy,sc,lay,col){const orb=lay.orbit*sc;ctx.beginPath();for(let t=0;t<360;t++){const a=2*Math.PI*t/360,px=cx+orb*Math.cos(a),py=cy+orb*Math.sin(a);if(t===0)ctx.moveTo(px,py);else ctx.lineTo(px,py);}ctx.setLineDash([2,6]);ctx.strokeStyle=col+'55';ctx.lineWidth=1;ctx.stroke();ctx.setLineDash([]);};
function drawCheckerboard(ctx,w,h){const ss=16;for(let y=0;y<h;y+=ss)for(let x=0;x<w;x+=ss){ctx.fillStyle=(Math.floor(x/ss)+Math.floor(y/ss))%2===0?'#fff':'#e8f0ff';ctx.fillRect(x,y,ss,ss);}}

function draw2D(){
  const cx=250,cy=250,sc=scale2d();x2.clearRect(0,0,500,500);drawCheckerboard(x2,500,500);
  updateParticles();drawParticles();
  const rings=geo.rings,mats=getMat(geo.devKey);
  for(let i=rings-1;i>=0;i--){const lay=geo.layers[i],col=LAYER_COLORS[i%6],opx=lay.orbit*sc;if(showTrajectory)drawTrajectory(x2,cx,cy,sc,lay,col);drawRoller2D(cx,cy,opx,lay.num,lay.rollerPoles,col,angle*layerSpeed(i),i);drawStator2D(cx,cy,lay.Br*sc,lay.BR*sc,lay.statorPoles,col,mats);}
  const sc2=smoothScore();x2.fillStyle='#333';x2.font='bold 9px system-ui';x2.textAlign='center';x2.fillText((cfg.name.split('★')[1]||cfg.name).substring(0,46),cx,12);x2.fillStyle=sc2>=80?'#1d9e75':sc2>=50?'#ba7517':'#e24b4a';x2.fillText('综合性价比 '+sc2+'分 | '+DEVICE[geo.devKey].name+' · 方案'+schemeId,cx,26);

}

function initParticles(){particles=[];const N=300;for(let i=0;i<N;i++){const ri=Math.floor(Math.random()*geo.rings),lay=geo.layers[ri],sc=scale2d(),r=lay.orbit*sc+(Math.random()*2-1)*lay.Yr*sc;particles.push({r,a:Math.random()*2*Math.PI,vr:0.02+Math.random()*0.08,vt:[1,2.5,6.25][ri]*0.01*(0.5+Math.random()),ring:ri,life:1,alpha:0.3+Math.random()*0.5});}}
function updateParticles(){const scS=smoothScore(),rough=Math.max(0.005,(100-scS)/100*0.25),radU=scS/100,sc=scale2d();particles.forEach(p=>{p.life-=0.001;if(p.life<=0){const ri=Math.floor(Math.random()*geo.rings),lay=geo.layers[ri];p.ring=ri;p.r=lay.orbit*sc+(Math.random()*2-1)*lay.Yr*sc;p.a=Math.random()*2*Math.PI;p.vr=0.02+Math.random()*0.08;p.vt=[1,2.5,6.25][ri]*0.01*(0.5+Math.random());p.life=1;p.alpha=0.3+Math.random()*0.5;return;}p.vr+=0.0008*(1+p.r/180)*radU;const bA=p.a*(p.ring+1)*3;p.vt+=rough*Math.sin(bA)*0.001;p.vr*=0.998;p.vt*=0.998;p.r+=p.vr;p.a+=p.vt/p.r;const lay=geo.layers[p.ring];if(p.r>lay.orbit*sc+lay.Yr*sc+8)p.life=0;if(p.r<20){p.r=20;p.vr*=-0.5;}});}
function drawParticles(){const bins=40,dens=new Array(bins).fill(0);particles.forEach(p=>{const bi=Math.min(bins-1,Math.max(0,Math.floor(p.r/200*bins)));dens[bi]++;});const maxD=Math.max(1,...dens);particles.forEach(p=>{if(p.life<=0)return;const cx=250,cy=250,px=cx+p.r*Math.cos(p.a),py=cy+p.r*Math.sin(p.a),bi=Math.min(bins-1,Math.max(0,Math.floor(p.r/200*bins))),dN=dens[bi]/maxD;x2.beginPath();x2.arc(px,py,1.5,0,2*Math.PI);x2.fillStyle=`rgba(${150+50*dN|0},${130+60*dN|0},${40+30*dN|0},${p.alpha*(0.3+0.7*dN)})`;x2.fill();});}

// 3D
function isoPt(x,y,z,Sxy,Sz,cx,cy,yaw){const c=Math.cos(yaw),s=Math.sin(yaw),xr=x*c-y*s,yr=x*s+y*c;return{sx:cx+(xr-yr)*ISO_COS*Sxy,sy:cy+(xr+yr)*ISO_SIN*Sxy-z*Sz};}
function drawStator3D(ctx,Sxy,Sz,cx,cy,yaw,lay,col,mats){const Br=lay.Br,BR=lay.BR,h=lay.hStator,ml=mats.length,dr=(BR-Br)/ml,cTop=isoPt(0,0,h*Sz,Sxy,Sz,cx,cy,yaw);for(let m=0;m<ml;m++){const r1=Br+m*dr,r2=Br+(m+1)*dr,mc=mats[m];if(mc.color==='mag'){ctx.beginPath();ctx.ellipse(cTop.sx,cTop.sy,r2*ISO_COS*Sxy,r2*ISO_SIN*Sxy,0,0,2*Math.PI);ctx.ellipse(cTop.sx,cTop.sy,r1*ISO_COS*Sxy,r1*ISO_SIN*Sxy,0,0,2*Math.PI,true);ctx.fillStyle='rgba(80,80,120,0.22)';ctx.fill('evenodd');const nP=lay.statorPoles,da=2*Math.PI/nP,vis=Math.min(nP,180),step=nP/vis;for(let i=0;i<vis;i++){const a=2*Math.PI*i/vis,isN=Math.floor(i*step)%2===0;ctx.beginPath();ctx.ellipse(cTop.sx,cTop.sy,r2*ISO_COS*Sxy,r2*ISO_SIN*Sxy,0,a,a+da*step*0.85);ctx.strokeStyle=isN?'rgba(255,70,70,0.9)':'rgba(70,120,255,0.9)';ctx.lineWidth=1.5;ctx.stroke();}}else{ctx.beginPath();ctx.ellipse(cTop.sx,cTop.sy,r2*ISO_COS*Sxy,r2*ISO_SIN*Sxy,0,0,2*Math.PI);ctx.ellipse(cTop.sx,cTop.sy,r1*ISO_COS*Sxy,r1*ISO_SIN*Sxy,0,0,2*Math.PI,true);ctx.fillStyle=mc.color;ctx.fill('evenodd');}}}
function drawRoller3D(ctx,Sxy,Sz,cx,cy,yaw,lay,col,rot){const oR=lay.orbit,Yr=lay.Yr,zMid=lay.hStator*Sz/2;for(let j=0;j<lay.num;j++){const th=rot+2*Math.PI*j/lay.num,ox=oR*Math.cos(th),oy=oR*Math.sin(th),cp=isoPt(ox,oy,zMid,Sxy,Sz,cx,cy,yaw);ctx.beginPath();ctx.ellipse(cp.sx,cp.sy,Yr*ISO_COS*Sxy,Yr*ISO_SIN*Sxy,0,0,2*Math.PI);ctx.fillStyle=col;ctx.fill();ctx.strokeStyle=col;ctx.lineWidth=2;ctx.stroke();}}
function draw3D(){const Sxy=scale3dR(),Sz=scale3dZ(),cx=180,cy=370;x3.clearRect(0,0,360,640);drawCheckerboard(x3,360,640);const rings=geo.rings,mats=getMat(geo.devKey);for(let i=rings-1;i>=0;i--){const lay=geo.layers[i],col=LAYER_COLORS[i%6];drawStator3D(x3,Sxy,Sz,cx,cy,viewYaw,lay,col,mats);drawRoller3D(x3,Sxy,Sz,cx,cy,viewYaw,lay,col,angle*layerSpeed(i));}x3.fillStyle='#333';x3.font='bold 9px system-ui';x3.textAlign='center';x3.fillText(DEVICE[geo.devKey].name+' · 方案'+schemeId,cx,14);x3.fillStyle='#888';x3.font='7px system-ui';x3.fillText((viewYawAuto?'AUTO':'FIXED')+' | '+(paused?'PAUSED':'RUN')+' | 3rings x'+geo.matLayers+'mats',cx,28);}

// SCORE + UI
function smoothScore(){const sp=cfg.sp,rp=cfg.rp,rings=geo.rings;let s=0;const hp=sp.map(v=>v/2),hr=rp.map(v=>v/2);for(let i=0;i<rings;i++){if(gcd(hp[i],hr[i])===1)s+=22;}let cgS=0;for(let i=0;i<rings-1;i++)cgS+=1/(gcd(hp[i],hp[i+1])+1);s+=18*cgS/(rings-1);const diff=(rp[0]!==rp[1])+(rp[1]!==rp[2])+(rp[0]!==rp[2]);s+=diff*2;if(rp.every(v=>v===rp[0]))s+=8;let tot=hp[0];for(let i=1;i<rings;i++)tot=lcm(tot,hp[i]);s+=Math.log10(tot+1)*0.9;return Math.min(100,Math.round(s));}
function updateStatus(){const sp=cfg.sp,rp=cfg.rp;let all1=true;for(let i=0;i<geo.rings;i++)if(gcd(sp[i]/2,rp[i]/2)!==1)all1=false;const sc=smoothScore();document.getElementById('statusBar').innerHTML='<span class="'+(all1?'good':'bad')+'">'+(all1?'✓ 全互质':'✗ 公约数')+'</span> | '+DEVICE[devKey].name+' · '+geo.rings+'环 | 方案'+schemeId;document.getElementById('smoothFill').style.width=sc+'%';document.getElementById('smoothFill').style.background=sc>=80?'#1d9e75':sc>=50?'#ba7517':'#e24b4a';document.getElementById('smoothVal').textContent=sc+'分';}

function buildDevSelect(){const s=document.getElementById('devSelect');Object.values(DEVICE).forEach(d=>{const o=document.createElement('option');o.value=d.key;o.textContent=d.name;s.appendChild(o);});s.value=devKey;}
function buildSchemeSelect(){const s=document.getElementById('schemeSelect');SCHEMES.forEach(sc=>{const o=document.createElement('option');o.value=sc.id;o.textContent=sc.name;s.appendChild(o);});s.value=schemeId;}
function buildCfgSelect(){const s=document.getElementById('cfgSelect');s.innerHTML='';ALL_CFGS.forEach((c,i)=>{const o=document.createElement('option');o.value=i;o.textContent=c.name;if(c.st==='fail')o.style.color='#e24b4a';s.appendChild(o);});s.value=ALL_CFGS.indexOf(cfg);}
function buildMassSelect(){const s=document.getElementById('massSel'),data=MASSDATA[devKey];data.forEach((d,i)=>{const o=document.createElement('option');o.value=i;o.textContent=d.sp.join('/');s.appendChild(o);});}
function loadDev(k){devKey=k;resetForRebuild();buildMassSelect();rebuild();}
function loadScheme(id){schemeId=parseInt(id);resetForRebuild();rebuild();}
function loadCfg(i){cfg=ALL_CFGS[i];rebuild();}
function onMassSelect(idx){if(parseInt(idx)>=0){const d=MASSDATA[devKey][parseInt(idx)];cfg={id:'csv',name:'CSV推荐 '+d.sp.join('/'),sp:d.sp,rp:[34,34,34],num:[12,22,32],st:'good'};massAuto=false;massOverrides={m:d.sp,rho:massOverrides.rho||2.5};for(let i=0;i<3;i++){document.getElementById('m'+i).value=d.sp[i];document.getElementById('mn'+i).value=d.sp[i];}rebuild();}}
function resetForRebuild(){heightAuto=true;heightOverrides={s:[],r:[]};paramAuto=true;paramOverrides={Yr:[2,2,2],Br0:4,n:[1,1,1]};volumeAuto=true;volumeOverrides={Bv:[]};massAuto=true;massOverrides={m:[],rho:2.5};rollerNumAuto=true;rollerNumOverrides={num:[]};}
function rebuild(){geo=computeGeometry(devKey,schemeId,cfg);if(heightAuto)syncHtSliders();if(paramAuto&&getScheme(schemeId).ctrl==='size')syncParamSliders();if(rollerNumAuto)syncRNSliders();updateSliderLock();initParticles();updateStatus();}
function syncHtSliders(){for(let i=0;i<3;i++){const l=geo.layers[i];document.getElementById('hs'+i).value=Math.round(l.hStator);document.getElementById('hn'+i).value=Math.round(l.hStator);document.getElementById('hr'+i).value=Math.round(l.hRoller);document.getElementById('hnr'+i).value=Math.round(l.hRoller);}}
function syncParamSliders(){document.getElementById('pBr0').value=4;document.getElementById('pnBr0').value=4;document.getElementById('pYr0').value=2;document.getElementById('pnYr0').value=2;document.getElementById('pn0').value=1;document.getElementById('pnn0').value=1;}
function syncRNSliders(){const dn=(cfg.num&&cfg.num.length===3)?cfg.num:[12,22,32];for(let i=0;i<3;i++){document.getElementById('rn'+i).value=dn[i];document.getElementById('rnn'+i).value=dn[i];}}

// slider handlers
function onHtChange(){heightAuto=false;heightOverrides={s:[+document.getElementById('hs0').value,+document.getElementById('hs1').value,+document.getElementById('hs2').value],r:[+document.getElementById('hr0').value,+document.getElementById('hr1').value,+document.getElementById('hr2').value]};for(let i=0;i<3;i++){document.getElementById('hn'+i).value=heightOverrides.s[i];document.getElementById('hnr'+i).value=heightOverrides.r[i];}geo=computeGeometry(devKey,schemeId,cfg);}
function onHtNum(i){let v=+document.getElementById('hn'+i).value;if(isNaN(v))return;document.getElementById('hs'+i).value=v;onHtChange();}
function onHtNumR(i){let v=+document.getElementById('hnr'+i).value;if(isNaN(v))return;document.getElementById('hr'+i).value=v;onHtChange();}
function onParamChange(){paramAuto=false;paramOverrides={Br0:+document.getElementById('pBr0').value||4,Yr:[+document.getElementById('pYr0').value,+document.getElementById('pYr0').value,+document.getElementById('pYr0').value],n:[+document.getElementById('pn0').value,+document.getElementById('pn0').value,+document.getElementById('pn0').value]};document.getElementById('pnBr0').value=paramOverrides.Br0;document.getElementById('pnYr0').value=paramOverrides.Yr[0];document.getElementById('pnn0').value=paramOverrides.n[0];geo=computeGeometry(devKey,schemeId,cfg);updateVolDisplay();}
function onParamNum(k){let v;if(k==='Br0'){v=+document.getElementById('pnBr0').value||4;document.getElementById('pBr0').value=v;}else if(k==='Yr'){v=+document.getElementById('pnYr0').value||2;document.getElementById('pYr0').value=v;}else{v=+document.getElementById('pnn0').value||1;document.getElementById('pn0').value=v;}onParamChange();}
function onRNChange(){rollerNumAuto=false;rollerNumOverrides={num:[+document.getElementById('rn0').value,+document.getElementById('rn1').value,+document.getElementById('rn2').value]};for(let i=0;i<3;i++)document.getElementById('rnn'+i).value=rollerNumOverrides.num[i];geo=computeGeometry(devKey,schemeId,cfg);initParticles();updateStatus();}
function onRNNum(i){let v=+document.getElementById('rnn'+i).value;if(isNaN(v)||v<1)return;document.getElementById('rn'+i).value=v;onRNChange();}
function onVolChange(){volumeAuto=false;volumeOverrides={Bv:[+document.getElementById('bv0').value,+document.getElementById('bv1').value,+document.getElementById('bv2').value]};for(let i=0;i<3;i++)document.getElementById('bvn'+i).value=volumeOverrides.Bv[i];geo=computeGeometry(devKey,schemeId,cfg);updateVolDisplay();}
function onMassChange(){massAuto=false;massOverrides={m:[+document.getElementById('m0').value,+document.getElementById('m1').value,+document.getElementById('m2').value],rho:+document.getElementById('rho').value||2.5};for(let i=0;i<3;i++)document.getElementById('mn'+i).value=massOverrides.m[i];document.getElementById('rhoN').value=massOverrides.rho;geo=computeGeometry(devKey,schemeId,cfg);updateVolDisplay();}
function onVminChange(){volumeThreshold=+document.getElementById('vMin').value;document.getElementById('vMinN').value=volumeThreshold;updateVolDisplay();}
function onMinHChange(){minRollerH=+document.getElementById('minH').value;document.getElementById('minHN').value=minRollerH;updateVolDisplay();}
function onMinRVChange(){minRollerVol=+document.getElementById('minRV').value;document.getElementById('minRVN').value=minRollerVol;updateVolDisplay();}
function onEFacChange(){eFactor=+document.getElementById('eFac').value;document.getElementById('eFacN').value=eFactor;geo=computeGeometry(devKey,schemeId,cfg);updateVolDisplay();}
function onKFacChange(){kFactor=+document.getElementById('kFac').value;document.getElementById('kFacN').value=kFactor;updateVolDisplay();}
function updateVolDisplay(){const vol=calcVolumes(geo),s=vol.stator.map(v=>v.toFixed(1)).join('/'),r=vol.roller.map(v=>v.toFixed(1)).join('/'),ctrl=getScheme(schemeId).ctrl;let extra='',warn='';if(ctrl==='volume'){const yh=geo.layers.map(l=>l.hRoller.toFixed(1)).join('/');extra=' | 滚筒高 '+yh+' '+(Math.min(...geo.layers.map(l=>l.hRoller))>=minRollerH?'<span class="good">≥'+minRollerH+'cm✓</span>':'<span class="bad">&lt;'+minRollerH+'cm</span>');}if(ctrl==='mass'){const yvr=vol.roller.map(v=>v.toFixed(1)).join('/');extra=' | 滚筒体 '+yvr+' '+(Math.min(...vol.roller)>=minRollerVol?'<span class="good">≥'+minRollerVol+'cm³✓</span>':'<span class="bad">&lt;'+minRollerVol+'cm³</span>');}for(let i=1;i<geo.rings;i++){if(geo.layers[i].hRoller>=geo.layers[i-1].hStator/kFactor){warn='<span class="warn">⚠环'+(i+1)+'滚筒高≥环'+i+'定子高/'+kFactor.toFixed(1)+'</span> ';break;}}document.getElementById('volInfo').innerHTML=warn+'定子体积 '+s+' | 滚筒 '+r+' cm³'+extra+' | Min='+vol.minV.toFixed(1)+' '+(vol.feasible?'<span class="good">✓可行</span>':'<span class="bad">✗低于Vmin</span>');}
function updateSliderLock(){const sch=getScheme(schemeId),ctrl=sch.ctrl,adj=sch.adj,lock=document.getElementById('lockInfo');lock.textContent=ctrl==='volume'?'🔓 体积→高度':ctrl==='size'?'🔓 尺寸→体积':ctrl==='mass'?'🔓 质量→体积':'🔒 锁定';lock.style.color=adj?'#1d9e75':'#e24b4a';for(let i=0;i<3;i++){document.getElementById('hs'+i).disabled=ctrl!=='size';document.getElementById('hn'+i).disabled=ctrl!=='size';document.getElementById('hr'+i).disabled=ctrl!=='size';document.getElementById('hnr'+i).disabled=ctrl!=='size';document.getElementById('hs'+i).style.opacity=ctrl==='size'?'1':'0.45';document.getElementById('hr'+i).style.opacity=ctrl==='size'?'1':'0.45';}['pBr0','pnBr0','pYr0','pnYr0','pn0','pnn0'].forEach(id=>{const el=document.getElementById(id);if(el)el.disabled=ctrl!=='size';});document.getElementById('volRow').style.display=ctrl==='volume'?'flex':'none';document.getElementById('massRow').style.display=ctrl==='mass'?'flex':'none';updateVolDisplay();}
function resetHeights(){heightAuto=true;heightOverrides={s:[],r:[]};paramAuto=true;paramOverrides={Yr:[2,2,2],Br0:4,n:[1,1,1]};geo=computeGeometry(devKey,schemeId,cfg);syncHtSliders();syncParamSliders();document.getElementById('rn0').value=12;document.getElementById('rn1').value=22;document.getElementById('rn2').value=32;for(let i=0;i<3;i++)document.getElementById('rnn'+i).value=[12,22,32][i];rollerNumAuto=true;rollerNumOverrides={num:[]};updateVolDisplay();}

// init
c2d.addEventListener('wheel',e=>{e.preventDefault();speed=Math.max(0.1,Math.min(4,speed+(e.deltaY>0?-0.2:0.2)));document.getElementById('spd').textContent=speed+'x';});
c3d.addEventListener('wheel',e=>{e.preventDefault();speed=Math.max(0.1,Math.min(4,speed+(e.deltaY>0?-0.2:0.2)));document.getElementById('spd').textContent=speed+'x';});
c2d.addEventListener('click',()=>{paused=!paused;});c3d.addEventListener('click',()=>{viewYawAuto=!viewYawAuto;});
geo=computeGeometry(devKey,schemeId,cfg);buildDevSelect();buildSchemeSelect();buildCfgSelect();buildMassSelect();
initParticles();updateStatus();syncHtSliders();updateVolDisplay();
setInterval(()=>{if(!paused)angle+=0.005*speed;if(viewYawAuto)viewYaw+=0.003*speed;},16);
(function frame(){draw2D();draw3D();requestAnimationFrame(frame);})();
