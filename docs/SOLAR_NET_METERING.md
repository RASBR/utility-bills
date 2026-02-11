# Solar / net-metering logic (electricity)

Electricity bills can include bidirectional readings:

- Imported from grid (المستجرة من الشبكة)
- Exported to grid (المصدرة إلى الشبكة)
- Billed quantity (الكمية المفوترة)

Example from your bill:

- Imported current: 16128
- Imported previous: 15364
- Imported difference: 764

- Exported current: 9216
- Exported previous: 8986
- Exported difference: 230

- Billed quantity: 534

Rule:

- import_kwh = import_current - import_previous
- export_kwh = export_current - export_previous
- net_kwh = import_kwh - export_kwh

Typically, billed_kwh ≈ net_kwh.

If export_kwh > import_kwh then net_kwh becomes negative and can be treated as a credit (policy-dependent).
