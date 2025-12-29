"""
Property-based tests for authentication system
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, status

from app.services.auth import AuthService
from app.models.user import UserType, UserModel, PatientModel, InstitutionModel
from app.core.exceptions import AuthenticationError, ConflictError


# Test data strategies
@st.composite
def valid_firebase_token_data(draw):
    """Generate valid Firebase token data"""
    uid = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    email = draw(st.emails())
    name = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'))))
    
    return {
        "uid": uid,
        "email": email,
        "name": name,
        "exp": draw(st.integers(min_value=1000000000, max_value=2000000000))  # Unix timestamp
    }


@st.composite
def user_registration_data(draw):
    """Generate user registration data"""
    user_type = draw(st.sampled_from([UserType.PATIENT, UserType.INSTITUTION]))
    name = draw(st.one_of(
        st.none(),
        st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')))
    ))
    
    return {
        "user_type": user_type.value,
        "name": name
    }


def create_mock_auth_service():
    """Create AuthService instance with mocked dependencies"""
    with patch('app.services.auth.initialize_firebase'), \
         patch('app.services.auth.DatabaseService') as mock_db_service:
        
        # Mock database service
        mock_db_instance = AsyncMock()
        mock_db_service.return_value = mock_db_instance
        
        service = AuthService()
        service.db_service = mock_db_instance
        return service


class TestAuthenticationProperties:
    """Property-based tests for authentication and authorization"""
    
    @given(valid_firebase_token_data())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_authentication_and_authorization_property(self, token_data):
        """
        Property 1: Authentication and Authorization
        For any valid user credentials (patient or hospital), the authentication system 
        should verify the credentials, create or retrieve the user session, and grant 
        access to role-appropriate features
        **Feature: health-insight-core, Property 1: Authentication and Authorization**
        **Validates: Requirements 1.1, 1.2, 8.1, 8.2**
        """
        # Arrange
        auth_service = create_mock_auth_service()
        mock_token = "mock_firebase_token"
        uid = token_data["uid"]
        
        # Mock Firebase token verification
        with patch('app.services.auth.verify_firebase_token', return_value=token_data):
            
            # Test Case 1: New user authentication (should create user)
            auth_service.db_service.get_user_by_uid.return_value = None
            auth_service.db_service.create_user = AsyncMock()
            auth_service.db_service.initialize = AsyncMock()
            
            # Act
            user = await auth_service.authenticate_user(mock_token)
            
            # Assert - User should be created and returned
            assert user is not None
            assert user.uid == uid
            assert isinstance(user, UserModel)
            
            # Test Case 2: Existing user authentication (should retrieve user)
            existing_user_data = {
                "uid": uid,
                "user_type": UserType.PATIENT.value,
                "name": token_data.get("name", "Test User"),
                "favorites": [],
                "bio_data": {},
                "reports": []
            }
            
            auth_service.db_service.get_user_by_uid.return_value = existing_user_data
            
            # Act
            user = await auth_service.authenticate_user(mock_token)
            
            # Assert - Existing user should be returned
            assert user is not None
            assert user.uid == uid
            assert user.user_type == UserType.PATIENT
            assert isinstance(user, PatientModel)
    
    @given(valid_firebase_token_data(), user_registration_data())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_user_registration_property(self, token_data, registration_data):
        """
        Property: User Registration Completeness
        For any valid Firebase token and registration data, the system should create 
        a user with the specified type and return the appropriate user model
        **Feature: health-insight-core, Property 1: Authentication and Authorization**
        **Validates: Requirements 1.1, 1.2, 8.1, 8.2**
        """
        # Arrange
        auth_service = create_mock_auth_service()
        mock_token = "mock_firebase_token"
        uid = token_data["uid"]
        user_type = UserType(registration_data["user_type"])
        name = registration_data["name"]
        
        # Mock Firebase token verification
        with patch('app.services.auth.verify_firebase_token', return_value=token_data):
            
            # Mock database operations
            auth_service.db_service.get_user_by_uid.return_value = None  # New user
            auth_service.db_service.create_user = AsyncMock()
            auth_service.db_service.initialize = AsyncMock()
            
            # Act
            user = await auth_service.register_user(mock_token, user_type, name)
            
            # Assert - User should be created with correct type
            assert user is not None
            assert user.uid == uid
            assert user.user_type == user_type
            
            if user_type == UserType.PATIENT:
                assert isinstance(user, PatientModel)
                assert user.favorites == []
                assert user.bio_data == {}
                assert user.reports == []
            else:  # INSTITUTION
                assert isinstance(user, InstitutionModel)
                assert user.patient_list == []
            
            # Verify database create was called
            auth_service.db_service.create_user.assert_called_once()
    
    @given(st.sampled_from([UserType.PATIENT, UserType.INSTITUTION]))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_role_validation_property(self, user_type):
        """
        Property: Role Validation Consistency
        For any user type, role validation should correctly identify matching and non-matching roles
        **Feature: health-insight-core, Property 1: Authentication and Authorization**
        **Validates: Requirements 1.1, 1.2, 8.1, 8.2**
        """
        # Arrange
        auth_service = create_mock_auth_service()
        if user_type == UserType.PATIENT:
            user = PatientModel(uid="test_uid", user_type=user_type, name="Test Patient")
        else:
            user = InstitutionModel(uid="test_uid", user_type=user_type, name="Test Institution")
        
        # Act & Assert - Same role should validate
        assert auth_service.validate_user_role(user, user_type) is True
        
        # Act & Assert - Different role should not validate
        other_type = UserType.INSTITUTION if user_type == UserType.PATIENT else UserType.PATIENT
        assert auth_service.validate_user_role(user, other_type) is False
        
        # Act & Assert - Multiple roles should work correctly
        assert auth_service.validate_user_roles(user, [user_type]) is True
        assert auth_service.validate_user_roles(user, [other_type]) is False
        assert auth_service.validate_user_roles(user, [user_type, other_type]) is True
    
    @given(st.text(min_size=1, max_size=100))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_invalid_token_handling_property(self, invalid_token):
        """
        Property: Invalid Token Rejection
        For any invalid token, the authentication system should reject it with appropriate error
        **Feature: health-insight-core, Property 1: Authentication and Authorization**
        **Validates: Requirements 1.1, 1.2, 8.1, 8.2**
        """
        # Arrange
        auth_service = create_mock_auth_service()
        
        # Arrange - Mock Firebase to raise ValueError for invalid token
        with patch('app.services.auth.verify_firebase_token', side_effect=ValueError("Invalid token")):
            
            # Act & Assert - Should raise AuthenticationError for invalid token
            with pytest.raises(AuthenticationError) as exc_info:
                await auth_service.authenticate_user(invalid_token)
            
            assert "Invalid authentication token" in str(exc_info.value.message)
    
    @given(valid_firebase_token_data())
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_duplicate_user_registration_property(self, token_data):
        """
        Property: Duplicate Registration Prevention
        For any existing user, attempting to register again should fail with conflict error
        **Feature: health-insight-core, Property 1: Authentication and Authorization**
        **Validates: Requirements 1.1, 1.2, 8.1, 8.2**
        """
        # Arrange
        auth_service = create_mock_auth_service()
        mock_token = "mock_firebase_token"
        uid = token_data["uid"]
        
        # Mock existing user
        existing_user_data = {
            "uid": uid,
            "user_type": UserType.PATIENT.value,
            "name": "Existing User"
        }
        
        with patch('app.services.auth.verify_firebase_token', return_value=token_data):
            auth_service.db_service.get_user_by_uid.return_value = existing_user_data
            auth_service.db_service.initialize = AsyncMock()
            
            # Act & Assert - Should raise ConflictError for duplicate registration
            with pytest.raises(ConflictError) as exc_info:
                await auth_service.register_user(mock_token, UserType.PATIENT, "New Name")
            
            assert "Resource already exists" in str(exc_info.value.message)