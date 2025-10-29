import json
import pandas as pd

report = input()
# Cargar el JSON de Trivy
with open(report, "r") as f:
    data = json.load(f)

vuln_rows = []

# Recorrer Results y extraer vulnerabilidades
for result in data.get("Results", []):
    target = result.get("Target")
    vulns = result.get("Vulnerabilities", [])
    
    for v in vulns:
        vuln_rows.append({
            "Target": target,
            "VulnerabilityID": v.get("VulnerabilityID"),
            "PkgName": v.get("PkgName"),
            "InstalledVersion": v.get("InstalledVersion"),
            "FixedVersion": v.get("FixedVersion"),
            "Severity": v.get("Severity"),
            "Title": v.get("Title"),
        })

# Crear DataFrame
df = pd.DataFrame(vuln_rows)

print(df)
