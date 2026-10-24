#!/usr/bin/env python3
"""Conservative, local-only OpenAPI 3.x compatibility audit; zero network calls."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from typing import Any

METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
MAX_DEPTH = 7


class InputError(Exception):
    pass


def read_document(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InputError(f"Cannot read {path}: {exc}") from exc
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        if path.suffix.lower() not in {".yaml", ".yml"}:
            raise InputError(f"Invalid JSON: {path} ({exc})") from exc
        try:
            import yaml
        except ImportError as err:
            raise InputError("YAML needs PyYAML: python -m pip install pyyaml, or export JSON") from err
        try:
            doc = yaml.safe_load(text)
        except yaml.YAMLError as err:
            raise InputError(f"Invalid YAML {path}: {err}") from err
    if not isinstance(doc, dict) or not str(doc.get("openapi", "")).startswith("3."):
        raise InputError(f"{path}: expected an OpenAPI 3.x object")
    if not isinstance(doc.get("paths", {}), dict):
        raise InputError(f"{path}: paths must be an object")
    return doc


def unescape_ref(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def resolve(doc: dict, item: Any, *, depth: int = 0, seen: frozenset[str] = frozenset()) -> Any:
    if depth > MAX_DEPTH or not isinstance(item, dict) or "$ref" not in item:
        return item
    ref = item["$ref"]
    if not isinstance(ref, str) or not ref.startswith("#/") or ref in seen:
        return item  # explicitly do not fetch external/cyclic references
    target: Any = doc
    for part in ref[2:].split("/"):
        if not isinstance(target, dict):
            return item
        target = target.get(unescape_ref(part))
        if target is None:
            return item
    value = resolve(doc, target, depth=depth+1, seen=seen|{ref})
    if isinstance(value, dict) and len(item)>1:
        return {**value, **{key: val for key, val in item.items() if key != "$ref"}}
    return value


def operations(doc: dict) -> dict[tuple[str, str], dict]:
    result: dict[tuple[str, str], dict] = {}
    for path, path_item in doc.get("paths", {}).items():
        path_item = resolve(doc, path_item)
        if not isinstance(path_item, dict):
            continue
        for method in METHODS:
            op = resolve(doc, path_item.get(method, {}))
            if method in path_item and isinstance(op, dict):
                result[path, method] = {**op, "_path_parameters": path_item.get("parameters", [])}
    return result


def params(doc: dict, operation: dict) -> dict[tuple[str, str], dict]:
    entries = (operation.get("_path_parameters") or []) + (operation.get("parameters") or [])
    result: dict[tuple[str, str], dict] = {}
    for entry in entries:
        value = resolve(doc, entry)
        if isinstance(value, dict):
            name, location = value.get("name"), value.get("in")
            if isinstance(name, str) and isinstance(location, str):
                result[name, location] = value  # operation level overrides path level
    return result


def flatten_schema(doc: dict, schema: Any) -> dict:
    item = resolve(doc, schema)
    return item if isinstance(item, dict) else {}


def report_append(findings: list[dict], severity: str, code: str, location: str, explanation: str):
    item = {"severity": severity, "code": code, "location": location, "explanation": explanation}
    if item not in findings:
        findings.append(item)


def compare_request_schema(old_doc: dict, new_doc: dict, old_s: Any, new_s: Any, loc: str,
                           findings: list[dict], depth: int = 0) -> None:
    if depth > MAX_DEPTH:
        return
    old = flatten_schema(old_doc, old_s)
    new = flatten_schema(new_doc, new_s)
    if "$ref" in old or "$ref" in new or any(key in old or key in new for key in ("oneOf", "anyOf", "allOf")):
        report_append(findings, "review", "complex-schema", loc, "Unresolved reference or composed schema: review manually.")
        return
    if old.get("type") and new.get("type") and old["type"] != new["type"]:
        report_append(findings, "review", "request-type-change", loc, f"Request type changed: {old['type']} -> {new['type']}")
    old_values, new_values = old.get("enum"), new.get("enum")
    if isinstance(old_values, list) and isinstance(new_values, list):
        removed = [v for v in old_values if v not in new_values]
        if removed:
            report_append(findings, "breaking", "request-enum-narrowed", loc, f"Previously accepted enum value(s) removed: {removed!r}")
    old_props = old.get("properties", {}) if isinstance(old.get("properties"),dict) else {}
    new_props = new.get("properties", {}) if isinstance(new.get("properties"),dict) else {}
    old_required = set(old.get("required", [])) if isinstance(old.get("required"),list) else set()
    new_required = set(new.get("required", [])) if isinstance(new.get("required"),list) else set()
    for prop in sorted(new_required - old_required):
        report_append(findings, "breaking", "new-required-request-property", f"{loc}.{prop}", "Property is now required in request data.")
    for prop in sorted(old_props.keys() - new_props.keys()):
        if new.get("additionalProperties") is False:
            report_append(findings, "review", "request-property-removed", f"{loc}.{prop}", "Previously documented request property removed and unknown properties disallowed.")
    for prop in sorted(old_props.keys() & new_props.keys()):
        compare_request_schema(old_doc,new_doc,old_props[prop],new_props[prop],f"{loc}.{prop}",findings,depth+1)
    if old.get("items") and new.get("items"):
        compare_request_schema(old_doc,new_doc,old["items"],new["items"],loc+"[]",findings,depth+1)


def compare_response_schema(old_doc: dict,new_doc: dict,old_s: Any,new_s: Any,loc: str,
                            findings: list[dict],depth: int = 0) -> None:
    if depth > MAX_DEPTH: return
    old,new=flatten_schema(old_doc,old_s),flatten_schema(new_doc,new_s)
    if "$ref" in old or "$ref" in new or any(k in old or k in new for k in ("oneOf","anyOf","allOf")):
        report_append(findings,"review","complex-schema",loc,"Unresolved reference or composed schema: review manually.")
        return
    if old.get("type") and new.get("type") and old["type"] != new["type"]:
        report_append(findings,"review","response-type-change",loc,f"Response type changed: {old['type']} -> {new['type']}")
    old_props=old.get("properties",{}) if isinstance(old.get("properties"),dict) else {}
    new_props=new.get("properties",{}) if isinstance(new.get("properties"),dict) else {}
    old_required=set(old.get("required",[])) if isinstance(old.get("required"),list) else set()
    for prop in sorted(old_props.keys()-new_props.keys()):
        sev = "breaking" if prop in old_required else "review"
        report_append(findings,sev,"response-property-removed",f"{loc}.{prop}","Previously documented response property removed.")
    for prop in sorted(old_props.keys() & new_props.keys()):
        compare_response_schema(old_doc,new_doc,old_props[prop],new_props[prop],f"{loc}.{prop}",findings,depth+1)
    if old.get("items") and new.get("items"):
        compare_response_schema(old_doc,new_doc,old["items"],new["items"],loc+"[]",findings,depth+1)
    if isinstance(old.get("enum"),list) and isinstance(new.get("enum"),list):
        extra=[v for v in new["enum"] if v not in old["enum"]]
        if extra:
            report_append(findings,"review","response-enum-expanded",loc,f"New response enum value(s) may affect exhaustive clients: {extra!r}")


def compare(old: dict,new: dict) -> list[dict]:
    findings: list[dict]=[]
    old_ops,new_ops=operations(old),operations(new)
    for path,method in sorted(old_ops.keys()-new_ops.keys()):
        report_append(findings,"breaking","operation-removed",f"{method.upper()} {path}","Previously documented operation removed.")
    for key in sorted(old_ops.keys() & new_ops.keys()):
        path,method=key
        old_op,new_op=old_ops[key],new_ops[key]
        loc=f"{method.upper()} {path}"
        old_params,new_params=params(old,old_op),params(new,new_op)
        for p in sorted(new_params.keys()):
            param=new_params[p]
            if param.get("required",False) and (p not in old_params or not old_params[p].get("required",False)):
                report_append(findings,"breaking","required-parameter-added",f"{loc} {p[1]}:{p[0]}","New required parameter or previously optional parameter now required.")
        for p in sorted(old_params.keys() & new_params.keys()):
            if old_params[p].get("schema") and new_params[p].get("schema"):
                compare_request_schema(old,new,old_params[p]["schema"],new_params[p]["schema"],f"{loc} {p[1]}:{p[0]}",findings)
        old_body=resolve(old,old_op.get("requestBody",{}))
        new_body=resolve(new,new_op.get("requestBody",{}))
        old_body=old_body if isinstance(old_body,dict) else {}
        new_body=new_body if isinstance(new_body,dict) else {}
        if new_body.get("required") and not old_body.get("required"):
            report_append(findings,"breaking","required-body-added",loc,"Request body became required.")
        old_media=old_body.get("content",{}) if isinstance(old_body.get("content"),dict) else {}
        new_media=new_body.get("content",{}) if isinstance(new_body.get("content"),dict) else {}
        for mime in sorted(old_media.keys()-new_media.keys()):
            report_append(findings,"breaking","request-media-removed",f"{loc} request {mime}","Previously accepted request content type removed.")
        for mime in sorted(old_media.keys() & new_media.keys()):
            a,b=old_media[mime],new_media[mime]
            if isinstance(a,dict) and isinstance(b,dict):
                compare_request_schema(old,new,a.get("schema"),b.get("schema"),f"{loc} request {mime}",findings)
        old_res=old_op.get("responses",{}) if isinstance(old_op.get("responses"),dict) else {}
        new_res=new_op.get("responses",{}) if isinstance(new_op.get("responses"),dict) else {}
        for status in sorted(old_res):
            if not (str(status).startswith("2") or status == "default"):
                continue
            if status not in new_res:
                report_append(findings,"breaking" if str(status).startswith("2") else "review","response-status-removed",f"{loc} response {status}","Previously documented successful/default response status removed.")
                continue
            a,b=resolve(old,old_res[status]),resolve(new,new_res[status])
            if not isinstance(a,dict) or not isinstance(b,dict): continue
            ca=a.get("content",{}) if isinstance(a.get("content"),dict) else {}
            cb=b.get("content",{}) if isinstance(b.get("content"),dict) else {}
            for mime in sorted(ca.keys()-cb.keys()):
                report_append(findings,"breaking","response-media-removed",f"{loc} response {status} {mime}","Documented response content type removed.")
            for mime in sorted(ca.keys() & cb.keys()):
                sa,sb=ca[mime],cb[mime]
                if isinstance(sa,dict) and isinstance(sb,dict):
                    compare_response_schema(old,new,sa.get("schema"),sb.get("schema"),f"{loc} response {status} {mime}",findings)
    return findings


def render_md(findings: list[dict], old_file: str, new_file: str) -> str:
    breakers=sum(f["severity"]=="breaking" for f in findings)
    reviews=sum(f["severity"]=="review" for f in findings)
    lines=["# OpenAPI Compatibility Audit", "",f"Old: `{old_file}`  ",f"New: `{new_file}`", "",f"**{breakers} breaking change(s); {reviews} manual-review finding(s).**", ""]
    if not findings:
        return "\n".join(lines+["No changes detected by this conservative rule set.", "", "This is not proof of full compatibility.", ""])
    lines.extend(["| Severity | Rule | Location | Evidence |","|---|---|---|---|"])
    for f in findings:
        safe=lambda s:str(s).replace("|","\\|").replace("\n"," ")
        lines.append(f"| {safe(f['severity'])} | {safe(f['code'])} | {safe(f['location'])} | {safe(f['explanation'])} |")
    lines.extend(["", "Review composed/external schemas and runtime behavior separately; results are static-document checks only.", ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old",type=Path,required=True)
    parser.add_argument("--new",type=Path,required=True)
    parser.add_argument("--format",choices=["markdown","json"],default="markdown")
    parser.add_argument("--out",type=Path,help="Write report to this path; default stdout")
    parser.add_argument("--fail-on",choices=["breaking","any","none"],default="breaking")
    args=parser.parse_args(argv)
    try:
        findings=compare(read_document(args.old),read_document(args.new))
        payload={"old":str(args.old),"new":str(args.new),"summary":{"breaking":sum(f["severity"]=="breaking" for f in findings),"review":sum(f["severity"]=="review" for f in findings)},"findings":findings}
        output=json.dumps(payload,indent=2,ensure_ascii=False)+"\n" if args.format=="json" else render_md(findings,str(args.old),str(args.new))
        if args.out:
            args.out.parent.mkdir(parents=True,exist_ok=True)
            args.out.write_text(output,encoding="utf-8")
        else:
            sys.stdout.write(output)
        fail = (args.fail_on=="any" and len(findings)>0) or (args.fail_on=="breaking" and payload["summary"]["breaking"]>0)
        return 2 if fail else 0
    except (InputError,ValueError) as exc:
        print(f"ERROR: {exc}",file=sys.stderr)
        return 1


if __name__=="__main__":
    sys.exit(main())
