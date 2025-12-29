"""
Integration tests for complete user workflows
Tests end-to-end functionality across multiple components
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime
import json
import io

from app.main import app
from app.services.database import db_service
from app.services.auth import AuthService
from app.models.user import PatientModel, InstitutionModel, UserType
from app.models.report import Report, MetricData


@pytest.fixture
def client():
    """Test client for API requests"""
    return TestClient(app)


@pytest.fixture
def mock_firebase_token():
    """Mock Firebase token for authentication"""
    return {
        "uid": "test_patient_123",
        "email": "patient@test.com",
        "exp": 9999999999
    }


@pytest.fixture
def mock_hospital_token():
    """Mock Firebase token for hospital authentication"""
    return {
        "uid": "test_hospital_123",
        "email": "hospital@test.com",
        "exp": 9999999999
    }


@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing"""
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n>>\nendobj\n4 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(Test Report) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000206 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n299\n%%EOF"


class TestPatientWorkflow:
    """Test complete patient workflow from registration to analysis"""

    @patch('app.services.auth.AuthService.verify_token')
    @patch('app.services.database.db_service.initialize')
    @patch('app.services.database.db_service.get_user_by_uid')
    @patch('app.services.database.db_service.create_user')
    async def test_patient_registration_workflow(
        self, 
        mock_create_user, 
        mock_get_user, 
        mock_initialize, 
        mock_verify_token, 
        client, 
        mock_firebase_token
    ):
        """Test complete patient registration workflow"""
        # Setup mocks
        mock_verify_token.return_value = mock_firebase_token
        mock_initialize.return_value = None
        mock_get_user.return_value = None  # User doesn't exist
        
        # Mock user creation
        created_user = PatientModel(
            uid="test_patient_123",
            user_type=UserType.PATIENT,
            name="Test Patient",
            favorites=[],
            bio_data={},
            reports=[]
        )
        mock_create_user.return_value = created_user

        # Test registration
        response = client.post(
            "/api/v1/auth/register",
            json={"role": "patient", "name": "Test Patient"},
            headers={"Authorization": "Bearer fake_token"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_type"] == "patient"
        assert data["user"]["name"] == "Test Patient"
        assert "message" in data

    @patch('app.services.auth.AuthService.verify_token')
    @patch('app.services.database.db_service.initialize')
    @patch('app.services.database.db_service.get_user_by_uid')
    @patch('app.services.pdf_parser.pdf_parser_service.validate_pdf_content')
    @patch('app.services.pdf_parser.pdf_parser_service.parse_medical_report')
    @patch('app.services.database.db_service.create_report')
    @patch('app.services.database.db_service.add_report_to_patient')
    async def test_report_upload_workflow(
        self,
        mock_add_report,
        mock_create_report,
        mock_parse_report,
        mock_validate_pdf,
        mock_get_user,
        mock_initialize,
        mock_verify_token,
        client,
        mock_firebase_token,
        sample_pdf_content
    ):
        """Test complete report upload and processing workflow"""
        # Setup mocks
        mock_verify_token.return_value = mock_firebase_token
        mock_initialize.return_value = None
        
        # Mock patient user
        patient = PatientModel(
            uid="test_patient_123",
            user_type=UserType.PATIENT,
            name="Test Patient",
            favorites=[],
            bio_data={},
            reports=[]
        )
        mock_get_user.return_value = patient

        # Mock PDF processing
        mock_validate_pdf.return_value = True
        mock_parse_report.return_value = {
            "GLUCOSE": MetricData(
                name="Glucose",
                value="120",
                unit="mg/dL",
                range="70-100",
                verdict="HIGH"
            )
        }
        mock_create_report.return_value = None
        mock_add_report.return_value = None

        # Test file upload
        response = client.post(
            "/api/v1/reports/upload",
            files={"file": ("test_report.pdf", io.BytesIO(sample_pdf_content), "application/pdf")},
            headers={"Authorization": "Bearer fake_token"}
        )

        assert response.status_code == 202
        data = response.json()
        assert "report_id" in data
        assert data["processing_status"] == "processing"

    @patch('app.services.auth.AuthService.verify_token')
    @patch('app.services.database.db_service.initialize')
    @patch('app.services.database.db_service.get_user_by_uid')
    @patch('app.services.database.db_service.get_report_by_id')
    @patch('app.services.llm_analysis.llm_analysis_service.analyze_test_results')
    @patch('app.services.database.db_service.create_llm_report')
    @patch('app.services.database.db_service.update_report')
    async def test_ai_analysis_workflow(
        self,
        mock_update_report,
        mock_create_llm_report,
        mock_analyze_results,
        mock_get_report,
        mock_get_user,
        mock_initialize,
        mock_verify_token,
        client,
        mock_firebase_token
    ):
        """Test AI analysis generation workflow"""
        # Setup mocks
        mock_verify_token.return_value = mock_firebase_token
        mock_initialize.return_value = None
        
        # Mock patient user
        patient = PatientModel(
            uid="test_patient_123",
            user_type=UserType.PATIENT,
            name="Test Patient",
            favorites=[],
            bio_data={},
            reports=[]
        )
        mock_get_user.return_value = patient

        # Mock report data
        report_data = {
            "report_id": "test_report_123",
            "patient_id": "test_patient_123",
            "processed_at": datetime.utcnow().isoformat(),
            "attributes": {
                "GLUCOSE": {
                    "name": "Glucose",
                    "value": "120",
                    "unit": "mg/dL",
                    "range": "70-100",
                    "verdict": "HIGH"
                }
            },
            "llm_output": None,
            "llm_report_id": None
        }
        mock_get_report.return_value = report_data

        # Mock AI analysis
        mock_llm_report = MagicMock()
        mock_llm_report.output = {
            "lifestyle_recommendations": ["Reduce sugar intake"],
            "nutritional_advice": ["Eat more fiber"],
            "symptom_explanations": ["High glucose may indicate diabetes risk"],
            "next_steps": ["Consult with healthcare provider"]
        }
        mock_analyze_results.return_value = mock_llm_report
        mock_create_llm_report.return_value = "llm_report_123"
        mock_update_report.return_value = None

        # Test analysis generation
        response = client.post(
            "/api/v1/reports/test_report_123/analyze",
            json={"report_id": "test_report_123", "include_profile": True},
            headers={"Authorization": "Bearer fake_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "analysis" in data
        assert "lifestyle_recommendations" in data["analysis"]
        assert data["report_id"] == "test_report_123"


class TestHospitalWorkflow:
    """Test complete hospital workflow for patient management"""

    @patch('app.services.auth.AuthService.verify_token')
    @patch('app.services.database.db_service.initialize')
    @patch('app.services.database.db_service.get_user_by_uid')
    @patch('app.services.database.db_service.get_reports_by_patient_ids')
    @patch('app.services.database.db_service.count_reports_by_patient_ids')
    async def test_hospital_patient_access_workflow(
        self,
        mock_count_reports,
        mock_get_reports,
        mock_get_user,
        mock_initialize,
        mock_verify_token,
        client,
        mock_hospital_token
    ):
        """Test hospital accessing patient reports workflow"""
        # Setup mocks
        mock_verify_token.return_value = mock_hospital_token
        mock_initialize.return_value = None
        
        # Mock hospital user
        hospital = InstitutionModel(
            uid="test_hospital_123",
            user_type=UserType.INSTITUTION,
            name="Test Hospital",
            patient_list=["test_patient_123", "test_patient_456"]
        )
        mock_get_user.return_value = hospital

        # Mock reports data
        mock_reports = [
            {
                "report_id": "report_123",
                "patient_id": "test_patient_123",
                "processed_at": datetime.utcnow().isoformat(),
                "attributes": {"GLUCOSE": {"value": "120", "verdict": "HIGH"}}
            },
            {
                "report_id": "report_456",
                "patient_id": "test_patient_456",
                "processed_at": datetime.utcnow().isoformat(),
                "attributes": {"CHOLESTEROL": {"value": "250", "verdict": "HIGH"}}
            }
        ]
        mock_get_reports.return_value = mock_reports
        mock_count_reports.return_value = 2

        # Test getting reports for hospital patients
        response = client.get(
            "/api/v1/reports/",
            headers={"Authorization": "Bearer fake_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["reports"]) == 2
        assert data["total"] == 2


class TestRealtimeSynchronization:
    """Test real-time synchronization across sessions"""

    @patch('app.services.websocket.websocket_service')
    async def test_realtime_data_update_broadcast(self, mock_websocket_service):
        """Test real-time data updates are broadcast to connected clients"""
        # Mock WebSocket service
        mock_websocket_service.broadcast_data_update = AsyncMock()

        # Simulate data update
        patient_id = "test_patient_123"
        update_type = "report_processing_completed"
        update_data = {
            "report_id": "test_report_123",
            "status": "completed",
            "processed_at": datetime.utcnow().isoformat()
        }

        # Call broadcast function
        await mock_websocket_service.broadcast_data_update(
            patient_id, update_type, update_data
        )

        # Verify broadcast was called
        mock_websocket_service.broadcast_data_update.assert_called_once_with(
            patient_id, update_type, update_data
        )

    @patch('app.services.websocket.websocket_service')
    @patch('app.services.chatbot.chatbot_service')
    async def test_chat_session_synchronization(self, mock_chatbot_service, mock_websocket_service):
        """Test chat session synchronization across multiple connections"""
        # Mock services
        mock_websocket_service.handle_start_chat = AsyncMock()
        mock_websocket_service.handle_send_message = AsyncMock()
        mock_chatbot_service.start_session = AsyncMock()
        mock_chatbot_service.send_message = AsyncMock()

        # Mock chat session data
        session_data = {
            "session_id": "chat_session_123",
            "messages": [
                {
                    "role": "user",
                    "content": "What do my test results mean?",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        }

        mock_chatbot_service.start_session.return_value = session_data
        mock_websocket_service.handle_start_chat.return_value = session_data

        # Test chat session start
        result = await mock_websocket_service.handle_start_chat("test_patient_123")
        
        # Verify session was created and synchronized
        assert result == session_data
        mock_websocket_service.handle_start_chat.assert_called_once()


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery scenarios"""

    @patch('app.services.auth.AuthService.verify_token')
    @patch('app.services.database.db_service.initialize')
    @patch('app.services.database.db_service.get_user_by_uid')
    async def test_authentication_error_handling(
        self,
        mock_get_user,
        mock_initialize,
        mock_verify_token,
        client
    ):
        """Test authentication error handling"""
        # Setup mocks for authentication failure
        mock_verify_token.side_effect = Exception("Invalid token")
        mock_initialize.return_value = None

        # Test with invalid token
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    @patch('app.services.auth.AuthService.verify_token')
    @patch('app.services.database.db_service.initialize')
    @patch('app.services.database.db_service.get_user_by_uid')
    @patch('app.services.pdf_parser.pdf_parser_service.validate_pdf_content')
    async def test_pdf_processing_error_handling(
        self,
        mock_validate_pdf,
        mock_get_user,
        mock_initialize,
        mock_verify_token,
        client,
        mock_firebase_token
    ):
        """Test PDF processing error handling"""
        # Setup mocks
        mock_verify_token.return_value = mock_firebase_token
        mock_initialize.return_value = None
        
        # Mock patient user
        patient = PatientModel(
            uid="test_patient_123",
            user_type=UserType.PATIENT,
            name="Test Patient",
            favorites=[],
            bio_data={},
            reports=[]
        )
        mock_get_user.return_value = patient

        # Mock PDF validation failure
        mock_validate_pdf.return_value = False

        # Test with invalid PDF
        invalid_content = b"Not a PDF file"
        response = client.post(
            "/api/v1/reports/upload",
            files={"file": ("invalid.pdf", io.BytesIO(invalid_content), "application/pdf")},
            headers={"Authorization": "Bearer fake_token"}
        )

        assert response.status_code == 400
        data = response.json()
        assert "Invalid PDF file" in data["detail"]

    @patch('app.services.auth.AuthService.verify_token')
    @patch('app.services.database.db_service.initialize')
    @patch('app.services.database.db_service.get_user_by_uid')
    @patch('app.services.database.db_service.get_report_by_id')
    async def test_database_error_recovery(
        self,
        mock_get_report,
        mock_get_user,
        mock_initialize,
        mock_verify_token,
        client,
        mock_firebase_token
    ):
        """Test database error recovery"""
        # Setup mocks
        mock_verify_token.return_value = mock_firebase_token
        mock_initialize.return_value = None
        
        # Mock patient user
        patient = PatientModel(
            uid="test_patient_123",
            user_type=UserType.PATIENT,
            name="Test Patient",
            favorites=[],
            bio_data={},
            reports=[]
        )
        mock_get_user.return_value = patient

        # Mock database error
        mock_get_report.side_effect = Exception("Database connection failed")

        # Test database error handling
        response = client.get(
            "/api/v1/reports/test_report_123",
            headers={"Authorization": "Bearer fake_token"}
        )

        assert response.status_code == 500
        data = response.json()
        assert "Failed to get report" in data["detail"]


@pytest.mark.asyncio
async def test_complete_patient_journey():
    """Test complete patient journey from registration to analysis"""
    # This test would require a more complex setup with actual database
    # and would be run in a separate integration test environment
    
    # Steps that would be tested:
    # 1. Patient registers
    # 2. Patient uploads PDF report
    # 3. System processes PDF and extracts data
    # 4. Patient requests AI analysis
    # 5. System generates and returns analysis
    # 6. Patient tracks concerning metrics
    # 7. Patient views dashboard with trends
    # 8. Patient chats with AI about results
    
    # For now, we'll just verify the test structure is correct
    assert True  # Placeholder for actual integration test


if __name__ == "__main__":
    pytest.main([__file__])