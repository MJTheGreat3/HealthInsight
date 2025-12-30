# HealthInsightCore API Documentation

This document provides comprehensive documentation for all API endpoints in the HealthInsightCore medical test analysis platform.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: Your deployed backend URL

## Authentication

All API endpoints (except `/ping` and `/db-test`) require Firebase JWT authentication.

**Header Format:**

```
Authorization: Bearer <firebase_jwt_token>
```

**Authentication Flow:**

1. User logs in via Firebase on frontend
2. Firebase returns JWT token
3. Frontend includes token in Authorization header
4. Backend verifies token using Firebase Admin SDK

---

## 📋 Table of Contents

1. [Authentication & User Management](#authentication--user-management)
2. [Report Management](#report-management)
3. [AI Analysis](#ai-analysis)
4. [Chat Interface](#chat-interface)
5. [Access Control](#access-control)
6. [Hospital Management](#hospital-management)
7. [Dashboard & Analytics](#dashboard--analytics)
8. [Tracked Metrics](#tracked-metrics)
9. [Utility Endpoints](#utility-endpoints)

---

## Authentication & User Management

### POST `/api/user`

**Description**: User registration/onboarding - creates patient or institution account

**Request Body:**

```json
{
  "user_type": "patient" | "institution",
  "name": "string (optional for patients)",
  "hospital_name": "string (required for institutions)"
}
```

**Response:**

```json
{
  "message": "User created successfully",
  "user_id": "ObjectId"
}
```

---

### GET `/api/auth/me`

**Description**: Verify current user authentication and retrieve role

**Response:**

```json
{
  "uid": "firebase_uid",
  "email": "user@example.com",
  "role": "patient" | "institution"
}
```

---

### GET `/api/user/me`

**Description**: Get detailed user profile with BioData and Favorites

**Response (Patient):**

```json
{
  "_id": "ObjectId",
  "uid": "firebase_uid",
  "email": "user@example.com",
  "user_type": "patient",
  "name": "John Doe",
  "BioData": {
    "age": 30,
    "gender": "male",
    "weight": "70kg"
  },
  "Favorites": ["cholesterol", "blood_sugar", "hemoglobin"],
  "Reports": ["report_id_1", "report_id_2"]
}
```

**Response (Institution):**

```json
{
  "_id": "ObjectId",
  "uid": "firebase_uid",
  "email": "hospital@example.com",
  "user_type": "institution",
  "hospital_name": "City General Hospital",
  "patient_list": ["patient_uid_1", "patient_uid_2"]
}
```

---

### PATCH `/api/user/me`

**Description**: Update patient profile (name, BioData)

**Request Body:**

```json
{
  "name": "Updated Name",
  "BioData": {
    "age": 31,
    "gender": "male",
    "weight": "72kg",
    "height": "175cm"
  }
}
```

**Response:**

```json
{
  "message": "Profile updated successfully"
}
```

---

### GET `/api/user/{user_id}`

**Description**: Retrieve user by ObjectId

**Parameters:**

- `user_id`: MongoDB ObjectId

**Response:** Same as `/api/user/me`

---

### POST `/api/user/favorites`

**Description**: Add health marker to favorites (case-insensitive, sanitized)

**Request Body:**

```json
{
  "marker": "Blood Pressure"
}
```

**Response:**

```json
{
  "message": "Added to favorites",
  "favorites": ["cholesterol", "blood_sugar", "blood_pressure"]
}
```

---

### DELETE `/api/user/favorites`

**Description**: Remove marker from favorites

**Request Body:**

```json
{
  "marker": "blood_pressure"
}
```

**Response:**

```json
{
  "message": "Removed from favorites",
  "favorites": ["cholesterol", "blood_sugar"]
}
```

---

### GET `/api/user/favorites`

**Description**: List all user favorites

**Response:**

```json
{
  "favorites": ["cholesterol", "blood_sugar", "hemoglobin"]
}
```

---

## Report Management

### POST `/api/reports/upload`

**Description**: Upload PDF report, extract medical data, store in database (file discarded)

**Request:**

- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: PDF file (max 10MB)
  - `patient_id`: string (optional, defaults to current user UID)
  - `report_id`: string (optional, auto-generated if not provided)

**Response:**

```json
{
  "message": "Report uploaded successfully",
  "report_id": "ObjectId",
  "patient_id": "firebase_uid",
  "attributes_count": 15,
  "processed_at": "2024-01-15T10:30:00Z"
}
```

---

### POST `/api/reports/upload-and-analyze`

**Description**: Upload PDF and automatically generate AI analysis (atomic operation)

**Request:**

- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: PDF file (max 10MB)
  - `patient_id`: string (optional)
  - `report_id`: string (optional)

**Response:**

```json
{
  "message": "Report uploaded and analyzed successfully",
  "report_id": "ObjectId",
  "llm_report_id": "ObjectId",
  "analysis": {
    "interpretation": "Your test results show...",
    "lifestyle_changes": ["30 min walk daily", "reduce sodium intake"],
    "nutritional_changes": ["increase iron-rich foods", "add vitamin D"],
    "symptom_probable_cause": null,
    "next_steps": ["consult a doctor", "repeat test in 3 months"],
    "concern_options": ["hemoglobin", "cholesterol", "blood_sugar"]
  }
}
```

---

### GET `/api/reports/{report_id}`

**Description**: Retrieve specific report with all attributes

**Parameters:**

- `report_id`: MongoDB ObjectId

**Response:**

```json
{
  "_id": "ObjectId",
  "Report_id": "report_12345",
  "Patient_id": "firebase_uid",
  "Processed_at": "2024-01-15T10:30:00Z",
  "Attributes": {
    "test_1": {
      "name": "Hemoglobin",
      "value": "12.5",
      "remark": "Low",
      "range": "13.5-17.5",
      "unit": "g/dL"
    },
    "test_2": {
      "name": "Total Cholesterol",
      "value": "220",
      "remark": "High",
      "range": "<200",
      "unit": "mg/dL"
    }
  },
  "llm_report_id": "ObjectId"
}
```

---

### GET `/api/reports/patient/{patient_id}`

**Description**: Get all reports for a patient (limit 50, sorted by time)

**Parameters:**

- `patient_id`: Firebase UID

**Response:**

```json
{
  "reports": [
    {
      "_id": "ObjectId",
      "Report_id": "report_12345",
      "Patient_id": "firebase_uid",
      "Processed_at": "2024-01-15T10:30:00Z",
      "attributes_count": 15,
      "has_llm_analysis": true
    }
  ],
  "total_count": 3
}
```

---

### PATCH `/api/reports/{report_id}/processed-at`

**Description**: Update report timestamp

**Parameters:**

- `report_id`: MongoDB ObjectId

**Request Body:**

```json
{
  "processed_at": "2024-01-15T10:30:00Z"
}
```

---

### PATCH `/api/reports/{report_id}/attribute-by-name`

**Description**: Update test values by name (value, remark, range, unit)

**Parameters:**

- `report_id`: MongoDB ObjectId

**Request Body:**

```json
{
  "name": "Hemoglobin",
  "value": "13.0",
  "remark": "Normal",
  "range": "13.5-17.5",
  "unit": "g/dL"
}
```

---

### POST `/api/reports/{report_id}/attribute`

**Description**: Add new test attribute to report

**Parameters:**

- `report_id`: MongoDB ObjectId

**Request Body:**

```json
{
  "name": "Vitamin D",
  "value": "25",
  "remark": "Deficient",
  "range": "30-100",
  "unit": "ng/mL"
}
```

---

### DELETE `/api/reports/{report_id}/attribute-by-name`

**Description**: Delete test by name

**Parameters:**

- `report_id`: MongoDB ObjectId

**Request Body:**

```json
{
  "name": "Vitamin D"
}
```

---

### DELETE `/api/reports/{report_id}`

**Description**: Delete entire report

**Parameters:**

- `report_id`: MongoDB ObjectId

**Response:**

```json
{
  "message": "Report deleted successfully"
}
```

---

### GET `/api/reports`

**Description**: List all reports (limit 50)

**Response:**

```json
{
  "reports": [
    {
      "_id": "ObjectId",
      "Report_id": "report_12345",
      "Patient_id": "firebase_uid",
      "Processed_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### GET `/api/draw_graph/{patient_id}/{attribute}`

**Description**: Extract trend data for specific biomarker with fuzzy matching

**Parameters:**

- `patient_id`: Firebase UID
- `attribute`: Biomarker name (supports fuzzy matching, e.g., "cholesterol", "hb", "sugar")

**Response:**

```json
{
  "attribute": "Total Cholesterol",
  "matched_tests": ["Total Cholesterol", "Cholesterol Total"],
  "data_points": [
    {
      "date": "2024-01-15",
      "value": 220,
      "unit": "mg/dL",
      "remark": "High",
      "report_id": "ObjectId"
    },
    {
      "date": "2024-02-15",
      "value": 200,
      "unit": "mg/dL",
      "remark": "Normal",
      "report_id": "ObjectId"
    }
  ],
  "trend": "improving"
}
```

---

## AI Analysis

### POST `/api/LLMReport`

**Description**: Generate LLM analysis or update favorites

**Request Body (Generate Analysis):**

```json
{
  "patient_id": "firebase_uid",
  "report_id": "ObjectId",
  "Attributes": {
    "test_1": {
      "name": "Hemoglobin",
      "value": "12.5",
      "remark": "Low",
      "range": "13.5-17.5"
    }
  }
}
```

**Request Body (Update Favorites Only):**

```json
{
  "patient_id": "firebase_uid",
  "selected_concerns": ["hemoglobin", "cholesterol", "blood_sugar"]
}
```

**Response (Analysis Generated):**

```json
{
  "llm_report_id": "ObjectId",
  "analysis": {
    "interpretation": "Your hemoglobin levels are below the normal range...",
    "lifestyle_changes": ["increase iron-rich foods", "avoid tea with meals"],
    "nutritional_changes": [
      "eat spinach and red meat",
      "take iron supplements"
    ],
    "symptom_probable_cause": null,
    "next_steps": ["consult a hematologist", "repeat CBC in 4 weeks"],
    "concern_options": ["hemoglobin", "iron_deficiency", "fatigue"]
  }
}
```

---

### GET `/api/LLMReport/{report_id}`

**Description**: Retrieve LLM analysis by ObjectId

**Parameters:**

- `report_id`: MongoDB ObjectId

**Response:**

```json
{
  "_id": "ObjectId",
  "patient_id": "firebase_uid",
  "report_id": "ObjectId",
  "time": "2024-01-15T10:30:00Z",
  "output": {
    "interpretation": "Analysis text...",
    "lifestyle_changes": ["suggestion 1", "suggestion 2"],
    "nutritional_changes": ["nutrition tip 1", "nutrition tip 2"],
    "symptom_probable_cause": null,
    "next_steps": ["step 1", "step 2"],
    "concern_options": ["concern 1", "concern 2"]
  },
  "input": {
    "test_data": "..."
  }
}
```

---

### GET `/api/LLMReportsPatientList/{patient_id}`

**Description**: List patient's LLM reports (limit 10, sorted by time)

**Parameters:**

- `patient_id`: Firebase UID

**Response:**

```json
{
  "llm_reports": [
    {
      "_id": "ObjectId",
      "report_id": "ObjectId",
      "time": "2024-01-15T10:30:00Z",
      "has_analysis": true
    }
  ]
}
```

---

## Chat Interface

### POST `/api/chat`

**Description**: Interactive chatbot with medical report context

**Request Body:**

```json
{
  "message": "What does my cholesterol level mean?",
  "user_id": "firebase_uid",
  "report_id": "ObjectId",
  "conversation_history": [
    {
      "from_user": "user",
      "text": "Hello"
    },
    {
      "from_user": "assistant",
      "text": "Hi! I can help you understand your medical reports."
    }
  ]
}
```

**Response:**

```json
{
  "response": "Based on your recent report, your total cholesterol level of 220 mg/dL is above the recommended level of <200 mg/dL. This indicates you may be at increased risk for cardiovascular disease. I recommend discussing dietary changes and exercise with your doctor.",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Access Control

### POST `/access/request`

**Description**: Hospital requests patient data access

**Request Body:**

```json
{
  "email": "patient@example.com"
}
```

**Response:**

```json
{
  "status": "pending",
  "message": "Access request sent to patient"
}
```

---

### GET `/access/my-requests`

**Description**: Patient views all access requests (pending/approved/revoked)

**Response:**

```json
{
  "requests": [
    {
      "_id": "ObjectId",
      "hospital_uid": "hospital_firebase_uid",
      "hospital_name": "City General Hospital",
      "patient_email": "patient@example.com",
      "status": "pending",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": null
    }
  ]
}
```

---

### POST `/access/respond`

**Description**: Patient approves/rejects/revokes access

**Request Body:**

```json
{
  "request_id": "ObjectId",
  "action": "approve" | "reject" | "revoke"
}
```

**Response:**

```json
{
  "message": "Access approved successfully",
  "status": "approved"
}
```

---

### GET `/access/active`

**Description**: Patient lists hospitals with active access

**Response:**

```json
{
  "active_access": [
    {
      "hospital_uid": "hospital_firebase_uid",
      "hospital_name": "City General Hospital",
      "approved_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

## Hospital Management

### GET `/hospital/patients`

**Description**: Hospital views approved patients

**Response:**

```json
{
  "patients": [
    {
      "uid": "patient_firebase_uid",
      "name": "John Doe",
      "email": "patient@example.com",
      "report_count": 5,
      "last_report": "2024-01-15T10:30:00Z",
      "approved_at": "2024-01-10T09:00:00Z"
    }
  ]
}
```

---

### GET `/hospital/patient/{patient_uid}`

**Description**: Hospital views specific patient (read-only, requires approval)

**Parameters:**

- `patient_uid`: Patient's Firebase UID

**Response:**

```json
{
  "patient": {
    "uid": "patient_firebase_uid",
    "name": "John Doe",
    "email": "patient@example.com",
    "BioData": {
      "age": 30,
      "gender": "male"
    },
    "Favorites": ["cholesterol", "blood_sugar"],
    "report_count": 5,
    "recent_reports": [
      {
        "_id": "ObjectId",
        "Report_id": "report_12345",
        "Processed_at": "2024-01-15T10:30:00Z",
        "attributes_count": 15
      }
    ]
  }
}
```

---

## Dashboard & Analytics

### GET `/dashboard/actionable-suggestions`

**Description**: Generate meta-analysis across 1-5 recent reports for personalized health suggestions

**Response:**

```json
{
  "actionable_suggestions": [
    {
      "category": "nutrition",
      "priority": "high",
      "suggestion": "Your cholesterol levels have been consistently high across the last 3 reports. Consider reducing saturated fat intake and increasing fiber.",
      "affected_biomarkers": ["total_cholesterol", "ldl_cholesterol"],
      "trend": "worsening"
    },
    {
      "category": "lifestyle",
      "priority": "medium",
      "suggestion": "Your hemoglobin levels show improvement. Continue your current iron supplementation.",
      "affected_biomarkers": ["hemoglobin"],
      "trend": "improving"
    }
  ],
  "report_count": 3,
  "analysis_period": "last_6_months"
}
```

---

## Tracked Metrics

### POST `/api/user/favorites`

**Description**: Add health marker to tracked metrics (case-insensitive, sanitized)

**Request Body:**

```json
{
  "marker": "Blood Pressure"
}
```

**Response:**

```json
{
  "message": "Added to tracked metrics",
  "favorites": ["cholesterol", "blood_sugar", "blood_pressure"]
}
```

---

### DELETE `/api/user/favorites`

**Description**: Remove marker from tracked metrics

**Request Body:**

```json
{
  "marker": "blood_pressure"
}
```

**Response:**

```json
{
  "message": "Removed from tracked metrics",
  "favorites": ["cholesterol", "blood_sugar"]
}
```

---

### GET `/api/user/favorites`

**Description**: List all user tracked metrics

**Response:**

```json
{
  "favorites": ["cholesterol", "blood_sugar", "hemoglobin"]
}
```

---

### GET `/api/draw_graph/{patient_id}/{attribute}`

**Description**: Extract trend data for specific biomarker with fuzzy matching

**Parameters:**

- `patient_id`: Firebase UID
- `attribute`: Biomarker name (supports fuzzy matching, e.g., "cholesterol", "hb", "sugar")

**Response:**

```json
{
  "attribute": "Total Cholesterol",
  "matched_tests": ["Total Cholesterol", "Cholesterol Total"],
  "data_points": [
    {
      "date": "2024-01-15",
      "value": 220,
      "unit": "mg/dL",
      "remark": "High",
      "report_id": "ObjectId"
    },
    {
      "date": "2024-02-15",
      "value": 200,
      "unit": "mg/dL",
      "remark": "Normal",
      "report_id": "ObjectId"
    }
  ],
  "trend": "improving"
}
```

---

## Utility Endpoints

### GET `/ping`

**Description**: Health check endpoint (no authentication required)

**Response:**

```json
{
  "message": "pong"
}
```

---

### GET `/db-test`

**Description**: Database connectivity test (requires authentication)

**Response:**

```json
{
  "status": "ok",
  "report_count": 150
}
```

---

## Error Responses

### Common Error Formats

**401 Unauthorized:**

```json
{
  "detail": "Not authenticated"
}
```

**403 Forbidden:**

```json
{
  "detail": "Only hospitals can request access"
}
```

**404 Not Found:**

```json
{
  "detail": "User not found"
}
```

**400 Bad Request:**

```json
{
  "detail": "Patient email required"
}
```

**422 Validation Error:**

```json
{
  "detail": [
    {
      "loc": ["body", "patient_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limiting & Quotas

- **File Upload**: Max 10MB per PDF file
- **Reports per Patient**: No hard limit, but queries are limited to 50 results
- **LLM Analysis**: No rate limiting currently implemented
- **Chat Messages**: No rate limiting currently implemented

---

## Data Models

### User Model

```json
{
  "_id": "ObjectId",
  "uid": "firebase_uid",
  "email": "string",
  "user_type": "patient" | "institution",

  // Patient-specific fields
  "name": "string",
  "bio_data": {
    "height": "number",
    "weight": "number",
    "allergies": ["string"]
  },
  "favorites": ["string"],  // Tracked metrics/concerns
  "reports": ["string"],    // Report IDs

  // Institution-specific fields
  "hospital_name": "string",
  "patient_list": ["firebase_uid"]
}
```

### Report Model

```json
{
  "_id": "ObjectId",
  "report_id": "string",
  "patient_id": "firebase_uid",
  "processed_at": "ISO_datetime",
  "attributes": {
    "test_1": {
      "name": "string",
      "value": "string",
      "remark": "string",
      "range": "string",
      "unit": "string",
      "verdict": "NORMAL | HIGH | LOW | CRITICAL"
    }
  },
  "llm_output": "string",
  "llm_report_id": "ObjectId",
  "selected_concerns": ["string"] // Metrics added to favorites
}
```

### LLM Report Model

```json
{
  "_id": "ObjectId",
  "patient_id": "firebase_uid",
  "report_id": "ObjectId",
  "time": "ISO_datetime",
  "output": {
    "lifestyle_recommendations": ["string"],
    "nutritional_advice": ["string"],
    "symptom_explanations": ["string"],
    "next_steps": ["string"]
  },
  "input": {
    "attributes": "object",
    "bio_data": "object"
  }
}
```

### Chat Sessions Model

```json
{
  "_id": "ObjectId",
  "patient_id": "firebase_uid",
  "messages": [
    {
      "role": "user | assistant",
      "content": "string",
      "timestamp": "ISO_datetime"
    }
  ],
  "context": {
    "recent_reports": ["string"],
    "tracked_metrics": ["string"]
  },
  "created_at": "ISO_datetime",
  "updated_at": "ISO_datetime"
}
```

### Access Request Model

```json
{
  "_id": "ObjectId",
  "hospital_uid": "firebase_uid",
  "patient_email": "string",
  "status": "pending" | "approved" | "rejected" | "revoked",
  "created_at": "ISO_datetime",
  "updated_at": "ISO_datetime"
}
```

---

## Interactive API Documentation

When running the application, visit `http://localhost:8000/docs` for interactive Swagger UI documentation where you can test all endpoints directly in your browser.
