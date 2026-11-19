export interface User {
  id: string;
  email: string;
  username?: string;
  full_name?: string | null;
  avatar_url?: string | null;
  github_id?: number | null;
  google_id?: string | null;
  is_demo?: boolean;
  role: string;
  created_at: string;
}

export interface AuthResponse {
  user: User;
  token: {
    access_token: string;
    token_type: string;
    expires_in?: number;
  };
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: string;
  created_at: string;
}

export interface OrganizationMember {
  id: string;
  organization_id: string;
  user_id: string;
  role: string;
  user?: User;
  created_at: string;
}
