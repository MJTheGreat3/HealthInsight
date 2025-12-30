# API Reference

## Base URL

- Development: `http://localhost:8000`
- Production: `https://your-domain.com/api`

## Authentication

All API endpoints require Firebase JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <firebase-jwt-token>
```

## Response Format

All API responses follow this structure:

```json
{
  "success": true,
  "data": {},
  "message": "Success message",
  "error": null
}
```

Error responses:

```json
{
  "success": false,
  "data": null,
  "message": "Error description",
  "error": "ERROR_CODE"
}
```

## Endpoints

### Authentication

#### Get Current User

```http
GET /auth/me
```

**Response:**

```json
{
  "uid": "firebase-user-id",
  "email": "user@example.com",
  "role": "patient"
}
```

### User Management

#### Get User Profile

```http
GET /user/me
```

**Response:**

```json
{
  "uid": "firebase-user-id",
  "email": "user@example.com",
  "user_type": "patient",
  "name": "John Doe",
  "BioData": {
    "age": 30,
    "gender": "male"
  },
  "Favorites": ["hemoglobin", "cholesterol"]
}
```

#### Create/Onboard User

```http
POST /user
```

**Request Body:**

```json
{
  "user_type": "patient",
  "hospital_name": "Optional for institutions"
}
```

#### Update User Profile

```http
PATCH /user/me
```

**Request Body:**

```json
{
  "name": "John Doe",
  "age": 30,
  "gender": "male"
}
```

### Favorites Management

#### Add Favorite Marker

```http
POST /user/favorites
```

**Request Body:**

```json
{
  "marker": "Hemoglobin A1c"
}
```

#### Remove Favorite Marker

```http
DELETE /user/favorites
```

**Request Body:**

```json
{
  "marker": "Hemoglobin A1c"
}
```

#### Get User Favorites

```http
GET /user/favorites
```

**Response:**

```json
{
  "favorites": ["Hemoglobin A1c", "Total Cholesterol"]
}
```

### Report Management

#### Upload Report

```http
POST /api/reports/upload
```

**Request (multipart/form-data):**

- `file`: PDF file
- `patient_id`: Optional patient ID
- `report_id`: Optional report ID

**Response:**

```json
{
  "message": "Report uploaded and processed successfully",
  "report_id": "report_abc123",
  "patient_id": "patient_xyz789",
  "tests_stored": 15,
  "id": "mongodb-object-id"
}
```

**Note:** The uploaded PDF file is processed for data extraction and then discarded. Only the extracted medical data is stored in the database.

#### Upload and Analyze Report

```http
POST /api/reports/upload-and-analyze
```

**Request (multipart/form-data):**

- `file`: PDF file
- `patient_id`: Optional patient ID
- `report_id`: Optional report ID
- `auto_analyze`: Boolean (default: true)

**Response:**

```json
{
  "message": "Report uploaded and analyzed successfully",
  "report_id": "report_abc123",
  "patient_id": "patient_xyz789",
  "tests_stored": 15,
  "llm_analysis_complete": true,
  "llm_report_id": "llm_report_id",
  "llm_analysis": {
    "interpretation": "Your test results show...",
    "lifestyle_changes": ["Exercise 30 minutes daily"],
    "nutritional_changes": ["Increase iron-rich foods"],
    "next_steps": ["Consult with doctor"],
    "concern_options": ["Iron", "Vitamin D"]
  }
}
```

#### Get Specific Report

```http
GET /api/reports/{report_id}
```

**Response:**

```json
{
  "Report_id": "report_abc123",
  "Patient_id": "patient_xyz789",
  "Processed_at": "2024-01-15T10:30:00Z",
  "Attributes": {
    "test_1": {
      "name": "Hemoglobin",
      "value": "12.5",
      "unit": "g/dL",
      "range": "12.0-15.5",
      "remark": "Normal"
    }
  },
  "llm_report_id": "llm_report_id"
}
```

#### Get Patient Reports

```http
GET /api/reports/patient/{patient_id}
```

**Response:**

```json
{
  "patient_id": "patient_xyz789",
  "report_count": 3,
  "reports": [
    {
      "Report_id": "report_abc123",
      "Processed_at": "2024-01-15T10:30:00Z",
      "Attributes": {}
    }
  ]
}
```

#### Update Report Attribute

```http
PATCH /api/reports/{report_id}/attribute-by-name
```

**Request Body:**

```json
{
  "name": "Hemoglobin",
  "value": "13.0",
  "remark": "Improved",
  "range": "12.0-15.5",
  "unit": "g/dL"
}
```

#### Add New Attribute

```http
POST /api/reports/{report_id}/attribute
```

**Request Body:**

```json
{
  "name": "New Test",
  "value": "100",
  "unit": "mg/dL",
  "range": "70-100",
  "remark": "Normal"
}
```

#### Delete Attribute

```http
DELETE /api/reports/{report_id}/attribute-by-name
```

**Request Body:**

```json
{
  "name": "Test Name"
}
```

#### Delete Report

```http
DELETE /api/reports/{report_id}
```

### Data Visualization

#### Get Graph Data

```http
GET /api/draw_graph/{patient_id}/{attribute}
```

**Response:**

```json
{
  "patient_id": "patient_xyz789",
  "attribute": "hemoglobin",
  "data_points": 5,
  "values": [
    {
      "value": 12.5,
      "timestamp": "2024-01-15T10:30:00Z",
      "remark": "Normal",
      "matched_name": "Hemoglobin"
    }
  ]
}
```

### AI Analysis

#### Get LLM Report

```http
GET /api/llm-reports/{report_id}
```

**Response:**

```json
{
  "patient_id": "patient_xyz789",
  "report_id": "report_abc123",
  "time": "2024-01-15T10:30:00Z",
  "output": {
    "interpretation": "Your test results indicate...",
    "lifestyle_changes": ["Exercise regularly"],
    "nutritional_changes": ["Eat more leafy greens"],
    "symptom_probable_cause": null,
    "next_steps": ["Follow up in 3 months"],
    "concern_options": ["Iron", "Vitamin B12"]
  },
  "input": {}
}
```

#### Generate Analysis

```http
POST /api/llm-reports/analyze
```

**Request Body:**

```json
{
  "patient_id": "patient_xyz789",
  "report_id": "report_abc123",
  "favorites": ["hemoglobin"],
  "biodata": {
    "age": 30,
    "gender": "male"
  }
}
```

### Dashboard

#### Get Actionable Suggestions

```http
GET /dashboard/actionable-suggestions
```

**Response:**

```json
{
  "actionable_suggestions": [
    "Consider increasing iron intake based on recent hemoglobin levels",
    "Schedule follow-up blood work in 3 months",
    "Maintain current exercise routine"
  ]
}
```

### Access Control

#### Request Patient Access

```http
POST /access/request
```

**Request Body:**

```json
{
  "patient_email": "patient@example.com",
  "message": "Request access for treatment"
}
```

#### Get Access Requests

```http
GET /access/requests
```

**Response:**

```json
{
  "requests": [
    {
      "_id": "request_id",
      "patient_email": "patient@example.com",
      "hospital_uid": "hospital_uid",
      "hospital_name": "City Hospital",
      "message": "Request message",
      "status": "pending",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Update Access Request

```http
PATCH /access/requests/{request_id}
```

**Request Body:**

```json
{
  "status": "approved"
}
```

### Hospital Management

#### Get Hospital Patients

```http
GET /hospital/patients
```

**Response:**

```json
[
  {
    "_id": "patient_object_id",
    "uid": "patient_uid",
    "email": "patient@example.com",
    "name": "John Doe",
    "user_type": "patient"
  }
]
```

#### Get Patient Details for Hospital

```http
GET /hospital/patient/{patient_uid}
```

**Response:**

```json
{
  "uid": "patient_uid",
  "email": "patient@example.com",
  "name": "John Doe",
  "BioData": {
    "age": 30,
    "gender": "male"
  },
  "Reports": ["report_id_1", "report_id_2"]
}
```

## Error Codes

| Code                  | Description                          |
| --------------------- | ------------------------------------ |
| `INVALID_TOKEN`       | Firebase token is invalid or expired |
| `USER_NOT_FOUND`      | User not found in database           |
| `UNAUTHORIZED`        | User not authorized for this action  |
| `INVALID_FILE_TYPE`   | Uploaded file is not a PDF           |
| `FILE_TOO_LARGE`      | File exceeds maximum size limit      |
| `PROCESSING_FAILED`   | PDF processing or OCR failed         |
| `LLM_ANALYSIS_FAILED` | AI analysis could not be completed   |
| `DATABASE_ERROR`      | Database operation failed            |
| `VALIDATION_ERROR`    | Request data validation failed       |

## Rate Limits

- File uploads: 10 per hour per user
- API requests: 1000 per hour per user
- AI analysis: 50 per day per user

## File Upload Limits

- Maximum file size: 10MB
- Supported formats: PDF only
- Maximum pages: 50 per PDF
- **Important**: Uploaded files are processed for data extraction and then immediately discarded. Only the extracted medical data is stored in the database.
