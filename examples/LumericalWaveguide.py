import BPG
from bag.layout.util import BBox


class SingleModeWaveguide(BPG.PhotonicTemplateBase):
    def __init__(self, temp_db,
                 lib_name,
                 params,
                 used_names,
                 **kwargs,
                 ):
        """ Class for generating a single mode waveguide shape in Lumerical """
        BPG.PhotonicTemplateBase.__init__(self, temp_db, lib_name, params, used_names, **kwargs)

    @classmethod
    def get_params_info(cls):
        return dict(
            width='Waveguide width in microns',
            length='Waveguide length in microns'
        )

    @classmethod
    def get_default_param_values(cls):
        return dict(
            width=.6,
            length=4
        )

    def draw_layout(self):
        """ Specifies the creation of the lumerical shapes """
        # Add cladding
        clad = self.add_rect(layer='Clad',
                             bbox=BBox(left=-5,
                                       bottom=-5,
                                       right=5,
                                       top=5,
                                       resolution=self.grid.resolution,
                                       unit_mode=False)
                             )

        # Add buried oxide layer
        box = self.add_rect(layer='BOX',
                            bbox=BBox(left=-5,
                                      bottom=-5,
                                      right=5,
                                      top=5,
                                      resolution=self.grid.resolution,
                                      unit_mode=False)
                            )

        # Add waveguide
        wg0 = self.add_rect(layer='Si',
                            bbox=BBox(left=-3,
                                      bottom=-2,
                                      right=-2,
                                      top=2,
                                      resolution=self.grid.resolution,
                                      unit_mode=False)
                            )

        # Add waveguide
        wg1 = self.add_rect(layer='Si',
                            bbox=BBox(left=2,
                                      bottom=-2,
                                      right=3,
                                      top=2,
                                      resolution=self.grid.resolution,
                                      unit_mode=False)
                            )

        poly_test = self.add_polygon()


if __name__ == '__main__':
    # Load a previous BPG Project if it exists, otherwise create a new one
    local_dict = locals()
    if 'prj' not in local_dict:
        print('creating BAG project')
        bprj = BPG.PhotonicBagProject()

    else:
        print('loading BAG project')
        bprj = local_dict['bprj']

    spec_file = './specs/example_spec_file.yaml'
    PLM = BPG.PhotonicLayoutManager(bprj, spec_file)
    PLM.generate_gds()
    PLM.generate_lsf()
