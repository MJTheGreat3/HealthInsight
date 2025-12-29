"""
Authentication service for Firebase Auth integration
"""

from typing import Optional, Dict, Any, Union
from fastapi import HTTPException, status
from firebase_admin import auth
from app.core.firebase import initialize_firebase, verify_firebase_token
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DatabaseError,
    get_error_message
)
from app.core.error_logging import error_logger
from app.models.user import UserType, UserModel, PatientModel, InstitutionModel
from app.services.database import DatabaseService


class AuthService:
    """Service for handling Firebase authentication and user management"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        initialize_firebase()
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify Firebase ID token and return decoded token data
        
        Args:
            token: Firebase ID token
            
        Returns:
            Decoded token data containing user information
            
        Raises:
            AuthenticationError: If token is invalid or verification fails
        """
        try:
            decoded_token = await verify_firebase_token(token)
            return decoded_token
        except ValueError as e:
            raise AuthenticationError(
                message=get_error_message("AUTH_TOKEN_INVALID"),
                details={"original_error": str(e)}
            )
        except Exception as e:
            error_logger.log_authentication_error(e)
            raise AuthenticationError(
                message=get_error_message("AUTH_TOKEN_INVALID"),
                details={"error_type": type(e).__name__}
            )
    
    async def get_or_create_user(self, uid: str, user_data: Optional[Dict[str, Any]] = None) -> Union[UserModel, PatientModel, InstitutionModel]:
        """
        Get existing user or create new user in database
        
        Args:
            uid: Firebase user ID
            user_data: Optional user data for new user creation
            
        Returns:
            UserModel instance (PatientModel or InstitutionModel)
            
        Raises:
            DatabaseError: If database operations fail
        """
        try:
            # Initialize database service if needed
            if not self.db_service.db:
                await self.db_service.initialize()
            
            # Try to get existing user
            existing_user_data = await self.db_service.get_user_by_uid(uid)
            if existing_user_data:
                # Convert dict to appropriate model
                user_type = existing_user_data.get("user_type")
                if user_type == UserType.PATIENT:
                    return PatientModel(**existing_user_data)
                elif user_type == UserType.INSTITUTION:
                    return InstitutionModel(**existing_user_data)
                else:
                    return UserModel(**existing_user_data)
            
            # Create new user if not exists
            if user_data and "user_type" in user_data:
                user_type = UserType(user_data["user_type"])
                
                if user_type == UserType.PATIENT:
                    new_user = PatientModel(
                        uid=uid,
                        user_type=user_type,
                        name=user_data.get("name"),
                        favorites=[],
                        bio_data={},
                        reports=[]
                    )
                else:  # INSTITUTION
                    new_user = InstitutionModel(
                        uid=uid,
                        user_type=user_type,
                        name=user_data.get("name"),
                        patient_list=[]
                    )
                
                # Save to database
                await self.db_service.create_user(new_user)
                return new_user
            else:
                # Create basic user model if no type specified
                new_user = UserModel(uid=uid, user_type=None)
                await self.db_service.create_user(new_user)
                return new_user
                
        except Exception as e:
            error_logger.log_database_error(e, "get_or_create_user", "users", uid)
            raise DatabaseError(
                message=get_error_message("DB_OPERATION_FAILED"),
                details={"operation": "get_or_create_user", "uid": uid}
            )
    
    async def authenticate_user(self, token: str) -> Union[UserModel, PatientModel, InstitutionModel]:
        """
        Authenticate user with Firebase token and return user model
        
        Args:
            token: Firebase ID token
            
        Returns:
            UserModel instance for authenticated user
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # Verify token
        decoded_token = await self.verify_token(token)
        uid = decoded_token.get("uid")
        
        if not uid:
            raise AuthenticationError(
                message=get_error_message("AUTH_TOKEN_INVALID"),
                details={"reason": "missing_uid"}
            )
        
        # Get or create user
        user = await self.get_or_create_user(uid)
        return user
    
    async def register_user(self, token: str, user_type: UserType, name: Optional[str] = None) -> Union[UserModel, PatientModel, InstitutionModel]:
        """
        Register new user with specified type
        
        Args:
            token: Firebase ID token
            user_type: Type of user (patient or institution)
            name: Optional user name
            
        Returns:
            Created UserModel instance
            
        Raises:
            AuthenticationError: If token is invalid
            ConflictError: If user already exists
            DatabaseError: If database operations fail
        """
        # Verify token
        decoded_token = await self.verify_token(token)
        uid = decoded_token.get("uid")
        
        if not uid:
            raise AuthenticationError(
                message=get_error_message("AUTH_TOKEN_INVALID"),
                details={"reason": "missing_uid"}
            )
        
        try:
            # Initialize database service if needed
            if not self.db_service.db:
                await self.db_service.initialize()
            
            # Check if user already exists
            existing_user = await self.db_service.get_user_by_uid(uid)
            if existing_user:
                raise ConflictError(
                    message=get_error_message("RESOURCE_ALREADY_EXISTS"),
                    details={"resource": "user", "uid": uid}
                )
            
            # Create user data
            user_data = {
                "user_type": user_type.value,
                "name": name or decoded_token.get("name") or decoded_token.get("email", "").split("@")[0]
            }
            
            # Create and return user
            user = await self.get_or_create_user(uid, user_data)
            return user
            
        except ConflictError:
            raise
        except Exception as e:
            error_logger.log_database_error(e, "register_user", "users", uid)
            raise DatabaseError(
                message=get_error_message("AUTH_REGISTRATION_FAILED"),
                details={"uid": uid, "user_type": user_type.value}
            )
    
    def validate_user_role(self, user: Union[UserModel, PatientModel, InstitutionModel], required_role: UserType) -> bool:
        """
        Validate if user has required role
        
        Args:
            user: User model to validate
            required_role: Required user type
            
        Returns:
            True if user has required role, False otherwise
        """
        return user.user_type == required_role
    
    def validate_user_roles(self, user: Union[UserModel, PatientModel, InstitutionModel], required_roles: list[UserType]) -> bool:
        """
        Validate if user has any of the required roles
        
        Args:
            user: User model to validate
            required_roles: List of acceptable user types
            
        Returns:
            True if user has any of the required roles, False otherwise
        """
        return user.user_type in required_roles