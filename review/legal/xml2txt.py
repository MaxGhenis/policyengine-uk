import sys, re, xml.etree.ElementTree as ET
def text(el):
    out=[]
    def walk(e, depth=0):
        tag=e.tag.split('}')[-1]
        if tag in ('Commentaries','Commentary','Metadata','Contents'): return
        if tag in ('Number','Pnumber'):
            out.append('\n'+(e.text or '').strip()+' ')
        elif e.text and e.text.strip(): out.append(e.text.strip()+' ')
        for c in e:
            walk(c, depth+1)
            if c.tail and c.tail.strip(): out.append(c.tail.strip()+' ')
        if tag in ('P','Text','Title'): out.append('\n')
    walk(el)
    s=''.join(out)
    s=re.sub(r'\n\s*\n+','\n',s)
    return s
for f in sys.argv[1:]:
    root=ET.parse(f).getroot()
    body=None
    for e in root.iter():
        if e.tag.split('}')[-1] in ('Body','Primary','Secondary'):
            body=e
    print('=====',f)
    print(text(body if body is not None else root)[:8000])
