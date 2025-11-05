# SignNow Integration

## Goals
- Fill and send Intake/Retainer packets directly from staged data.
- Track `packet_status`, `packet_url`, `signed_at` back in Sheets.

## Checklist
- SignNow API key + team ID
- Template IDs for Intake, Retainer
- Drive folder for outputs
- Apps Script web app published (access: only your workspace)

## API Steps (Apps Script)
1. Exchange API key for bearer token (if required).
2. Create document from template.
3. Prefill fields using your field map.
4. Invite signer(s) (client & agent, if needed).
5. Poll document status or webhook (preferred).
6. On completion:
   - Download final PDF to Drive.
   - Update row in Google Sheet.

## Field Mapping Tips
- Keep field names in **config/signnow.json**:
```json
{
  "templates": {
    "intake": "TEMPLATE_ID_1",
    "retainer": "TEMPLATE_ID_2"
  },
  "map": {
    "client_first_name": "first_name",
    "client_last_name": "last_name",
    "dob": "dob",
    "phone": "phone",
    "email": "email",
    "primary_charge": "charge_1",
    "total_bond": "total_bond",
    "booking_id": "booking_id",
    "county": "county",
    "case_number": "case_number"
  }
}
