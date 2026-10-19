"""Show the actual old/new card regions, at equal scale, without lighting or blur."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
import cairosvg

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/line_gradient_refined'
ns='{http://www.w3.org/2000/svg}'
old=ET.parse(ROOT/'output/line_gradient_test/preview/card.svg').getroot()
new=ET.parse(OUT/'preview/card.svg').getroot()
geometry=json.loads((OUT/'geometry_validation.json').read_text())
width,height,_=geometry['size_mm']
assert max(abs(a-b) for a,b in zip(map(float,old.get('viewBox').split()),[0.,0.,width,height]))<.001
scale=5.5; margin=35; panel=width*scale; gap=30
canvas_width=2*panel+2*margin+gap; canvas_height=height*scale+175
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_width}" height="{canvas_height}" viewBox="0 0 {canvas_width} {canvas_height}">',
     '<rect width="100%" height="100%" fill="#edf0f5"/>',
     '<g font-family="sans-serif" fill="#1d2940">',
     f'<text x="{margin}" y="35" font-size="23">Gerade Farbbahnen · gleiche Logogrösse</text>',
     f'<text x="{margin}" y="63" font-size="15">0,4-mm-Düse · nominelle Farben · digitale Flächenprüfung weiterhin nicht bestanden</text>']
for index,(root,label) in enumerate(((old,'Bisher: 0,48 mm'),(new,'Entwurf: 0,44 mm · gerundete Enden'))):
    x=margin+index*(panel+gap)
    svg.append(f'<text x="{x}" y="100" font-size="20">{label}</text>')
    svg.append(f'<g transform="translate({x},115) scale({scale})">')
    svg.extend(ET.tostring(child,encoding='unicode') for child in root)
    svg.append('</g>')
svg.extend(['</g>','</svg>'])
path=OUT/'preview/comparison.svg';path.write_text('\n'.join(svg))
cairosvg.svg2png(url=str(path),write_to=str(path.with_suffix('.png')),output_width=1800)
print(path.with_suffix('.png'))
