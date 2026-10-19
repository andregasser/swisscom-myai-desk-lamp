"""Build test card 13 from the approved straight, variable-width full-logo SVG."""
import json
import hashlib
import build_line_gradient_test as card

SOURCE=card.ROOT/'design_studies/line_gradient_full/proposal.svg'
OUT=card.ROOT/'output/line_gradient_full'

def main():
    study=json.loads((SOURCE.parent/'preview_checks.json').read_text())
    assert study['all_interfaces_straight'] and not study['endpoint_modifications']
    assert study['nominal_nozzle_mm']==.4 and study['minimum_designed_band_mm']==.32
    assert study['source_sha256']==hashlib.sha256((card.ROOT/'assets/logos/Mode=Dark, Type=Stacked.svg').read_bytes()).hexdigest()
    card.main(SOURCE,OUT,corner_radius=1.,plate_name='13_full_line_test',design_metadata={
        'band_label':'variable Farbbahnen ab 0.32 mm',
        'minimum_designed_band_mm':.32,'source_svg_sha256':study['source_sha256'],
        'source_study_sha256':hashlib.sha256((SOURCE.parent/'preview_checks.json').read_bytes()).hexdigest(),
        'all_interfaces_straight':True,'endpoint_modifications':False,'contour_border_mm':0,
        'documentation':'FARBBAHNEN_GESAMT_TEST.md',
        'method':'Extrusion of the approved full-gradient SVG; no endpoint reassignment or added border.'})

if __name__=='__main__':main()
