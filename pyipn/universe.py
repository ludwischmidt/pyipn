import numpy as np
import collections
import yaml
from astropy.time import Time
import astropy.units as u

from .effective_area import EffectiveArea
from .geometry import Pointing, DetectorLocation

from .grb import GRB
from .detector import Detector


class Universe(object):
    def __init__(self, grb):
        """FIXME! briefly describe function

        :param grb: 
        :returns: 
        :rtype: 

        """

        self._detectors = collections.OrderedDict()
        self._grb = grb

        self._time_differences = None
        self._T0 = None
        self._light_curves = None

    def register_detector(self, detector):
        """FIXME! briefly describe function

        :param detector: 
        :returns: 
        :rtype: 

        """

        self._detectors[detector.name] = detector

    @property
    def detectors(self):
        return self._detectors

    @property
    def light_curves(self):
        return self._light_curves

    def explode_grb(self, tstart, tstop, verbose=True):
        """FIXME! briefly describe function

        :param verbose: 
        :returns: 
        :rtype: 

        """

        self._compute_time_differences()

        self._create_light_curves(tstart, tstop)

    def _compute_time_differences(self):
        """FIXME! briefly describe function

        :returns: 
        :rtype: 

        """

        # compute which detector sees the GRB first
        ltt = []
        for name, detector in self._detectors.items():

            ltt.append(detector.angular_separation(self._grb).value)

        # rank the distances in ascending order
        self._distance_rank = np.argsort(ltt)
        unsort = self._distance_rank.argsort()

        # for now compute considering all detectors are static
        # the TOA difference of each detector
        ltt = np.array(ltt)[self._distance_rank]

        self._time_differences = [0.0]
        self._T0 = [0.0]
        T0 = 0.0
        for i in range(len(ltt) - 1):

            dt = ltt[i + 1] - ltt[i]
            assert (
                dt > 0
            ), "The time diferences should be positive if the ranking worked!"

            T0 += dt
            self._T0.append(T0)
            self._time_differences.append(dt)

        self._T0 = np.array(self._T0)
        self._time_differences = np.array(self._time_differences)

        self._T0 = self._T0[unsort]
        self._time_differences[unsort]

    def _create_light_curves(self, tstart, tstop):
        """FIXME! briefly describe function

        :returns: 
        :rtype: 

        """

        self._light_curves = collections.OrderedDict()

        for t0, (name, detector) in zip(self._T0, self._detectors.items()):

            self._light_curves[name] = detector.build_light_curve(
                self._grb, t0, tstart, tstop
            )

    @classmethod
    def from_yaml(cls, yaml_file):
        """
        Create a universe from a yaml file

        :param cls: 
        :param yaml_file: 
        :returns: 
        :rtype: 

        """

        with open(yaml_file, "r") as f:

            setup = yaml.load(f, Loader=yaml.SafeLoader)

            grb_params = setup["grb"]

            grb = GRB(
                grb_params["ra"],
                grb_params["dec"],
                grb_params["distance"] * u.Mpc,
                grb_params["K"],
                grb_params["t_rise"],
                grb_params["t_decay"],
            )

            universe = cls(grb)

            for name, value in setup["detectors"].items():

                eff_area = EffectiveArea(value["effective_area"])

                time = Time(value["time"])

                location = DetectorLocation(
                    value["ra"], value["dec"], value["altitude"] * u.km, time
                )

                pointing = Pointing(value["pointing"]["ra"], value["pointing"]["dec"])

                det = Detector(location, pointing, eff_area, name)

                universe.register_detector(det)

            return universe