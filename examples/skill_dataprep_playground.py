import BPG
from bag.layout.util import BBox


class SkillClassName(BPG.PhotonicTemplateBase):
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
        )

    @classmethod
    def get_default_param_values(cls):
        return dict(
        )

    def draw_layout(self):
        """ Specifies the creation of the lumerical shapes """

        # circ = BPG.photonic_objects.PhotonicRound(
        #     layer='SI',
        #     resolution=self.grid.resolution/100,
        #     center=(40, 30),
        #     rout=10,
        #     rin=5,
        #     # theta0=45,
        #     # theta1=60,
        #     unit_mode=False
        # )
        # self.add_round(circ)

        self.add_rect(
            layer=('RX', 'drawing'),
            coord1=(10, 10),
            coord2=(20, 24),
        )

        self.add_rect(
            layer=('RX', 'drawing'),
            coord1=(-100, -100),
            coord2=(-50, -70),
        )

        self.add_polygon(
            layer=('RX', 'drawing'),
            points=[(0, 0), (10, 0), (10, 5), (0, 5)]
        )

        self.add_polygon(
            layer=('RX', 'drawing'),
            points=[(0, 0), (20, 0), (20, 10)]
        )

        self.add_polygon(
            layer=('RX', 'drawing'),
            points=[(30, 0), (40, 10), (50, 0), (40, -10)]
        )


if __name__ == '__main__':
    # Load a previous BPG Project if it exists, otherwise create a new one
    local_dict = locals()
    if 'prj' not in local_dict:
        print('Creating BAG project')
        bprj = BPG.PhotonicBagProject()

    else:
        print('Loading BAG project')
        bprj = local_dict['bprj']


    spec_file = 'BPG/examples/specs/skill_dataprep_specs.yaml'
    PLM = BPG.PhotonicLayoutManager(bprj, spec_file)
    PLM.generate_gds()
    PLM.dataprep_skill()