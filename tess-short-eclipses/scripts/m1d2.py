"""Narrow offline ancillary-metadata adapter; original numeric decoder unchanged."""

import hashlib
import importlib.util
import os
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def original():
    spec = importlib.util.spec_from_file_location("m1d2_preserved_base", ROOT / "scripts/m1d.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = original()
NS = BASE.NS
MANIFEST = ROOT / "out/m1d2-manifest.json"
SERVICE = "https://gaia.ari.uni-heidelberg.de/datalink/gaiadr3"


def adapt(content):
    if len(content) > 5_000_000 or b"<!DOCTYPE" in content or b"<!ENTITY" in content:
        raise ValueError("STOP_XML_BOUND_OR_DECLARATION")
    text = content.decode("utf-8")
    if "\x00" in text:
        raise ValueError("STOP_XML_ENCODING")
    # Preserve the original declaration's validation before ElementTree rewrites it.
    declaration = BASE.re.match(r"\ufeff?<\?xml\s.*?\?>", text, flags=BASE.re.DOTALL)
    if declaration:
        encoding = BASE.re.search(r"encoding\s*=\s*(['\"])(.*?)\1", declaration.group())
        if encoding and encoding.group(2).lower().replace("-", "") != "utf8":
            raise ValueError("STOP_XML_ENCODING")
    root = ET.fromstring(text)
    if any(not node.tag.startswith(NS) for node in root.iter()):
        raise ValueError("STOP_FOREIGN_NAMESPACE")
    resources = root.findall(".//" + NS + "RESOURCE")
    if len(resources) != 2 or any(node not in list(root) for node in resources):
        raise ValueError("STOP_SERVICE_RESOURCES")
    results = [node for node in resources if node.get("type") == "results"]
    metadata = [node for node in resources if node.get("type") == "meta"]
    if len(results) != 1 or len(metadata) != 1:
        raise ValueError("STOP_SERVICE_RESOURCES")
    descriptor = metadata[0]
    if descriptor.attrib != {"type": "meta", "utype": "adhoc:service", "name": "Datalink_GaiaDR3"}:
        raise ValueError("STOP_SERVICE_PROFILE")
    if [node.tag for node in descriptor] != [NS + tag for tag in ("DESCRIPTION", "PARAM", "GROUP")]:
        raise ValueError("STOP_SERVICE_CHILDREN")
    description, access, group = descriptor
    if description.attrib or len(description):
        raise ValueError("STOP_SERVICE_DESCRIPTION")
    if access.attrib != {"arraysize": "51", "datatype": "char", "name": "accessURL",
                         "ucd": "meta.ref.url", "value": SERVICE}:
        raise ValueError("STOP_SERVICE_URL_PROFILE")
    if len(access) != 1 or access[0].tag != NS + "DESCRIPTION" or access[0].attrib or len(access[0]):
        raise ValueError("STOP_SERVICE_URL_DESCRIPTION")
    if group.attrib != {"name": "inputParams"} or len(group) != 1:
        raise ValueError("STOP_SERVICE_INPUTS")
    parameter = group[0]
    if (parameter.tag != NS + "PARAM" or len(parameter)
            or parameter.attrib != {"name": "sourceid", "datatype": "long", "ref": "source_id", "value": ""}):
        raise ValueError("STOP_SERVICE_REFERENCE")
    ids = root.findall(".//*[@ID='source_id']")
    if len(ids) != 1 or ids[0].tag != NS + "FIELD" or ids[0].get("name") != "source_id":
        raise ValueError("STOP_SERVICE_REFERENCE")
    statuses = root.findall(".//" + NS + "INFO[@name='QUERY_STATUS']")
    if not statuses or any(node.get("value") != "OK" for node in statuses):
        raise ValueError("STOP_QUERY_STATUS")
    descriptor_bytes = ET.tostring(descriptor, encoding="utf-8")
    result_bytes = ET.tostring(results[0], encoding="utf-8")
    root.remove(descriptor)
    if ET.tostring(results[0], encoding="utf-8") != result_bytes:
        raise ValueError("STOP_RESULTS_CHANGED")
    sanitized = ET.tostring(root, encoding="utf-8")
    return sanitized, {"ignored_service_url_not_fetched": SERVICE,
                       "descriptor_sha256": hashlib.sha256(descriptor_bytes).hexdigest(),
                       "derived_xml_sha256": hashlib.sha256(sanitized).hexdigest(),
                       "original_results_subtree_unchanged": True}


def decode(content):
    sanitized, _ = adapt(content)
    return BASE.validate(BASE.decode(sanitized))


def dependencies():
    preserved = original()
    if preserved.dependencies() != preserved.OLD.read_json(preserved.MANIFEST)["dependencies"]:
        raise ValueError("STOP_M1D_PROVENANCE")
    if preserved.OLD.read_json(preserved.RESULT).get("error") != "STOP_TABLE_STRUCTURE":
        raise ValueError("STOP_M1D_OUTCOME")
    paths = [Path(__file__), ROOT / "M1d2-PROTOCOL-2026-09-12.md", ROOT / "tests/test_m1d2.py",
             ROOT / "tests/test_m1d2_review.py",
             ROOT / "scripts/m1d.py", preserved.MANIFEST, preserved.RESULT,
             ROOT / "out/m1d-worker-outcome.json", BASE.ARI, BASE.OLD.REFERENCE]
    return {os.path.relpath(path, ROOT).replace("\\", "/"): BASE.OLD.m1.sha(path) for path in paths}


def execute():
    if BASE.OLD.read_json(MANIFEST)["dependencies"] != dependencies():
        raise ValueError("STOP_MANIFEST_CHANGED")
    result = {"manifest_sha256": BASE.OLD.m1.sha(MANIFEST), "network_requests": 0,
              "pixel_recalculation": False, "unknown_search_authorized": False}
    try:
        sanitized, metadata = adapt(BASE.ARI.read_bytes())
        mirror = BASE.validate(BASE.decode(sanitized))
        parity = BASE.OLD.compare_tables(BASE.OLD.strict_catalog(BASE.OLD.REFERENCE), mirror)
    except (ValueError, ET.ParseError, OSError) as error:
        result.update(status="STOP_M1D2", error_type=type(error).__name__, error=str(error))
    else:
        result.update(status="OFFLINE_CATALOG_PARITY_PASS", parity=parity, metadata=metadata,
                      numeric_decoders="unchanged_m1d_struct_and_numpy", rows=len(mirror))
    return result


def main():
    # Isolated module globals only. Original source, protocol and receipts are immutable.
    for name in ("MANIFEST", "RESULT", "ATTEMPT", "WORKER_START", "OUTCOME"):
        setattr(BASE, name, Path(str(getattr(BASE, name)).replace("m1d-", "m1d2-")))
    BASE.__file__ = __file__
    BASE.dependencies = dependencies
    BASE.execute = execute
    # The old harness has one literal runtime path: redirect its save call only.
    save = BASE.OLD.m1.save

    def stage_save(path, value):
        if path == ROOT / "out/m1d-runtime.json":
            path = ROOT / "out/m1d2-runtime.json"
        return save(path, value)

    BASE.OLD.m1.save = stage_save
    try:
        BASE.main()
    finally:
        BASE.OLD.m1.save = save


if __name__ == "__main__":
    main()
