import { apiRequest, setAuthToken } from './apiClient';
import { AuthResponse, User } from '../types/auth';

export const authApi = {
  login: async (email: string, password: string): Promise<AuthResponse> => {
    const res = await apiRequest<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    if (res?.token?.access_token) {
      setAuthToken(res.token.access_token);
    }
    return res;
  },

  register: async (
    email: string,
    password: string,
    fullName?: string,
    organizationName?: string
  ): Promise<AuthResponse> => {
    const res = await apiRequest<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
        organization_name: organizationName,
      }),
    });
    if (res?.token?.access_token) {
      setAuthToken(res.token.access_token);
    }
    return res;
  },

  getMe: (): Promise<User> => apiRequest<User>('/auth/me'),

  logout: (): void => {
    setAuthToken(null);
  },
};
