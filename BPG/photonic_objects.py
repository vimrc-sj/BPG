# -*- coding: utf-8 -*-

"""This module defines various layout objects one can add and manipulate in a template.
"""
from typing import TYPE_CHECKING, Union, List, Tuple, Optional, Dict, Any, Iterator, Iterable, \
    Generator

from bag.layout.objects import Arrayable, Rect, Path, PathCollection, TLineBus, Polygon, Blockage, Boundary, \
    ViaInfo, Via, PinInfo, Instance
from bag.layout.routing import RoutingGrid
from bag.layout.template import TemplateBase
import bag.io
from bag.layout.util import transform_loc_orient, transform_point

if TYPE_CHECKING:
    from BPG.photonic_template import PhotonicTemplateBase
    from BPG.photonic_port import PhotonicPort


ldim = Union[float, int]
dim_type = Union[float, int]
coord_type = Tuple[dim_type, dim_type]


class InstanceInfo(dict):
    """A dictionary that represents a layout instance.
    """

    param_list = ['lib', 'cell', 'view', 'name', 'loc', 'orient', 'num_rows',
                  'num_cols', 'sp_rows', 'sp_cols']

    def __init__(self, res, change_orient=True, **kwargs):
        kv_iter = ((key, kwargs[key]) for key in self.param_list)
        dict.__init__(self, kv_iter)
        self._resolution = res
        if 'params' in kwargs:
            self.params = kwargs['params']

        # skill/OA array before rotation, while we're doing the opposite.
        # this is supposed to fix it.
        if change_orient:
            orient = self['orient']
            if orient == 'R180':
                self['sp_rows'] *= -1
                self['sp_cols'] *= -1
            elif orient == 'MX':
                self['sp_rows'] *= -1
            elif orient == 'MY':
                self['sp_cols'] *= -1
            elif orient == 'R90':
                self['sp_rows'], self['sp_cols'] = self['sp_cols'], -self['sp_rows']
                self['num_rows'], self['num_cols'] = self['num_cols'], self['num_rows']
            elif orient == 'MXR90':
                self['sp_rows'], self['sp_cols'] = self['sp_cols'], self['sp_rows']
                self['num_rows'], self['num_cols'] = self['num_cols'], self['num_rows']
            elif orient == 'MYR90':
                self['sp_rows'], self['sp_cols'] = -self['sp_cols'], -self['sp_rows']
                self['num_rows'], self['num_cols'] = self['num_cols'], self['num_rows']
            elif orient == 'R270':
                self['sp_rows'], self['sp_cols'] = -self['sp_cols'], self['sp_rows']
                self['num_rows'], self['num_cols'] = self['num_cols'], self['num_rows']
            elif orient != 'R0':
                raise ValueError('Unknown orientation: %s' % orient)

    @property
    def lib(self):
        # type: () -> str
        return self['lib']

    @property
    def cell(self):
        # type: () -> str
        return self['cell']

    @property
    def view(self):
        # type: () -> str
        return self['view']

    @property
    def name(self):
        # type: () -> str
        return self['name']

    @name.setter
    def name(self, new_name):
        # type: (str) -> None
        self['name'] = new_name

    @property
    def loc(self):
        # type: () -> Tuple[float, float]
        loc_list = self['loc']
        return loc_list[0], loc_list[1]

    @property
    def orient(self):
        # type: () -> str
        return self['orient']

    @property
    def num_rows(self):
        # type: () -> int
        return self['num_rows']

    @property
    def num_cols(self):
        # type: () -> int
        return self['num_cols']

    @property
    def sp_rows(self):
        # type: () -> float
        return self['sp_rows']

    @property
    def sp_cols(self):
        # type: () -> float
        return self['sp_cols']

    @property
    def params(self):
        # type: () -> Optional[Dict[str, Any]]
        return self.get('params', None)

    @params.setter
    def params(self, new_params):
        # type: (Optional[Dict[str, Any]]) -> None
        self['params'] = new_params

    @property
    def angle_reflect(self):
        # type: () -> Tuple[int, bool]
        orient = self['orient']
        if orient == 'R0':
            return 0, False
        elif orient == 'R180':
            return 180, False
        elif orient == 'MX':
            return 0, True
        elif orient == 'MY':
            return 180, True
        elif orient == 'R90':
            return 90, False
        elif orient == 'MXR90':
            return 90, True
        elif orient == 'MYR90':
            return 270, True
        elif orient == 'R270':
            return 270, False
        else:
            raise ValueError('Unknown orientation: %s' % orient)

    def copy(self):
        """Override copy method of dictionary to return an InstanceInfo instead."""
        return InstanceInfo(self._resolution, change_orient=False, **self)

    def move_by(self, dx=0, dy=0):
        # type: (float, float) -> None
        """Move this instance by the given amount.

        Parameters
        ----------
        dx : float
            the X shift.
        dy : float
            the Y shift.
        """
        res = self._resolution
        loc = self.loc
        self['loc'] = [round((loc[0] + dx) / res) * res,
                       round((loc[1] + dy) / res) * res]


class PhotonicInstance(Instance):
    """A layout instance, with optional arraying parameters.

    Parameters
    ----------
    parent_grid : RoutingGrid
        the parent RoutingGrid object.
    lib_name : str
        the layout library name.
    master : TemplateBase
        the master template of this instance.
    loc : Tuple[Union[float, int], Union[float, int]]
        the origin of this instance.
    orient : str
        the orientation of this instance.
    name : Optional[str]
        name of this instance.
    nx : int
        number of columns.
    ny : int
        number of rows.
    spx : Union[float, int]
        column pitch.
    spy : Union[float, int]
        row pitch.
    unit_mode : bool
        True if layout dimensions are specified in resolution units.
    """

    def __init__(self,
                 parent_grid,  # type: RoutingGrid
                 lib_name,  # type: str
                 master,  # type: PhotonicTemplateBase
                 loc,  # type: Tuple[ldim, ldim]
                 orient,  # type: str
                 name=None,  # type: Optional[str]
                 nx=1,  # type: int
                 ny=1,  # type: int
                 spx=0,  # type: ldim
                 spy=0,  # type: ldim
                 unit_mode=False,  # type: bool
                 ):
        # type: (...) -> None
        res = parent_grid.resolution
        Arrayable.__init__(self, res, nx=nx, ny=ny, spx=spx, spy=spy, unit_mode=unit_mode)
        self._parent_grid = parent_grid
        self._lib_name = lib_name
        self._inst_name = name
        self._master = master
        if unit_mode:
            self._loc_unit = loc[0], loc[1]
        else:
            self._loc_unit = int(round(loc[0] / res)), int(round(loc[1] / res))
        self._orient = orient
        self._photonic_port_list = {}
        self._photonic_port_creator()

    def _photonic_port_creator(self):
        # type: (...) -> None
        """
        Helper for creating the photonic ports of this instance
        Returns
        -------

        """
        for port_name in self._master.photonic_ports_names_iter():
            self._photonic_port_list[port_name] = self._master.get_photonic_port(port_name).transform(
                loc=self._loc_unit,
                orient=self._orient,
                unit_mode=True
            )

    def set_port_used(self,
                      port_name,  # type: str
                      ):
        # type: (...) -> None
        if port_name not in self._photonic_port_list:
            raise ValueError("Photonic port {} not in instance {}", port_name, self._inst_name)

        self._photonic_port_list[port_name].used(True)

    def get_port_used(self,
                      port_name,  # type: str
                      ):
        # type: (...) -> bool
        if port_name not in self._photonic_port_list:
            raise ValueError("Photonic port {} not in instance {}", port_name, self._inst_name)

        return self._photonic_port_list[port_name].used()

    def get_photonic_port(self,
                          name,  # type: str
                          row=0,  # type: int
                          col=0,  # type: int
                          ):
        # type: (...) -> PhotonicPort
        """

        Parameters
        ----------
        name
        row
        col

        Returns
        -------

        """
        # TODO: Incomplete
        dx, dy = self.get_item_location(row=row, col=col, unit_mode=True)
        xshift, yshift = self._loc_unit
        loc = (xshift + dx, yshift + dy)
        return self._photonic_port_list[name].transform(
            loc=loc,
            orient='R0'
        )

    @property
    def master(self):
        # type: () -> PhotonicTemplateBase
        """The master template of this instance."""
        return self._master

    def get_bound_box_of(self, row=0, col=0):
        """Returns the bounding box of an instance in this mosaic."""
        dx, dy = self.get_item_location(row=row, col=col, unit_mode=True)
        xshift, yshift = self._loc_unit
        xshift += dx
        yshift += dy
        return self._master.bound_box.transform((xshift, yshift), self.orientation, unit_mode=True)

    def move_by(self, dx=0, dy=0, unit_mode=False):
        # type: (Union[float, int], Union[float, int], bool) -> None
        """Move this instance by the given amount.

        Parameters
        ----------
        dx : Union[float, int]
            the X shift.
        dy : Union[float, int]
            the Y shift.
        unit_mode : bool
            True if shifts are given in resolution units
        """
        if not unit_mode:
            dx = int(round(dx / self.resolution))
            dy = int(round(dy / self.resolution))
        self._loc_unit = self._loc_unit[0] + dx, self._loc_unit[1] + dy

        # TODO: Incomplete
        for port in self._photonic_port_list:
            port.transform()


    def get_port(self, name='', row=0, col=0):
        # type: (Optional[str], int, int) -> Port
        """Returns the port object of the given instance in the array.

        Parameters
        ----------
        name : Optional[str]
            the port terminal name.  If None or empty, check if this
            instance has only one port, then return it.
        row : int
            the instance row index.  Index 0 is the bottom-most row.
        col : int
            the instance column index.  Index 0 is the left-most column.

        Returns
        -------
        port : Port
            the port object.
        """
        dx, dy = self.get_item_location(row=row, col=col, unit_mode=True)
        xshift, yshift = self._loc_unit
        loc = (xshift + dx, yshift + dy)
        return self._master.get_port(name).transform(self._parent_grid, loc=loc,
                                                     orient=self.orientation, unit_mode=True)

    def get_pin(self, name='', row=0, col=0, layer=-1):
        # type: (Optional[str], int, int, int) -> Union[WireArray, BBox]
        """Returns the first pin with the given name.

        This is an efficient method if you know this instance has exactly one pin.

        Parameters
        ----------
        name : Optional[str]
            the port terminal name.  If None or empty, check if this
            instance has only one port, then return it.
        row : int
            the instance row index.  Index 0 is the bottom-most row.
        col : int
            the instance column index.  Index 0 is the left-most column.
        layer : int
            the pin layer.  If negative, check to see if the given port has only one layer.
            If so then use that layer.

        Returns
        -------
        pin : Union[WireArray, BBox]
            the first pin associated with the port of given name.
        """
        port = self.get_port(name, row, col)
        return port.get_pins(layer)[0]

    def get_all_port_pins(self, name='', layer=-1):
        # type: (Optional[str], int) -> List[WireArray]
        """Returns a list of all pins of all ports with the given name in this instance array.

        This method gathers ports from all instances in this array with the given name,
        then find all pins of those ports on the given layer, then return as list of WireArrays.

        Parameters
        ----------
        name : Optional[str]
            the port terminal name.  If None or empty, check if this
            instance has only one port, then return it.
        layer : int
            the pin layer.  If negative, check to see if the given port has only one layer.
            If so then use that layer.

        Returns
        -------
        pin_list : List[WireArray]
            the list of pins as WireArrays.
        """
        results = []
        for col in range(self.nx):
            for row in range(self.ny):
                port = self.get_port(name, row, col)
                results.extend(port.get_pins(layer))
        return results

    def port_pins_iter(self, name='', layer=-1):
        # type: (Optional[str], int) -> Iterator[WireArray]
        """Iterate through all pins of all ports with the given name in this instance array.

        Parameters
        ----------
        name : Optional[str]
            the port terminal name.  If None or empty, check if this
            instance has only one port, then return it.
        layer : int
            the pin layer.  If negative, check to see if the given port has only one layer.
            If so then use that layer.

        Yields
        ------
        pin : WireArray
            the pin as WireArray.
        """
        for col in range(self.nx):
            for row in range(self.ny):
                try:
                    port = self.get_port(name, row, col)
                except KeyError:
                    return
                for warr in port.get_pins(layer):
                    yield warr

    def port_names_iter(self):
        # type: () -> Iterable[str]
        """Iterates over port names in this instance.

        Yields
        ------
        port_name : str
            name of a port in this instance.
        """
        return self._master.port_names_iter()

    def has_port(self, port_name):
        # type: (str) -> bool
        """Returns True if this instance has the given port."""
        return self._master.has_port(port_name)

    def has_prim_port(self, port_name):
        # type: (str) -> bool
        """Returns True if this instance has the given primitive port."""
        return self._master.has_prim_port(port_name)

    def transform(self, loc=(0, 0), orient='R0', unit_mode=False, copy=False):
        # type: (Tuple[ldim, ldim], str, bool, bool) -> Optional[Figure]
        """Transform this figure."""
        if not unit_mode:
            res = self.resolution
            loc = int(round(loc[0] / res)), int(round(loc[1] / res))

        if not copy:
            self._loc_unit = loc
            self._orient = orient
            return self
        else:
            return Instance(self._parent_grid, self._lib_name, self._master, self._loc_unit,
                            self._orient, name=self._inst_name, nx=self.nx, ny=self.ny,
                            spx=self.spx_unit, spy=self.spy_unit, unit_mode=True)


class PhotonicRound(Arrayable):
    """A layout round object, with optional arraying parameters.

    Parameters
    ----------
    layer : string or (string, string)
        the layer name, or a tuple of layer name and purpose name.
        If pupose name not given, defaults to 'drawing'.
    rout :
    rin :
    theta0 :
    theta1 :

    nx : int
        number of columns.
    ny : int
        number of rows.
    spx : float
        column pitch.
    spy : float
        row pitch.
    unit_mode : bool
        True if layout dimensions are specified in resolution units.
    """

    def __init__(self,
                 layer,
                 resolution,
                 center,
                 rout,
                 rin=0,
                 theta0=0,
                 theta1=360,
                 nx=1,
                 ny=1,
                 spx=0,
                 spy=0,
                 unit_mode=False,
                 ):
        # python 2/3 compatibility: convert raw bytes to string.
        layer = bag.io.fix_string(layer)
        if isinstance(layer, str):
            layer = (layer, 'phot')
        self._layer = layer[0], layer[1]

        self._res = resolution

        if not unit_mode:
            self._rout_unit = int(round(rout / resolution))
            self._rin_unit = int(round(rin / resolution))
            self._center_unit = (int(round(center[0] / resolution)), int(round(center[1] / resolution)))
        else:
            self._rout_unit = int(round(rout))
            self._rin_unit = int(round(rin))
            self._center_unit = (int(round(center[0])), int(round(center[1])))

        self._theta0 = theta0
        self._theta1 = theta1

        Arrayable.__init__(self, self._res, nx=nx, ny=ny,
                           spx=spx, spy=spy, unit_mode=unit_mode)

    @property
    def rout(self):
        """The outer radius in layout units"""
        return self._rout_unit * self._res

    @property
    def rout_unit(self):
        """The outer radius in resolution units"""
        return self._rout_unit

    @rout.setter
    def rout(self,
             val,  # type: Union[float, int]
             ):
        """Sets the outer radius in layout units"""
        self._rout_unit = int(round(val / self._res))


    @rout_unit.setter
    def rout_unit(self,
                  val,  # type: int
                  ):
        """Sets the outer radius in resolution units"""
        self._rout_unit = int(round(val))

    @property
    def center(self):
        """The center in layout units"""
        return self._center_unit[0] * self._res, self._center_unit[1] * self._res

    @property
    def center_unit(self):
        """The center in resolution units"""
        return self._center_unit

    @center.setter
    def center(self,
               val,  # type: coord_type
               ):
        """Sets the center in layout units"""
        self._center_unit = (int(round(val[0] / self._res)), int(round(val[1] / self._res)))

    @center_unit.setter
    def center_unit(self,
                    val,  # type: coord_type
                    ):
        """Sets the center in resolution units"""
        self._center_unit = (int(round(val[0])), int(round(val[1])))

    @property
    def rin(self):
        """The inner radius in layout units"""
        return self._rin_unit * self._res

    @property
    def rin_unit(self):
        """The inner radius in resolution units"""
        return self._rin_unit

    @rin.setter
    def rin(self,
            val,  # type: Union[float, int]
            ):
        """Sets the inner radius in layout units"""
        self._rin_unit = int(round(val / self._res))

    @rin_unit.setter
    def rin_unit(self,
                 val,  # type: int
                 ):
        """Sets the inner radius in resolution units"""
        self._rin_unit = int(round(val))

    @property
    def theta0(self):
        """The starting angle, in degrees"""
        return self._theta0

    @theta0.setter
    def theta0(self,
               val,  # type: Union[float, int]
               ):
        """Sets the start angle in degrees"""
        self._theta0 = val

    @property
    def theta1(self):
        """The ending angle, in degrees"""
        return self._theta1

    @theta1.setter
    def theta1(self,
               val,  # type: Union[float, int]
               ):
        """Sets the start angle in degrees"""
        self._theta1 = val

    @property
    def layer(self):
        """The rectangle (layer, purpose) pair."""
        return self._layer

    @layer.setter
    def layer(self, val):
        """Sets the rectangle layer."""
        self.check_destroyed()
        # python 2/3 compatibility: convert raw bytes to string.
        val = bag.io.fix_string(val)
        if isinstance(val, str):
            val = (val, 'drawing')
        self._layer = val[0], val[1]
        print("WARNING: USING THIS BREAKS POWER FILL ALGORITHM.")

    @property
    def content(self):
        """A dictionary representation of this rectangle."""
        content = dict(layer=list(self.layer),
                       rout=self.rout,
                       rin=self.rin,
                       theta0=self.theta0,
                       theta1=self.theta1,
                       center=self.center,
                       )
        if self.nx > 1 or self.ny > 1:
            content['arr_nx'] = self.nx
            content['arr_ny'] = self.ny
            content['arr_spx'] = self.spx
            content['arr_spy'] = self.spy

        return content
    
    def move_by(self,
                dx=0,  # type: dim_type
                dy=0,  # type: dim_type
                unit_mode=False,  # type: bool
                ):
        """Moves the round object"""
        if unit_mode:
            self.center_unit = (self.center_unit[0] + int(round(dx)), self.center_unit[1] + int(round(dy)))
        else:
            self.center_unit = (self.center_unit[0] + int(round(dx / self._res)),
                                self.center_unit[1] + int(round(dy / self._res))
                                )

    def transform(self, loc=(0, 0), orient='R0', unit_mode=False, copy=False):
        # type: (Tuple[ldim, ldim], str, bool, bool) -> Optional[Figure]
        """Transform this figure."""

        if not unit_mode:
            loc = int(round(loc[0] / self._res)), int(round(loc[1] / self._res))

        new_center_unit = transform_point(self.center_unit[0], self.center_unit[1], loc=loc, orient=orient)

        if orient == 'R0':
            new_theta0 = self.theta0
            new_theta1 = self.theta1
        elif orient == 'R90':
            new_theta0 = self.theta0 + 90
            new_theta1 = self.theta1 + 90
        elif orient == 'R180':
            new_theta0 = self.theta0 + 180
            new_theta1 = self.theta1 + 180
        elif orient == 'R270':
            new_theta0 = self.theta0 + 270
            new_theta1 = self.theta1 + 270
        elif orient == 'MX':
            new_theta0 = -1 * self.theta1
            new_theta1 = -1 * self.theta0
        elif orient == 'MY':
            new_theta0 = 180 - self.theta1
            new_theta1 = 180 - self.theta0
        elif orient == 'MXR90':
            # MX, then R90
            new_theta0 = -1 * self.theta1 + 90
            new_theta1 = -1 * self.theta0 + 90
        else: # orient == 'MYR90'
            new_theta0 = 180 - self.theta1 + 90
            new_theta1 = 180 - self.theta0 + 90

        if copy:
            print("WARNING: USING THIS BREAKS POWER FILL ALGORITHM.")
            self.center_unit = new_center_unit
            self.theta0 = new_theta0
            self.theta1 = new_theta1
            return self
        else:
            return PhotonicRound(
                layer=self.layer,
                resolution=self.resolution,
                rout=self.rout_unit,
                center=new_center_unit,
                rin=self.rin_unit,
                theta0=new_theta0,
                theta1=new_theta1,
                nx=self.nx,
                ny=self.ny,
                spx=self.spx_unit,
                spy=self.spy_unit,
                unit_mode=True
            )

    @classmethod
    def lsf_export(cls,
                   rout,  # type: dim_type
                   rin,  # type: dim_type
                   theta0,  # type: dim_type
                   theta1,  # type: dim_type
                   layer_prop,
                   center,  # type: coord_type
                   nx=1,  # type: int
                   ny=1,  # type: int
                   spx=0.0,  # type: dim_type
                   spy=0.0,  # type: dim_type
                   ):
        # type: (...) -> List(str)
        """

        Parameters
        ----------
        rout
        rin
        theta0
        theta1
        layer_prop
        center
        nx
        ny
        spx
        spy

        Returns
        -------

        """
        x0, y0 = center[0], center[1]
        lsf_code = []

        if rin == 0:
            for x_count in range(nx):
                for y_count in range(ny):
                    lsf_code.append('\n')
                    lsf_code.append('addcircle;\n')

                    # Set material properties
                    lsf_code.append('set("material", "{}");\n'.format(layer_prop['material']))
                    lsf_code.append('set("alpha", {});\n'.format(layer_prop['alpha']))

                    # Set radius
                    lsf_code.append('set(radius, {});\n'.format(rout))

                    # Compute the x and y coordinates for each rectangle
                    lsf_code.append('set("x", {});\n'.format(x0 + spx * x_count))
                    lsf_code.append('set("y", {});\n'.format(y0 + spy * y_count))

                    # Extract the thickness values from the layermap file
                    lsf_code.append('set("z min", {});\n'.format(layer_prop['z_min']))
                    lsf_code.append('set("z max", {});\n'.format(layer_prop['z_max']))
        else:
            for x_count in range(nx):
                for y_count in range(ny):
                    lsf_code.append('\n')
                    lsf_code.append('addring;\n')

                    # Set material properties
                    lsf_code.append('set("material", "{}");\n'.format(layer_prop['material']))
                    lsf_code.append('set("alpha", {});\n'.format(layer_prop['alpha']))

                    # Set dimensions/angles
                    lsf_code.append('set(outer radius, {});\n'.format(rout))
                    lsf_code.append('set("innter radius", {});\n'.format(rin))
                    lsf_code.append('set("theta start", {});\n'.format(theta0))
                    lsf_code.append('set("theta stop", {});\n'.format(theta1))

                    # Compute the x and y coordinates for each rectangle
                    lsf_code.append('set("x", {});\n'.format(x0 + spx * x_count))
                    lsf_code.append('set("y", {});\n'.format(y0 + spy * y_count))

                    # Extract the thickness values from the layermap file
                    lsf_code.append('set("z min", {});\n'.format(layer_prop['z_min']))
                    lsf_code.append('set("z max", {});\n'.format(layer_prop['z_max']))

        return lsf_code


class PhotonicRect(Rect):
    """
    A layout rectangle, with optional arraying parameters.

    Parameters
    ----------
    layer : string or (string, string)
        the layer name, or a tuple of layer name and purpose name.
        If pupose name not given, defaults to 'drawing'.
    bbox : bag.layout.util.BBox or bag.layout.util.BBoxArray
        the base bounding box.  If this is a BBoxArray, the BBoxArray's
        arraying parameters are used.
    nx : int
        number of columns.
    ny : int
        number of rows.
    spx : float
        column pitch.
    spy : float
        row pitch.
    unit_mode : bool
        True if layout dimensions are specified in resolution units.
    """

    def __init__(self, layer, bbox, nx=1, ny=1, spx=0, spy=0, unit_mode=False):
        if isinstance(layer, str):
            layer = (layer, 'phot')
        Rect.__init__(self, layer, bbox, nx, ny, spx, spy, unit_mode)

    @classmethod
    def lsf_export(cls, bbox, layer_prop, nx=1, ny=1, spx=0.0, spy=0.0) -> List[str]:
        """
        Describes the current rectangle shape in terms of lsf parameters for lumerical use.
        Note that Lumerical uses meters as the base unit, so all coords are multiplied by 1e-6

        Parameters
        ----------
        bbox : [[float, float], [float, float]]
            lower left and upper right corner xy coordinates
        layer_prop : dict
            dictionary containing material properties for the desired layer
        nx : int
            number of arrayed rectangles in the x-direction
        ny : int
            number of arrayed rectangles in the y-direction
        spx : float
            space between arrayed rectangles in the x-direction
        spy : float
            space between arrayed rectangles in the y-direction

        Returns
        -------
        lsf_code : List[str]
            list of str containing the lsf code required to create specified rectangles
        """

        # Calculate the width and length of the rectangle
        x_span = (bbox[1][0] - bbox[0][0]) * 1e-6
        y_span = (bbox[1][1] - bbox[0][1]) * 1e-6

        # Calculate the center of the first rectangle rounded to the nearest nm
        base_x_center = round((bbox[1][0] + bbox[0][0]) / 2, 3) * 1e-6
        base_y_center = round((bbox[1][1] + bbox[0][1]) / 2, 3) * 1e-6

        # Write the lumerical code for each rectangle in the array
        lsf_code = []
        for x_count in range(nx):
            for y_count in range(ny):
                lsf_code.append('\n')
                lsf_code.append('addrect;\n')
                lsf_code.append('set("material", "{}");\n'.format(layer_prop['material']))
                lsf_code.append('set("alpha", {});\n'.format(layer_prop['alpha']))

                # Compute the x and y coordinates for each rectangle
                lsf_code.append('set("x span", {});\n'.format(x_span))
                lsf_code.append('set("x", {});\n'.format(base_x_center + spx * x_count))
                lsf_code.append('set("y span", {});\n'.format(y_span))
                lsf_code.append('set("y", {});\n'.format(base_y_center + spy * y_count))

                # Extract the thickness values from the layermap file
                lsf_code.append('set("z min", {});\n'.format(layer_prop['z_min']))
                lsf_code.append('set("z max", {});\n'.format(layer_prop['z_max']))

        return lsf_code

    @classmethod
    def shapely_export(cls,
                       bbox,  # type: [[int, int], [int, int]]
                       nx=1,  # type: int
                       ny=1,  # type: int
                       spx=0.0,  # type: int
                       spy=0.0,  # type: int
                       ):
        # type: (...) -> Tuple[Union[List[List[Tuple[int, int]]], List[Tuple[int,int]], List], Union[List[List[Tuple[int, int]]], List[Tuple[int,int]], List]]
        """
        Describes the current rectangle shape in terms of lsf parameters for lumerical use

        Parameters
        ----------
        bbox : [[float, float], [float, float]]
            lower left and upper right corner xy coordinates
        nx : int
            number of arrayed rectangles in the x-direction
        ny : int
            number of arrayed rectangles in the y-direction
        spx : float
            space between arrayed rectangles in the x-direction
        spy : float
            space between arrayed rectangles in the y-direction

        Returns
        -------
        lsf_code : List[str]
            list of str containing the lsf code required to create specified rectangles
        """

        # Calculate the width and length of the rectangle

        x_span = bbox[1][0] - bbox[0][0]  # type: int
        y_span = bbox[1][1] - bbox[0][1]  # type: int

        # Calculate the center of the first rectangle rounded to the nearest nm
        x_base = bbox[0][0]  # type: int
        y_base = bbox[0][1]  # type: int

        # Write the lumerical code for each rectangle in the array
        output_list_p = []
        output_list_n = []
        for x_count in range(nx):
            for y_count in range(ny):

                polygon_list = [(x_base + x_count * spx, y_base + y_count * spy),
                                (x_base + x_span + x_count * spx, y_base + y_count * spy),
                                (x_base + x_span + x_count * spx, y_base + y_span + y_count * spy),
                                (x_base + x_count * spx, y_base + y_span + y_count * spy),
                                (x_base + x_count * spx, y_base + y_count * spy)]
                output_list_p.append(polygon_list)

        return (output_list_p, output_list_n)


class PhotonicPath(Path):
    """
    A layout path.  Only 45/90 degree turns are allowed.

    Parameters
    ----------
    resolution : float
        the layout grid resolution.
    layer : string or (string, string)
        the layer name, or a tuple of layer name and purpose name.
        If purpose name not given, defaults to 'drawing'.
    width : float
        width of this path, in layout units.
    points : List[Tuple[float, float]]
        list of path points.
    end_style : str
        the path ends style.  Currently support 'truncate', 'extend', and 'round'.
    join_style : str
        the ends style at intermediate points of the path.  Currently support 'extend' and 'round'.
    unit_mode : bool
        True if width and points are given as resolution units instead of layout units.
    """

    def __init__(self,
                 resolution,  # type: float
                 layer,  # type: Union[str, Tuple[str, str]]
                 width,  # type: Union[int, float]
                 points,  # type: List[Tuple[Union[int, float], Union[int, float]]]
                 end_style='truncate',  # type: str
                 join_style='extend',  # type: str
                 unit_mode=False,  # type: bool
                 ):
        if isinstance(layer, str):
            layer = (layer, 'phot')
        Path.__init__(self, resolution, layer, width, points, end_style, join_style, unit_mode)


class PhotonicPathCollection(PathCollection):
    """
    A layout figure that consists of one or more paths.

    This class make it easy to draw bus/trasmission line objects.

    Parameters
    ----------
    resolution : float
        layout unit resolution.
    paths : List[Path]
        paths in this collection.
    """

    def __init__(self, resolution, paths):
        PathCollection.__init__(self, resolution, paths)


class PhotonicTLineBus(TLineBus):
    """
    A transmission line bus drawn using Path.

    assumes only 45 degree turns are used, and begin and end line segments are straight.

    Parameters
    ----------
    resolution : float
        layout unit resolution.
    layer : Union[str, Tuple[str, str]]
        the bus layer.
    points : List[Tuple[Union[float, int], Union[float, int]]]
        list of center points of the bus.
    widths : List[Union[float, int]]
        list of wire widths.  0 index is left/bottom most wire.
    spaces : List[Union[float, int]]
        list of wire spacings.
    end_style : str
        the path ends style.  Currently support 'truncate', 'extend', and 'round'.
    unit_mode : bool
        True if width and points are given as resolution units instead of layout units.
    """

    def __init__(self, resolution, layer, points, widths, spaces, end_style='truncate',
                 unit_mode=False):
        if isinstance(layer, str):
            layer = (layer, 'phot')
        TLineBus.__init__(self, resolution, layer, points, widths, spaces, end_style, unit_mode)


class PhotonicPolygon(Polygon):
    """
    A layout polygon object.

    Parameters
    ----------
    resolution : float
        the layout grid resolution.
    layer : Union[str, Tuple[str, str]]
        the layer name, or a tuple of layer name and purpose name.
        If purpose name not given, defaults to 'drawing'.
    points : List[Tuple[Union[float, int], Union[float, int]]]
        the points defining the polygon.
    unit_mode : bool
        True if the points are given in resolution units.
    """

    def __init__(self,
                 resolution,  # type: float
                 layer,  # type: Union[str, Tuple[str, str]]
                 points,  # type: List[Tuple[Union[float, int], Union[float, int]]]
                 unit_mode=False,  # type: bool
                 ):
        if isinstance(layer, str):
            layer = (layer, 'phot')
        Polygon.__init__(self, resolution, layer, points, unit_mode)

    @classmethod
    def lsf_export(cls, vertices, layer_prop) -> List[str]:
        """
        Describes the current polygon shape in terms of lsf parameters for lumerical use

        Parameters
        ----------
        vertices : List[Tuple[float, float]]
            ordered list of x,y coordinates representing the points of the polygon
        layer_prop : dict
            dictionary containing material properties for the desired layer

        Returns
        -------
        lsf_code : List[str]
            list of str containing the lsf code required to create specified rectangles
        """
        # Grab the number of vertices in the polygon to preallocate Lumerical matrix size
        poly_len = len(vertices)

        # Write the lumerical code for the polygon
        lsf_code = ['\n',
                    'addpoly;\n',
                    'set("material", "{}");\n'.format(layer_prop['material']),
                    'set("alpha", {});\n'.format(layer_prop['alpha']),

                    # Create matrix to hold vertices, Note that the Lumerical uses meters as the base unit
                    'V = matrix({},2);\n'.format(poly_len),
                    'V(1:{},1) = {};\n'.format(poly_len, [point[0]*1e-6 for point in vertices]),
                    'V(1:{},2) = {};\n'.format(poly_len, [point[1]*1e-6 for point in vertices]),
                    'set("vertices", V);\n',

                    # Set the thickness values from the layermap file
                    'set("z min", {}e-6);\n'.format(layer_prop['z_min']),
                    'set("z max", {}e-6);\n'.format(layer_prop['z_max'])]

        return lsf_code


class PhotonicAdvancedPolygon(Polygon):
    """
    A layout polygon object.

    Parameters
    ----------
    resolution : float
        the layout grid resolution.
    layer : Union[str, Tuple[str, str]]
        the layer name, or a tuple of layer name and purpose name.
        If purpose name not given, defaults to 'drawing'.
    points : List[Tuple[Union[float, int], Union[float, int]]]
        the points defining the polygon.
    unit_mode : bool
        True if the points are given in resolution units.
    """

    def __init__(self,
                 resolution,  # type: float
                 layer,  # type: Union[str, Tuple[str, str]]
                 points,  # type: List[Tuple[Union[float, int], Union[float, int]]]
                 negative_points,  # type: Union[List[coord_type], List[List[coord_type]]]
                 unit_mode=False,  # type: bool
                 ):
        if isinstance(layer, str):
            layer = (layer, 'phot')
        Polygon.__init__(self, resolution, layer, points, unit_mode)
        if not negative_points:
            self._negative_points = []  # TODO: or none?
        elif isinstance(negative_points[0], List):
            self._negative_points = negative_points
        else:
            self._negative_points = [negative_points]


class PhotonicBlockage(Blockage):
    """
    A blockage object.

    Subclass Polygon for code reuse.

    Parameters
    ----------
    resolution : float
        the layout grid resolution.
    block_type : str
        the blockage type.  Currently supports 'routing' and 'placement'.
    block_layer : str
        the blockage layer.  This value is ignored if blockage type is 'placement'.
    points : List[Tuple[Union[float, int], Union[float, int]]]
        the points defining the blockage.
    unit_mode : bool
        True if the points are given in resolution units.
    """

    def __init__(self, resolution, block_type, block_layer, points, unit_mode=False):
        # type: (float, str, str, List[Tuple[Union[float, int], Union[float, int]]], bool) -> None
        Blockage.__init__(self, resolution, block_type, block_layer, points, unit_mode)


class PhotonicBoundary(Boundary):
    """
    A boundary object.

    Subclass Polygon for code reuse.

    Parameters
    ----------
    resolution : float
        the layout grid resolution.
    boundary_type : str
        the boundary type.  Currently supports 'PR', 'snap', and 'area'.
    points : List[Tuple[Union[float, int], Union[float, int]]]
        the points defining the blockage.
    unit_mode : bool
        True if the points are given in resolution units.
    """

    def __init__(self, resolution, boundary_type, points, unit_mode=False):
        # type: (float, str, List[Tuple[Union[float, int], Union[float, int]]], bool) -> None
        Boundary.__init__(self, resolution, boundary_type, points, unit_mode)


class PhotonicViaInfo(ViaInfo):
    """
    A dictionary that represents a layout via.
    """

    param_list = ['id', 'loc', 'orient', 'num_rows', 'num_cols', 'sp_rows', 'sp_cols',
                  'enc1', 'enc2']

    def __init__(self, res, **kwargs):
        ViaInfo.__init__(self, res, **kwargs)


class PhotonicVia(Via):
    """
    A layout via, with optional arraying parameters.

    Parameters
    ----------
    tech : bag.layout.core.TechInfo
        the technology class used to calculate via information.
    bbox : bag.layout.util.BBox or bag.layout.util.BBoxArray
        the via bounding box, not including extensions.
        If this is a BBoxArray, the BBoxArray's arraying parameters are used.
    bot_layer : str or (str, str)
        the bottom layer name, or a tuple of layer name and purpose name.
        If purpose name not given, defaults to 'drawing'.
    top_layer : str or (str, str)
        the top layer name, or a tuple of layer name and purpose name.
        If purpose name not given, defaults to 'drawing'.
    bot_dir : str
        the bottom layer extension direction.  Either 'x' or 'y'.
    nx : int
        arraying parameter.  Number of columns.
    ny : int
        arraying parameter.  Mumber of rows.
    spx : float
        arraying parameter.  Column pitch.
    spy : float
        arraying parameter.  Row pitch.
    extend : bool
        True if via extension can be drawn outside of bounding box.
    top_dir : Optional[str]
        top layer extension direction.  Can force to extend in same direction as bottom.
    unit_mode : bool
        True if array pitches are given in resolution units.
    """

    def __init__(self, tech, bbox, bot_layer, top_layer, bot_dir,
                 nx=1, ny=1, spx=0, spy=0, extend=True, top_dir=None, unit_mode=False):
        Via.__init__(self, tech, bbox, bot_layer, top_layer, bot_dir, nx, ny, spx, spy, extend, top_dir, unit_mode)


class PhotonicPinInfo(PinInfo):
    """
    A dictionary that represents a layout pin.
    """

    param_list = ['net_name', 'pin_name', 'label', 'layer', 'bbox', 'make_rect']

    def __init__(self, res, **kwargs):
        PinInfo.__init__(self, res, **kwargs)