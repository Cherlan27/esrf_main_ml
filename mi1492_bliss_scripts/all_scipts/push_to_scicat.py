from ewoksjob.client import submit
import json

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
      "counter_name": "roi2",
      "scans": [
        "1"
      ]
    },
    "calibration": {
      "energy": {
        "unit": "keV",
        "value": 17,
        "valueSI": 2.7237001605e-15,
        "unitSI": "(kg m^2) / s^2"
      },
      "central_pixel_x": 1,
      "central_pixel_y": 2,
      "incidence_angle": {
        "unit": "deg",
        "unitSI": "deg"
      },
      "calibration_file": ""
    },
    "beamtime": {
      "beamtime_id": "ihsc1612",
      "date_start": "2018-12-09",
      "date_end": "2018-12-10",
      "title": "id03 inhouse"
    },
    "participants": [
      {
        "name": "Linus Pithan",
        "orcid": "0000-0002-6080-3273"
      }
    ],
    "local_contact": [
      {
        "name": "Alessandro Mariani",
        "email": "",
        "instument": "id02",
        "orcid": ""
      }
    ],
    "dataset_comment": {
      "comment": "a comment"
    }}
  """
template = json.loads(template_json)

inputs = [
    {"task_identifier": "SciCat", "name": "scientific_metadata", "value": json.dumps(template)},
    {
        "task_identifier": "SciCat",
        "name": "dataset_name",
        "value": "AI realtime prediction",
    },
    {
        "task_identifier": "SciCat",
        "name": "description",
        "value": "Filmthickness 39 monolayer",
    },
    {"task_identifier": "SciCat", "name": "source_folder", "value": "/path/to/data"},
]

nodes = [{"id": "scicat", "task_type": "class", "task_identifier": "tasks.SciCat"}]

workflow = {"graph": {"id": "scicat_graph"}, "nodes": nodes}
future = submit(args=(workflow,), kwargs={"inputs": inputs})
