# n8n Integration Guide

Quick start guide for integrating the Grid Image Generator with n8n workflows.

## Quick Start

### 1. Start the HTTP Server

**Option A: Using Docker (Recommended)**
```bash
docker-compose -f docker-compose.http.yml up -d
```

**Option B: Using Python**
```bash
pip install -r requirements.txt
python mcp_http_server.py
```

The server will be available at `http://localhost:8000`

### 2. Create n8n Workflow

#### Step-by-Step:

1. **Add a Trigger Node** (Webhook, Schedule, Manual, etc.)

2. **Add HTTP Request Node**
   - **Name:** Generate Grid Image
   - **Method:** POST
   - **URL:** `http://localhost:8000/generate`
   - **Authentication:** None (or add if you've secured the API)
   - **Send Headers:** Yes
     - **Header Name:** `Content-Type`
     - **Header Value:** `application/json`
   - **Send Body:** Yes
   - **Body Content Type:** JSON
   - **Specify Body:** Using JSON
   - **JSON Body:**
     ```json
     {
       "grid_data": {
         "T_Date": "{{ $json.date }}",
         "T_00": "{{ $json.hour_00 || '●' }}",
         "T_01": "{{ $json.hour_01 || '●' }}",
         "T_02": "{{ $json.hour_02 || '●' }}",
         "T_03": "{{ $json.hour_03 || '●' }}",
         "T_04": "{{ $json.hour_04 || '●' }}",
         "T_05": "{{ $json.hour_05 || '●' }}",
         "T_06": "{{ $json.hour_06 || '✕' }}",
         "T_07": "{{ $json.hour_07 || '✕' }}",
         "T_08": "{{ $json.hour_08 || '✕' }}",
         "T_09": "{{ $json.hour_09 || '✕' }}",
         "T_10": "{{ $json.hour_10 || '✕' }}",
         "T_11": "{{ $json.hour_11 || '✕' }}",
         "T_12": "{{ $json.hour_12 || '✕' }}",
         "T_13": "{{ $json.hour_13 || '●' }}",
         "T_14": "{{ $json.hour_14 || '●' }}",
         "T_15": "{{ $json.hour_15 || '●' }}",
         "T_16": "{{ $json.hour_16 || '%' }}",
         "T_17": "{{ $json.hour_17 || '✕' }}",
         "T_18": "{{ $json.hour_18 || '✕' }}",
         "T_19": "{{ $json.hour_19 || '✕' }}",
         "T_20": "{{ $json.hour_20 || '✕' }}",
         "T_21": "{{ $json.hour_21 || '✕' }}",
         "T_22": "{{ $json.hour_22 || '✕' }}",
         "T_23": "{{ $json.hour_23 || '%' }}"
       },
       "return_base64": false
     }
     ```

3. **Add Response Node** (based on your needs):
   - **Save to File:** Use "Write Binary File" node
   - **Send Email:** Use "Gmail" or "Send Email" node with attachment
   - **Upload to Cloud:** Use "Google Drive", "Dropbox", etc.
   - **Return in Webhook:** Use "Respond to Webhook" node

## Example Workflows

### Workflow 1: Generate and Save Image

```
[Webhook] → [HTTP Request] → [Write Binary File]
```

**Write Binary File Node:**
- **File Name:** `grid_availability_{{ $json.date }}.png`
- **Data:** `{{ $binary.data }}`
- **File Path:** `/path/to/save/`

### Workflow 2: Generate and Send via Email

```
[Schedule] → [HTTP Request] → [Gmail] or [Send Email]
```

**Gmail/Send Email Node:**
- **To:** recipient@example.com
- **Subject:** Grid Availability Report - {{ $json.date }}
- **Attachments:** 
  - **Name:** `grid_availability.png`
  - **Data:** `{{ $binary.data }}`

### Workflow 3: Generate from Database and Store

```
[PostgreSQL] → [HTTP Request] → [Google Drive]
```

1. **PostgreSQL Node:** Query grid data
2. **HTTP Request Node:** Generate image
3. **Google Drive Node:** Upload image

## Using Base64 Response

If you prefer base64 encoding:

1. Set `return_base64: true` in the HTTP Request body
2. Use a **Function Node** to convert base64 to binary:

```javascript
// Function Node Code
const base64Data = $input.item.json.image_base64;
const buffer = Buffer.from(base64Data, 'base64');

return [{
  json: $input.item.json,
  binary: {
    data: buffer
  }
}];
```

3. Then use the binary data in subsequent nodes

## Dynamic Data Mapping

### From Previous Node Data

If your trigger provides grid data:

```json
{
  "grid_data": {
    "T_Date": "{{ $json.date }}",
    "T_00": "{{ $json.hours[0] }}",
    "T_01": "{{ $json.hours[1] }}",
    // ... etc
  }
}
```

### Using Function Node to Build Request

For complex data transformation:

```javascript
// Function Node: Build Grid Data
const hours = $input.item.json.hours; // Array of 24 values
const date = $input.item.json.date;

const gridData = {
  T_Date: date
};

// Map hours array to T_00 through T_23
for (let i = 0; i < 24; i++) {
  const hourKey = `T_${String(i).padStart(2, '0')}`;
  gridData[hourKey] = hours[i] || '●';
}

return [{
  json: {
    grid_data: gridData,
    return_base64: false
  }
}];
```

## Error Handling

Add an **IF Node** after HTTP Request to check for errors:

```
[HTTP Request] → [IF] → [Success Path] / [Error Path]
```

**IF Node Condition:**
- **Value 1:** `{{ $json.success }}`
- **Operation:** Equals
- **Value 2:** `true`

**Error Path:** Add notification or logging node

## Testing

Test your workflow with a Manual Trigger:

1. Click "Execute Workflow"
2. Check the HTTP Request node output
3. Verify the image is generated correctly

## Production Tips

1. **Use Environment Variables** for the API URL:
   - In n8n: Settings → Environment Variables
   - Set: `GRID_API_URL=http://your-server:8000`
   - Use in HTTP Request: `{{ $env.GRID_API_URL }}/generate`

2. **Add Error Handling:**
   - Use Try-Catch nodes
   - Add retry logic
   - Log errors to monitoring service

3. **Secure the API:**
   - Add API key authentication
   - Use HTTPS
   - Implement rate limiting

4. **Optimize Performance:**
   - Cache frequently used images
   - Use async processing for large batches
   - Consider queue system for high volume

## Troubleshooting

### Connection Refused
- Ensure the HTTP server is running
- Check the port (default: 8000)
- Verify firewall settings

### Invalid Response
- Check the request body format
- Verify all required fields (T_Date) are present
- Check server logs for errors

### Image Not Generated
- Verify grid data format
- Check T_Date format (DD-MM-YYYY)
- Ensure hour values are valid (●, ✕, %, -)

## API Documentation

Full API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

