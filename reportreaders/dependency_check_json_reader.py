import json
import pandas as pd

# Leer el JSON
ruta_json = input()
with open(ruta_json, "r", encoding="utf-8") as f:
    data = json.load(f)

# Extraer dependencias
dependencies = data.get("dependencies", [])

# Crear lista para DataFrame
rows = []

for dep in dependencies:
    base_info = {
        "fileName": dep.get("fileName"),
        "filePath": dep.get("filePath"),
        "isVirtual": dep.get("isVirtual"),
    }
    
    vulns = dep.get("vulnerabilities", [])
    if vulns:  # Si hay vulnerabilidades, añadir una fila por cada vulnerabilidad
        for v in vulns:
            row = base_info.copy()
            row.update({
                "vuln_name": v.get("name"),
                "vuln_source": v.get("source"),
                "vuln_severity": v.get("severity"),
                "vuln_description": v.get("description"),
            })
            rows.append(row)
    else:  # Si no hay vulnerabilidades, añadir fila vacía en esos campos
        row = base_info.copy()
        row.update({
            "vuln_name": None,
            "vuln_source": None,
            "vuln_severity": None,
            "vuln_description": None,
        })
        rows.append(row)


df = pd.DataFrame(rows)

vuln_df = df[df["vuln_name"].notnull()]
print(vuln_df[["fileName", "vuln_name", "vuln_severity", "vuln_source"]])
