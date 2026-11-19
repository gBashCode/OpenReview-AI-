import { apiRequest } from './apiClient';
import { Organization, OrganizationMember } from '../types/auth';

export const organizationApi = {
  listOrganizations: (): Promise<Organization[]> => apiRequest('/organizations'),
  getOrganization: (id: string): Promise<Organization> => apiRequest(`/organizations/${id}`),
  listMembers: (orgId: string): Promise<OrganizationMember[]> =>
    apiRequest(`/organizations/${orgId}/members`),
  addMember: (orgId: string, email: string, role: string = 'member'): Promise<OrganizationMember> =>
    apiRequest(`/organizations/${orgId}/members`, {
      method: 'POST',
      body: JSON.stringify({ email, role }),
    }),
};
