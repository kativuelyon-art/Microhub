import base64, math, re, sys
t=open('poster.template.html').read()
d=[]
for row in range(-1,16):
    for col in range(-1,16):
        x=col*14+(7 if row%2 else 0); y=row*12.5
        if (x-100)**2+(y-100)**2<98**2: d.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.6"/>')
t=t.replace('{{DIMPLES}}',''.join(d))
def img(m):
    n=m.group(1); mime='image/png' if n.endswith('png') else 'image/jpeg'
    return f'data:{mime};base64,'+base64.b64encode(open('web/'+n,'rb').read()).decode()
t=re.sub(r'\{\{img:([^}]+)\}\}',img,t)
open('poster_express.html','w').write(t.replace('{{FONTS}}','<link rel="stylesheet" href="https://use.typekit.net/rhi5gla.css">'))
open('poster_preview.html','w').write(t.replace('{{FONTS}}','<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:ital,wght@0,500;0,600;0,700;0,800;0,900;1,800;1,900&display=block">'))
