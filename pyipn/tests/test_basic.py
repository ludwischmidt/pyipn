from pyipn import Universe, copy_template


def test_simple():

    copy_template()
    uni = Universe.from_yaml('template_config.yaml')
    uni.explode_grb(tstart=-50,tstop=50)
    for det, lc in uni.light_curves.items():
    
        lc.display(-10,50,1.)
