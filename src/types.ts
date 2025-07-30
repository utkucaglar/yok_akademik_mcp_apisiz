export interface AcademicProfile {
  id: number;
  name: string;
  title: string;
  url: string;
  info: string;
  photoUrl: string;
  header: string;
  green_label: string;
  blue_label: string;
  keywords: string;
  email: string;
}

export interface Collaborator {
  id: number;
  name: string;
  title: string;
  info: string;
  green_label: string;
  blue_label: string;
  keywords: string;
  photoUrl: string;
  status: string;
  deleted: boolean;
  url: string;
  email: string;
}

export interface SearchResponse {
  success: boolean;
  sessionId: string;
  profiles: AcademicProfile[];
  total_profiles: number;
}

export interface CollaboratorsResponse {
  success: boolean;
  sessionId: string;
  profile: AcademicProfile;
  collaborators: Collaborator[];
  total_collaborators: number;
  completed: boolean;
  status: string;
  timestamp: number;
}

export interface Field {
  id: number;
  name: string;
  specialties: Specialty[];
}

export interface Specialty {
  id: number;
  name: string;
}

export interface SearchParams {
  name: string;
  email?: string;
  field_id?: number;
  specialty_ids?: string[];
}

export interface CollaboratorParams {
  sessionId: string;
  profileId: number;
} 