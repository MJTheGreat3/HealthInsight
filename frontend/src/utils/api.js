const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const API_URLS = {
  USER_ME: `${API_BASE_URL}/user/me`,
  USER_FAVORITES: `${API_BASE_URL}/user/favorites`,
  HOSPITAL_PATIENTS: `${API_BASE_URL}/hospital/patients`,
  HOSPITAL_PATIENT: (uid) => `${API_BASE_URL}/hospital/patient/${uid}`,
  DASHBOARD_ACTIONABLE_SUGGESTIONS: `${API_BASE_URL}/dashboard/actionable-suggestions`,
  ACCESS_REQUEST: `${API_BASE_URL}/access/request`,
};

export default API_BASE_URL;