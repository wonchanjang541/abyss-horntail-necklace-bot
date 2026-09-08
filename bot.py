import os, random, sqlite3, io, asyncio
import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

TOKEN=os.getenv('DISCORD_BOT_TOKEN'); GUILD_ID=1536042800754466906; DB='abyss_horntail_necklace.db'; MAX_SLOTS=2

def con():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init_db():
 c=con(); c.execute('''CREATE TABLE IF NOT EXISTS item(user_id INTEGER PRIMARY KEY,base_str INTEGER,base_dex INTEGER,base_int INTEGER,base_luk INTEGER,str_stat INTEGER,dex INTEGER,int_stat INTEGER,luk INTEGER,atk INTEGER DEFAULT 3,matk INTEGER DEFAULT 3,pdef INTEGER DEFAULT 300,mdef INTEGER DEFAULT 300,avoid INTEGER DEFAULT 40,slots INTEGER DEFAULT 2,success_count INTEGER DEFAULT 0,destroyed INTEGER DEFAULT 0,lock_str INTEGER DEFAULT 0,lock_dex INTEGER DEFAULT 0,lock_int INTEGER DEFAULT 0,lock_luk INTEGER DEFAULT 0,lock_atk INTEGER DEFAULT 0,lock_matk INTEGER DEFAULT 0,lock_pdef INTEGER DEFAULT 0,lock_mdef INTEGER DEFAULT 0,lock_avoid INTEGER DEFAULT 0)'''); c.commit(); c.close()

def roll(uid):
 s=[random.randint(25,29) for _ in range(4)]; c=con(); c.execute('INSERT OR REPLACE INTO item VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(uid,*s,*s,3,3,300,300,40,2,0,0,0,0,0,0,0,0,0,0,0)); c.commit(); c.close()

def get(uid):
 c=con(); r=c.execute('SELECT * FROM item WHERE user_id=?',(uid,)).fetchone(); c.close()
 if not r: roll(uid); c=con(); r=c.execute('SELECT * FROM item WHERE user_id=?',(uid,)).fetchone(); c.close()
 return r

def save(uid,**kw):
 c=con(); c.execute('UPDATE item SET '+','.join(k+'=?' for k in kw)+' WHERE user_id=?',(*kw.values(),uid)); c.commit(); c.close()

def reset(uid):
 c=con(); c.execute('DELETE FROM item WHERE user_id=?',(uid,)); c.commit(); c.close(); roll(uid)

def font(n):
 for p in ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
  if os.path.exists(p): return ImageFont.truetype(p,n)
 return ImageFont.load_default()
ICON=Image.open('abyss_horntail_necklace.png').convert('RGBA')

def added_total(r):
 return (r['str_stat']-r['base_str'])+(r['dex']-r['base_dex'])+(r['int_stat']-r['base_int'])+(r['luk']-r['base_luk'])+(r['atk']-3)+(r['matk']-3)+(r['pdef']-300)+(r['mdef']-300)+(r['avoid']-40)

def ncolor(r):
 b=added_total(r)
 if b<0:return (170,170,170)
 if b<=5:return (255,160,70) if r['success_count'] else (255,255,255)
 if b<=22:return (90,150,255)
 if b<=39:return (190,100,255)
 if b<=56:return (255,225,70)
 if b<=73:return (90,220,100)
 return (255,80,80)

def card(r):
 im=Image.new('RGB',(690,700),(20,32,61)); d=ImageDraw.Draw(im); d.rounded_rectangle((12,12,678,688),20,fill=(28,45,82),outline=(102,144,205),width=3)
 plus=f" +{r['success_count']}" if r['success_count'] else ''
 d.text((30,25),'심연의 혼테일의 목걸이'+plus,font=font(30),fill=(255,100,100) if r['destroyed'] else ncolor(r))
 ic=ICON.copy(); ic.thumbnail((105,105)); im.paste(ic,(35,80),ic)
 if r['destroyed']:
  d.text((165,105),'파괴된 목걸이',font=font(28),fill=(255,100,100)); d.text((35,220),'백줌 실패로 장비가 파괴되었습니다.',font=font(22),fill=(255,220,220)); d.text((35,265),'아래 초기화 버튼으로 새 목걸이를 시작하세요.',font=font(20),fill='white'); return im
 d.text((165,90),'장비분류 : 목걸이',font=font(22),fill='white'); y=205
 for name,val in [('STR',r['str_stat']),('DEX',r['dex']),('INT',r['int_stat']),('LUK',r['luk']),('HP','+10%'),('MP','+10%'),('공격력',r['atk']),('마력',r['matk']),('물리방어력',r['pdef']),('마법방어력',r['mdef']),('회피율',r['avoid']),('보스 공격 시 데미지','+1%')]:
  d.text((45,y),f'{name} : {val}' if isinstance(val,str) else f'{name} : +{val}',font=font(20),fill=(245,245,245)); y+=37
 d.text((45,y+8),f"업그레이드 가능 횟수 : {r['slots']}",font=font(22),fill='white'); return im

async def show(i,r,msg='',edit=False):
 im=await asyncio.to_thread(card,r); b=io.BytesIO(); im.save(b,'PNG'); b.seek(0); f=discord.File(b,'abyss_horntail_necklace.png')
 if edit: await i.response.edit_message(content=msg,attachments=[f],view=View())
 else: await i.response.send_message(content=msg,file=f,view=View())

def chaos_changes(r):
 ch={}; out=[]
 for stat,lock in [('str_stat','lock_str'),('dex','lock_dex'),('int_stat','lock_int'),('luk','lock_luk'),('atk','lock_atk'),('matk','lock_matk'),('pdef','lock_pdef'),('mdef','lock_mdef'),('avoid','lock_avoid')]:
  old=r[stat]; new=0 if r[lock] else max(0,old+random.randint(-5,5));
  if new==0: ch[lock]=1
  ch[stat]=new; out.append((stat,new-old))
 return ch,out

async def chaos(i):
 r=get(i.user.id); uid=i.user.id
 if r['destroyed']: return await i.response.send_message('💥 파괴된 목걸이입니다. **🔄 초기화**를 눌러주세요.',ephemeral=True)
 if r['slots']<=0:return await i.response.send_message('❌ 남은 업그레이드 횟수가 없습니다.',ephemeral=True)
 s=r['slots']-1
 if random.random()<.60:
  ch,ds=chaos_changes(r); ch['slots']=s; ch['success_count']=r['success_count']+1; save(uid,**ch)
  names={'str_stat':'STR','dex':'DEX','int_stat':'INT','luk':'LUK','atk':'공','matk':'마력','pdef':'물방','mdef':'마방','avoid':'회피'}; msg='✨ **혼돈의 주문서 60% 성공!**\n'+', '.join(f"{names[k]} {v:+d}" for k,v in ds)+'\nHP / MP / 보공은 변하지 않습니다.'
 else: save(uid,slots=s); msg='❌ **혼돈의 주문서 60% 실패!**'
 await show(i,get(uid),msg,True)

async def white(i,pct):
 r=get(i.user.id); uid=i.user.id
 if r['destroyed']:return await i.response.send_message('💥 파괴된 목걸이입니다. **🔄 초기화**를 눌러주세요.',ephemeral=True)
 if r['slots']>=MAX_SLOTS:return await i.response.send_message('❌ 이미 업그레이드 가능 횟수가 최대 2회입니다.',ephemeral=True)
 if random.random()<pct/100:
  save(uid,slots=min(MAX_SLOTS,r['slots']+1)); msg=f'✨ **백줌 {pct}% 성공!** 업그레이드 가능 횟수 +1'
 else:
  boom=random.random() < (.02 if pct==1 else .06); save(uid,destroyed=int(boom)); msg=f'💥 **백줌 {pct}% 실패! 장비가 파괴되었습니다.**' if boom else f'❌ **백줌 {pct}% 실패!**'
 await show(i,get(uid),msg,True)

class View(discord.ui.View):
 def __init__(self): super().__init__(timeout=None)
 @discord.ui.button(label='혼줌 60%',style=discord.ButtonStyle.danger,emoji='📜',custom_id='ahn_c')
 async def c(self,i,b): await chaos(i)
 @discord.ui.button(label='백줌 1%',style=discord.ButtonStyle.primary,emoji='🧾',custom_id='ahn_w1')
 async def w1(self,i,b): await white(i,1)
 @discord.ui.button(label='백줌 3%',style=discord.ButtonStyle.primary,emoji='🧾',custom_id='ahn_w3')
 async def w3(self,i,b): await white(i,3)
 @discord.ui.button(label='초기화',style=discord.ButtonStyle.secondary,emoji='🔄',custom_id='ahn_r')
 async def r(self,i,b): reset(i.user.id); await show(i,get(i.user.id),'🔄 **새 심연의 혼테일의 목걸이로 초기화했습니다.**',True)

bot=commands.Bot(command_prefix='!',intents=discord.Intents.default())
@bot.event
async def on_ready():
 bot.add_view(View()); g=discord.Object(id=GUILD_ID); bot.tree.copy_global_to(guild=g); x=await bot.tree.sync(guild=g); print(bot.user,len(x))
@bot.tree.command(name='심혼목강화',description='심연의 혼테일의 목걸이 강화 시뮬레이션')
async def enhance(i:discord.Interaction): await show(i,get(i.user.id),'🐉 **심연의 혼테일의 목걸이 강화 시뮬레이션**')
@bot.tree.command(name='심혼목초기화',description='심연의 혼테일의 목걸이를 새로 뽑습니다.')
async def rst(i:discord.Interaction): reset(i.user.id); await show(i,get(i.user.id),'🔄 **기본 옵션을 새로 뽑았습니다.**')
@bot.tree.command(name='심혼목랭킹',description='심연의 혼테일의 목걸이 랭킹 TOP 10')
async def rank(i:discord.Interaction):
 c=con(); rows=c.execute('SELECT * FROM item WHERE destroyed=0').fetchall(); c.close(); arr=[]; jobs=[('전사','atk','str_stat','STR'),('궁수','atk','dex','DEX'),('마법사','matk','int_stat','INT'),('도적','atk','luk','LUK')]
 for r in rows:
  best=max([(r[p]+r[s]*.2,r[p],r[s],-o,j,p,sn) for o,(j,p,s,sn) in enumerate(jobs)])
  arr.append((best[0],best[1],best[2],r['user_id'],best[4],best[5],best[6],r['success_count']))
 arr.sort(key=lambda x:(x[0],x[1],x[2]),reverse=True); arr=arr[:10]
 if not arr:return await i.response.send_message('아직 랭킹 기록이 없습니다.')
 lines=['🏆 **심연의 혼테일의 목걸이 랭킹 TOP 10**','기준: 전사/궁수/도적 = 공격력 + 주스탯×0.2 · 법사 = 마력 + INT×0.2','']; medals=['🥇','🥈','🥉']
 for n,(g,p,st,uid,job,pcol,sn,sc) in enumerate(arr,1):
  mark=medals[n-1] if n<=3 else f'**{n}.**'; pname='마력' if pcol=='matk' else '공격력'; plus=f'+{sc}' if sc else '무작'; lines.append(f'{mark} <@{uid}> — **{g:.1f}급** ({job} / {pname} {p} / {sn} +{st} / {plus})')
 await i.response.send_message('\n'.join(lines))
init_db(); bot.run(TOKEN)
