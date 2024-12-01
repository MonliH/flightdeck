import json

d = {}
with open("output/projects_parsed_deduped.jsonl", "r") as file:
    for line in file:
        data = json.loads(line)
        if data["parsed_content"]["description_markdown"] == "":
            continue

        d[data["project_url"]] = data

with open("output/projects_parsed_final.jsonl", "w") as f:
    for r in d.values():
        f.write(json.dumps(r)+"\n")
