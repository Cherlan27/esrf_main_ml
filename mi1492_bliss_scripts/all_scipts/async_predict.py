from dataclasses import dataclass
import numpy as np
from io import BytesIO
import json
from ewoksjob.client import submit

from bliss.scanning.group import Sequence
from bliss.common import tango
from bliss.data.node import get_session_node, get_node
from bliss.scanning.chain import AcquisitionChannel

# from bliss.scanning.scan_meta import USER_SCAN_META
import gevent
from pprint import pprint
from bliss.config.channels import Channel

# if "xrr" not in USER_SCAN_META.categories_names():
#    USER_SCAN_META.add_categories({"xrr"})
#    USER_SCAN_META.xrr.set("xrr", {"@NX_class": "NXprocess"})
from bliss.config.channels import Channel

last_film_thickness = Channel("last_film_thickness", default_value=None)

PARAMETER_NAMES = [
    "d_full_rel",
    "rel_sigmas",
    "dr_sigmoid_rel_pos",
    "dr_sigmoid_rel_width",
    "d_block1_rel",
    "d_block",
    "s_block_rel",
    "r_block",
    "dr",
    "d3_rel",
    "s3_rel",
    "r3",
    "d_sio2",
    "s_sio2",
    "s_si",
    "r_sio2",
    "r_si",
]


@dataclass
class Priors:
    d_top: tuple = (0.0, 1000.0)  # (0., 1000.)
    d_sio2: tuple = (10.0, 30.0)

    sigma_top: tuple = (0.0, 50.0)  # (0., 50.)
    sigma_sio2: tuple = (
        0.0,
        10.0,
    )
    sigma_si: tuple = (
        0.0,
        2.0,
    )

    rho_top: tuple = (7.0, 14.0)
    rho_sio2: tuple = (19, 23)
    rho_si: tuple = (19, 21)
    max_d_change: float = 5.0
    fit_growth: bool = True

    def to_arr(self):
        return np.array(
            [
                self.d_top,
                self.d_sio2,
                self.sigma_top,
                self.sigma_sio2,
                self.sigma_si,
                self.rho_top,
                self.rho_sio2,
                self.rho_si,
            ]
        )


@dataclass
class PreprocessParams:
    energy_keV: float = 17.0
    beam_width: float = 0.03
    sample_length: float = 9.0
    # max_angle: float = None


def listen_scans_of_session(session):
    session_node = get_session_node(session)
    print(f"Listening to {session}")

    received_scans = []
    for event_type, node, event_data in session_node.walk_on_new_events(
        include_filter=["scan"]  # ,"scan_group"]
    ):

        if event_type == event_type.NEW_NODE:
            print(f"new scan", node.db_name)

        elif event_type == event_type.END_SCAN:
            print(node.db_name)

            params = node.info.get("fastfit")
            if params.get("xrr_scan_group_first", False):
                received_scans = [node]
                print("add scan")
            if params.get("xrr_scan_group_last", False):
                received_scans.append(node)
                print("add scan and process")
                process_scans(received_scans)


def process_scans(scans):

    print("start processing", scans)

    counter_names = [
        "axis:gam",
        "pilatus300k:roi_counters:roi2_sum",
        "pilatus300k:roi_counters:roi3_sum",
        "pilatus300k:roi_counters:roi4_sum",
        # 'autof_eh1:transm'
    ]
    data = list()

    data = dict()
    scans_names = list()
    transm = []
    for k in counter_names:
        data[k] = list()

    for scan in scans:
        scans_names.append(scan.db_name)
        shape = None  # have a place for the shape of the channel
        for node in scan.walk(wait=False, include_filter="channel"):

            if node.name in data:
                tmp = node.get_as_array(0, -1)
                print(node.name, type(data[node.name]), type(tmp))
                data[node.name].append(tmp)
                shape = len(tmp)  # remove tmp and use shape of channel instead

        # deal with transm in fast scans...
        transm.append(np.ones(shape) * scan.info.get("fastfit")["watt0"])
    data["autof_eh1:transm"] = transm

    for k, v in data.items():
        data[k] = np.concatenate(v)

    # still to deal with transmission
    tth_data = data["axis:gam"]
    intensity_data = (
        data["pilatus300k:roi_counters:roi2_sum"]
        - data["pilatus300k:roi_counters:roi3_sum"]
        - data["pilatus300k:roi_counters:roi4_sum"]
    )
    transm_data = data["autof_eh1:transm"]
    prediction = get_triton_prediction(tth_data, intensity_data, transm_data)
    # thickness = predict_and_save_on_array(tth_data, transm_data, intens_data,scans=scans)

    thickness = prediction["parameters_polished"][0]

    last_film_thickness.value = thickness

    print("######### predicted thickness", thickness)

    polished_params = prediction["parameters_polished"]
    param_names = PARAMETER_NAMES

    info={"xrr":dict(zip(param_names, polished_params))}
    
    #### now to scicat
    print("SCICAT")
    scicat_push(info,scans_names)

    # ~ seq = Sequence(
        # ~ title=f"AI_fit_thickness_{polished_params[0]:.3f} Monolayer"
      # ~ ,scan_info=info)
    # ~ seq.add_custom_channel(AcquisitionChannel("raw_tth", float, ()))
    # ~ seq.add_custom_channel(AcquisitionChannel("corrected_intensity", float, ()))
    # ~ seq.add_custom_channel(AcquisitionChannel("raw_q", float, ()))
    # ~ seq.add_custom_channel(AcquisitionChannel("predicted_intensity", float, ()))
    # ~ seq.add_custom_channel(AcquisitionChannel("predicted_q", float, ()))
    # ~ seq.add_custom_channel(AcquisitionChannel("params", float, ()))
    # ~ seq.add_custom_channel(AcquisitionChannel("params_names", str, ()))
    # ~ seq.add_custom_channel(AcquisitionChannel("polished_intensity", float, ()))
    # ~ seq.add_custom_channel(AcquisitionChannel("polished_params", float, ()))
    # ~ with seq.sequence_context() as scan_seq:

        # ~ seq.custom_channels["raw_tth"].emit(tth_data)
        # ~ seq.custom_channels["corrected_intensity"].emit(intensity_data)
        # ~ seq.custom_channels["raw_q"].emit(prediction["q"])
        # ~ seq.custom_channels["predicted_intensity"].emit(prediction["refl_predicted"])
        # ~ seq.custom_channels["params"].emit(prediction["parameters"])
        # ~ seq.custom_channels["params_names"].emit(param_names)
        # ~ seq.custom_channels["polished_intensity"].emit(
            # ~ prediction["refl_predicted_polished"]
        # ~ )
        # ~ seq.custom_channels["polished_params"].emit(polished_params)



def get_triton_prediction(
    tth,
    intensity,
    transm,
    beam_width=0.03,
    sample_length=10,
    wavelength=0.7293,
    max_d_change=5,
):
    def numpy_serialize(a):
        memfile = BytesIO()
        np.save(memfile, a)
        serialized = memfile.getvalue()
        return json.dumps(serialized.decode("latin-1"))

    @dataclass
    class Priors:
        d_top: tuple = (0.0, 1000.0)  # (0., 1000.)
        d_sio2: tuple = (10.0, 30.0)

        sigma_top: tuple = (0.0, 50.0)  # (0., 50.)
        sigma_sio2: tuple = (
            0.0,
            10.0,
        )
        sigma_si: tuple = (
            0.0,
            2.0,
        )

        rho_top: tuple = (7.0, 14.0)
        rho_sio2: tuple = (19, 23)
        rho_si: tuple = (19, 21)
        max_d_change: float = 5.0
        fit_growth: bool = True

        def to_arr(self):
            return np.array(
                [
                    self.d_top,
                    self.d_sio2,
                    self.sigma_top,
                    self.sigma_sio2,
                    self.sigma_si,
                    self.rho_top,
                    self.rho_sio2,
                    self.rho_si,
                ]
            )

    priors = numpy_serialize(Priors().to_arr())

    inputs = [
        {
            "task_identifier": "TritonInference",
            "name": "tth",
            "value": numpy_serialize(tth),
        },
        {
            "task_identifier": "TritonInference",
            "name": "intensity",
            "value": numpy_serialize(intensity),
        },
        {
            "task_identifier": "TritonInference",
            "name": "transm",
            "value": numpy_serialize(transm),
        },
        {
            "task_identifier": "TritonInference",
            "name": "beam_width",
            "value": numpy_serialize(np.array([beam_width])),
        },
        {
            "task_identifier": "TritonInference",
            "name": "sample_length",
            "value": numpy_serialize(np.array([sample_length])),
        },
        {
            "task_identifier": "TritonInference",
            "name": "wavelength",
            "value": numpy_serialize(np.array([wavelength])),
        },
        {
            "task_identifier": "TritonInference",
            "name": "max_d_change",
            "value": numpy_serialize(np.array([max_d_change])),
        },
        {"task_identifier": "TritonInference", "name": "priors", "value": priors},
    ]

    nodes = [
        {
            "id": "triton",
            "task_type": "class",
            "task_identifier": "tasks.TritonInference",
        }
    ]

    workflow = {"graph": {"id": "triton_graph"}, "nodes": nodes}
    future = submit(args=(workflow,), kwargs={"inputs": inputs})

    return future.get()
    
def scicat_push(prediction,scan_names):
    
    template_json = """
   {
    "measurement": {
      "measurement_type": "beamtime"
    },
    "logbook": {
      "logbook_file": "esrf elog",
      "logbook_pages": "mi1462"
    },
    "XRR": {
      "counter_name": "pilatus:roi2"
    },
    "calibration": {
      "energy": {
        "unit": "keV",
        "value": 17,
        "valueSI": 2.7237001605e-15,
        "unitSI": "(kg m^2) / s^2"
      },
      "central_pixel_x": 227,
      "central_pixel_y": 492,
      "incidence_angle": {
        "unit": "deg",
        "unitSI": "deg"
      },
      "calibration_file": ""
    },
    "beamtime": {
      "beamtime_id": "ihsc1612",
      "date_start": "2023-02-28",
      "date_end": "2023-03-06",
      "title": "mi1462"
    },
    "participants": [
      {
        "name": "Linus Pithan",
        "orcid": "0000-0002-6080-3273"
      },
      {
        "name": "Stefan Kowarik"
      },
      {
        "name": "Constantin Voelter"
      },
      {
        "name": "Vladimir Starostin"
      },
      {
        "name": "David Marecek"
      },
      {
        "name": "Lukas Petersdorf"
      }
    ],
    "local_contact": [
      {
        "name": "Maciej Jankowski",
        "email": "",
        "instument": "ID10",
        "orcid": ""
      },
      {
        "name": "Oleg Konovalov",
        "email": "",
        "instument": "ID10",
        "orcid": ""
      }
    ],
    "dataset_comment": {
      "comment": "measured and ingested on the last night of the beamtime"
    }}
  """
    template = json.loads(template_json)
    
    for k,v in prediction["xrr"].items():
        prediction["xrr"][k]=float(v)
    
    template["AI_realtime_fit"]=prediction
    inputs = [
        {"task_identifier": "SciCat", "name": "scientific_metadata", "value": json.dumps(template)},
        {
            "task_identifier": "SciCat",
            "name": "dataset_name",
            "value": f"XRR Multilayer real time fit: Film thickness:{prediction['xrr']['d_full_rel']:.3f} monolayer",
        },
        {
            "task_identifier": "SciCat",
            "name": "description",
            "value": "Fitted with multilayer_2_2 model (version 2023-03-05)",
        },
        {"task_identifier": "SciCat", "name": "source_folder", "value": str([s.replace(":","/")+".h5" for s in scan_names])},
    ]

    nodes = [{"id": "scicat", "task_type": "class", "task_identifier": "tasks.SciCat"}]

    workflow = {"graph": {"id": "scicat_graph"}, "nodes": nodes}
    future = submit(args=(workflow,), kwargs={"inputs": inputs})

    # ~ from bliss.scanning.group import Sequence
    # ~ EH1_OPTICS [1]: seq = Sequence(title="test_seq")                                                                                                                                         │·························
    # ~ ...: with seq.sequence_context() as scan_seq:                                                                                                                                 │·························
    # ~ ...:     scan_seq.add(loopscan(3,.1,simdiode1))                                                                                                                               │·························
    # ~ ...:     scan_seq.add(loopscan(5,.1,simdiode1))

    ##call predict and save

    # return grouped_scans


# ~ node.get_as_array(self.channel_indices[node.name], -1)
# ~ self.scan_node.info.get(key)
# ~ self.scan_node.info.get_all()
# dealing with node_ref_channel
#    elif event_type == event_type.NEW_NODE and node.type == "node_ref_channel"
# ~ def get_thickness_from_params(p, use_mlreflect: bool = False):

# ~ thickness = p['d_full_rel']
# ~ return thickness


# ~ TTH = "gam"
# ~ CROI = 'pilatus300k:roi_counters:roi2_sum'
# ~ BGROI1 = 'pilatus300k:roi_counters:roi3_sum'
# ~ BGROI2 = 'pilatus300k:roi_counters:roi4_sum'
# ~ TRANSM = 'autof_eh1:transm'


# ~ tth_data = np.concatenate(np.array([x.get_data(TTH) for x in scans]))
# ~ if fscan:
# ~ transm_data =  np.concatenate(np.array([np.ones(x.get_data(TTH).shape)*x.scan_info["instrument"]["filtW0"]["transmission"] for x in scans]))
# ~ else:
# ~ transm_data = np.concatenate(np.array([x.get_data(TRANSM) for x in scans]))
# ~ intens_data = np.concatenate(np.array([x.get_data(CROI) - x.get_data(BGROI1) - x.get_data(BGROI2) for x in scans]))

# ~ return predict_and_save_on_array(tth_data, transm_data, intens_data, scans=scans, priors=priors, preprocess=preprocess,
# ~ tango_uri_or_proxy=tango_uri_or_proxy)  # ,exp_energy_in_keV=exp_energy_in_keV,footprint_beam_width=footprint_beam_width,footprint_sample_length=footprint_sample_length)
