import tkinter as tk
from tkinter import filedialog,colorchooser,messagebox
import math,json,copy

class App:
 def __init__(self,r):
  self.r=r; r.title('Macaque WalkThrough Pro 0.2');r.geometry('1120x650');self.objects=[];self.sel=-1;self.start=None;self.tool=tk.StringVar(value='Wall');self.height=tk.StringVar(value='3');self.color='#b8a58b';self.cam=[0,-7,0];self.scale=24;self.history=[];self.future=[];self.elevation=tk.StringVar(value="0");self.projection=tk.StringVar(value="Top");self.collision=tk.BooleanVar(value=True)
  bar=tk.Frame(r,relief='raised',bd=2);bar.pack(fill='x')
  for name,fn in [('New',self.new),('Open',self.load),('Save',self.save),('Demo',self.demo),('Color',self.choose),('Delete',self.delete),('Reset camera',self.reset),('Undo',self.undo),('Redo',self.redo),('Duplicate',self.duplicate),('Export OBJ',self.export)]:tk.Button(bar,text=name,command=fn).pack(side='left')
  body=tk.PanedWindow(r,sashwidth=5);body.pack(fill='both',expand=True);left=tk.Frame(body);right=tk.Frame(body);body.add(left);body.add(right)
  tk.Label(left,text='Top View — Design',relief='raised').pack(fill='x');tk.Label(right,text='Walk View — Perspective',relief='raised').pack(fill='x')
  tools=tk.Frame(left);tools.pack(fill='x')
  for t in ['Select','Wall','Room','Box','Door','Window','Table','Chair','Bed']:tk.Radiobutton(tools,text=t,variable=self.tool,value=t,indicatoron=False).pack(side='left')
  tk.Label(tools,text='Height (m)').pack(side='left');tk.Entry(tools,textvariable=self.height,width=5).pack(side='left')
  options=tk.Frame(left);options.pack(fill='x')
  tk.Label(options,text='Elevation').pack(side='left');tk.Entry(options,textvariable=self.elevation,width=5).pack(side='left')
  tk.Button(options,text='Apply height / elevation',command=self.apply_dimensions).pack(side='left')
  tk.OptionMenu(options,self.projection,'Top','Front','Side',command=lambda _:self.draw()).pack(side='left')
  tk.Button(options,text='+',command=lambda:self.zoom(1.25)).pack(side='left');tk.Button(options,text='−',command=lambda:self.zoom(.8)).pack(side='left')
  tk.Checkbutton(options,text='Collision',variable=self.collision).pack(side='left')
  self.plan=tk.Canvas(left,bg='#fffef5',width=520);self.plan.pack(fill='both',expand=True);self.view=tk.Canvas(right,bg='#a9bbd0',width=560);self.view.pack(fill='both',expand=True)
  tk.Label(r,text='Drag in Top View to build • Select and drag to move • WASD walk • Left/Right turn • Drag in Walk View to turn').pack(fill='x')
  self.plan.bind('<Button-1>',self.down);self.plan.bind('<B1-Motion>',self.move);self.plan.bind('<ButtonRelease-1>',self.up);self.view.bind('<Button-1>',lambda e:(self.view.focus_set(),setattr(self,'lastx',e.x)));self.view.bind('<B1-Motion>',self.turn);self.view.bind('<Key>',self.key)
  for c in (self.plan,self.view):c.bind('<Configure>',lambda e:self.draw())
  self.demo()
  self.history.clear()
 def new(self):self.checkpoint();self.objects=[];self.sel=-1;self.draw()
 def reset(self):self.cam=[0,-7,0];self.draw()
 def demo(self):
  self.checkpoint()
  self.objects=[[-5,0,5,.2,3,'#c1ac91'],[-5,0,-4.8,7,3,'#b7aa92'],[4.8,0,5,7,3,'#c1ac91'],[-5,6.8,5,7,3,'#b7aa92'],[-3,3,-1,4.3,.8,'#82634c'],[1,4,3,5,1.1,'#708c91']];self.sel=-1;self.cam=[0,1,0];self.objects.extend([[5,0,10,.2,3,'#c1ac91'],[9.8,0,10,7,3,'#c1ac91'],[5,6.8,10,7,3,'#c1ac91']]);self.opening(4.7,2,5.1,3.5,'Door');self.opening(-2,-.1,1,.3,'Window');self.furniture(6,3,8,5,'Table',0);self.draw()
 def choose(self):
  c=colorchooser.askcolor(self.color)[1]
  if c:
   self.color=c
   if self.sel>=0:self.checkpoint();self.objects[self.sel][5]=c
   self.draw()
 def delete(self):
  if self.sel>=0:self.checkpoint();self.objects.pop(self.sel);self.sel=-1;self.draw()
 def save(self):
  p=filedialog.asksaveasfilename(defaultextension='.mwt',filetypes=[('WalkThrough project','*.mwt')]);
  if p:
   with open(p,'w') as f:json.dump(self.objects,f)
 def load(self):
  p=filedialog.askopenfilename(filetypes=[('WalkThrough project','*.mwt')]);
  if p:
   try:
    with open(p) as f:data=json.load(f)
    assert isinstance(data,list) and all(len(o) in (6,7) and all(isinstance(v,(int,float)) and math.isfinite(v) for v in o[:5]) and isinstance(o[5],str) and len(o[5])==7 and o[5][0]=='#' and all(c in '0123456789abcdefABCDEF' for c in o[5][1:]) for o in data)
    self.checkpoint();self.objects=[o if len(o)==7 else o+[0] for o in data];self.sel=-1;self.draw()
   except Exception as e:messagebox.showerror('Open failed',str(e))
 def xy(self,e):return (round((e.x-self.plan.winfo_width()/2)/self.scale*2)/2,round((self.plan.winfo_height()/2-e.y)/self.scale*2)/2)
 def screen(self,x,z):return self.plan.winfo_width()/2+x*self.scale,self.plan.winfo_height()/2-z*self.scale
 def down(self,e):
  if self.projection.get()!="Top":return
  self.start=self.xy(e);self.original=None
  if self.tool.get()=='Select':
   x,z=self.start;self.sel=next((i for i in reversed(range(len(self.objects))) if self.objects[i][0]-.15<=x<=self.objects[i][2]+.15 and self.objects[i][1]-.15<=z<=self.objects[i][3]+.15),-1)
   if self.sel>=0:self.checkpoint();self.original=self.objects[self.sel][:]
  self.draw()
 def move(self,e):
  if self.start is None:return
  x,z=self.xy(e);a,b=self.start
  if self.original is not None:
   o=self.original[:];o[0]+=x-a;o[2]+=x-a;o[1]+=z-b;o[3]+=z-b;self.objects[self.sel]=o;self.draw()
  elif self.tool.get()!='Select':
   self.draw();self.plan.create_rectangle(*self.screen(a,b),*self.screen(x,z),outline='blue',dash=(4,3))
 def up(self,e):
  if self.start is None:return
  a,b=self.start;x,z=self.xy(e);self.start=None
  if self.tool.get()=='Select':return
  try:h=max(.1,min(50,float(self.height.get())))
  except ValueError:return
  a,x=sorted((a,x));b,z=sorted((b,z));t=.2
  if self.tool.get()=='Wall':
   if x-a>z-b:z=b+t
   else:x=a+t
  if self.tool.get() in ("Door","Window"):
   x=max(x,a+.2);z=max(z,b+.2)
  if x-a<.1 or z-b<.1:return
  self.checkpoint()
  try:base=float(self.elevation.get())
  except ValueError:base=0
  tool=self.tool.get()
  if tool in ('Door','Window'):
   self.opening(a,b,x,z,tool);self.draw();return
  if tool in ('Table','Chair','Bed'):
   self.furniture(a,b,x,z,tool,base);self.draw();return
  if self.tool.get()=='Room':self.objects.extend([[a,b,x,b+t,h,self.color],[a,z-t,x,z,h,self.color],[a,b,a+t,z,h,self.color],[x-t,b,x,z,h,self.color]])
  else:self.objects.append([a,b,x,z,h,self.color,base])
  self.draw()
 def turn(self,e):self.cam[2]+=(e.x-self.lastx)*.008;self.lastx=e.x;self.draw()
 def key(self,e):
  x,z,y=self.cam;k=e.keysym.lower();s=.3
  if k=='left':y-=.12
  if k=='right':y+=.12
  if k in ('w','up','s','down','a','d'):
   f=1 if k in ('w','up') else -1 if k in ('s','down') else 0;side=1 if k=='d' else -1 if k=='a' else 0;x+=s*(f*math.sin(y)+side*math.cos(y));z+=s*(f*math.cos(y)-side*math.sin(y))
  if self.collision.get() and any(a-.18<x<c+.18 and b-.18<z<d+.18 and base<1.7 and base+ht>.3 for a,b,c,d,ht,col,base in self.parts()):x,z=self.cam[:2]
  self.cam=[x,z,y];self.draw()
 def parts(self):return [o if len(o)==7 else o+[0] for o in self.objects]
 def checkpoint(self):
  self.history.append(copy.deepcopy(self.objects));self.history=self.history[-60:];self.future.clear()
 def undo(self):
  if self.history:self.future.append(copy.deepcopy(self.objects));self.objects=self.history.pop();self.sel=-1;self.draw()
 def redo(self):
  if self.future:self.history.append(copy.deepcopy(self.objects));self.objects=self.future.pop();self.sel=-1;self.draw()
 def duplicate(self):
  if self.sel>=0:
   self.checkpoint();o=self.objects[self.sel][:];o[0]+=.5;o[1]+=.5;o[2]+=.5;o[3]+=.5;self.objects.append(o);self.sel=len(self.objects)-1;self.draw()
 def zoom(self,f):self.scale=max(8,min(100,self.scale*f));self.draw()
 def apply_dimensions(self):
  if self.sel<0:return
  try:h=float(self.height.get());base=float(self.elevation.get());assert math.isfinite(h) and math.isfinite(base) and h>0
  except (ValueError,AssertionError):return
  self.checkpoint();o=self.parts()[self.sel];o[4]=h;o[6]=base;self.objects[self.sel]=o;self.draw()
 def opening(self,a,b,x,z,tool):
  # Split a wall into side sections and lintel/sill around the opening.
  for i,(l,t,r,u,h,c,base) in enumerate(self.parts()):
   if base!=0 or min(r,x)<=max(l,a) or min(u,z)<=max(t,b):continue
   horizontal=r-l>u-t
   if min(r-l,u-t)>.5:continue
   lo,hi=(max(l,a),min(r,x)) if horizontal else (max(t,b),min(u,z))
   if hi-lo<.15:continue
   low=0 if tool=='Door' else min(.9,h*.3);high=min(h,2.1)
   def piece(start,end,bottom,height):
    if end-start>.01 and height>.01:self.objects.append(([start,t,end,u] if horizontal else [l,start,r,end])+[height,c,bottom])
   self.objects.pop(i);piece(l if horizontal else t,lo,0,h);piece(hi,r if horizontal else u,0,h);piece(lo,hi,0,low);piece(lo,hi,high,h-high);self.sel=-1;return
  messagebox.showinfo('Opening','Drag across an existing thin wall to cut an opening.')
 def furniture(self,a,b,x,z,tool,base):
  h=.75 if tool=='Table' else .45;leg=min(.12,(x-a)/4,(z-b)/4)
  if tool=='Bed':self.objects.extend([[a,b,x,z,.3,'#795942',base],[a,b,x,z,.2,'#e3ddd0',base+.3],[a,z-(z-b)*.25,x,z,.12,'#ffffff',base+.5]]);return
  for X in (a,x-leg):
   for Z in (b,z-leg):self.objects.append([X,Z,X+leg,Z+leg,h,'#795942',base])
  self.objects.append([a,b,x,z,.12,self.color,base+h])
  if tool=='Chair':self.objects.append([a,z-leg,x,z,.5,self.color,base+h])
 def export(self):
  path=filedialog.asksaveasfilename(defaultextension='.obj',filetypes=[('Wavefront OBJ','*.obj')])
  if not path:return
  with open(path,'w') as f:
   f.write('# Macaque WalkThrough Pro\n')
   for i,(a,b,x,z,h,c,y) in enumerate(self.parts()):
    f.write(f'o Object_{i+1}\n')
    for v in [(a,y,b),(x,y,b),(x,y,z),(a,y,z),(a,y+h,b),(x,y+h,b),(x,y+h,z),(a,y+h,z)]:f.write('v %g %g %g\n'%v)
    for face in [(1,2,3,4),(8,7,6,5),(5,6,2,1),(6,7,3,2),(7,8,4,3),(8,5,1,4)]:f.write('f '+' '.join(str(i*8+j) for j in face)+'\n')
 def draw(self):
  p=self.plan;p.delete('all');w=p.winfo_width();h=p.winfo_height()
  for x in range(int(-w/self.scale/2)-1,int(w/self.scale/2)+2):p.create_line(*self.screen(x,-h/self.scale),*self.screen(x,h/self.scale),fill='#dddcd4')
  for z in range(int(-h/self.scale/2)-1,int(h/self.scale/2)+2):p.create_line(*self.screen(-w/self.scale,z),*self.screen(w/self.scale,z),fill='#dddcd4')
  for i,(a,b,x,z,ht,c,base) in enumerate(self.parts()):
   mode=self.projection.get();coords=(a,b,x,z) if mode=='Top' else (a,base,x,base+ht) if mode=='Front' else (b,base,z,base+ht)
   p.create_rectangle(*self.screen(*coords[:2]),*self.screen(*coords[2:]),fill=c,outline='blue' if i==self.sel else '#444444',width=2)
  cx,cz,y=self.cam;px,py=self.screen(cx,cz);p.create_oval(px-4,py-4,px+4,py+4,fill='red');p.create_line(px,py,px+15*math.sin(y),py-15*math.cos(y),fill='red',width=2)
  v=self.view;v.delete('all');w=v.winfo_width();h=v.winfo_height();v.create_rectangle(0,h/2,w,h,fill='#a29c8c',outline='');faces=[];f=w*.75
  def camera(pt):
   dx,dy,dz=pt[0]-cx,pt[1]-1.65,pt[2]-cz;return (dx*math.cos(y)-dz*math.sin(y),dy,dx*math.sin(y)+dz*math.cos(y))
  for a,b,x,z,ht,c,base in self.parts():
   verts=[camera(t) for t in [(a,base,b),(x,base,b),(x,base,z),(a,base,z),(a,base+ht,b),(x,base+ht,b),(x,base+ht,z),(a,base+ht,z)]]
   for ids,shade in [([0,1,5,4],.85),([1,2,6,5],.65),([2,3,7,6],.85),([3,0,4,7],.65),([4,5,6,7],1)]:
    poly=[verts[i] for i in ids];cl=[]
    for A,B in zip(poly,poly[1:]+poly[:1]):
     if A[2]>=.08:cl.append(A)
     if (A[2]>=.08)!=(B[2]>=.08):
      t=(.08-A[2])/(B[2]-A[2]);cl.append(tuple(A[i]+t*(B[i]-A[i]) for i in range(3)))
    if len(cl)<3:continue
    rgb=[int(int(c[i:i+2],16)*shade) for i in (1,3,5)];col='#%02x%02x%02x'%tuple(rgb);faces.append((sum(t[2] for t in cl)/len(cl),[(w/2+f*X/Z,h/2-f*Y/Z) for X,Y,Z in cl],col))
  for _,pts,c in sorted(faces,key=lambda t:t[0],reverse=True):v.create_polygon(*[n for pt in pts for n in pt],fill=c,outline='#555555')
  v.create_line(w/2-6,h/2,w/2+6,h/2,fill='white');v.create_line(w/2,h/2-6,w/2,h/2+6,fill='white')
if __name__=='__main__':
 root=tk.Tk();App(root);root.mainloop()
