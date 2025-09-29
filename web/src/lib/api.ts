import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Manuscript {
  id: string;
  title: string;
  author?: string;
  created_at: string;
  current_version_id?: string;
}

export interface EditOption {
  option_id: string;
  label: string;
  before: string;
  after: string;
  diff: any[];
  severity: string;
}

export interface EditSuggestResponse {
  edit_session_id: string;
  options: EditOption[];
}

export interface EditSuggestRequest {
  manuscript_id: string;
  instruction: string;
  target_range: { start: number; end: number };
  k?: number;
  num_options?: number;
  style_prefs?: Record<string, string>;
}

export interface ApplyEditRequest {
  edit_session_id: string;
  option_id: string;
}

export const manuscriptApi = {
  // Create a new manuscript
  create: async (data: { title: string; author?: string; content: string }): Promise<Manuscript> => {
    const response = await api.post('/manuscripts/', data);
    return response.data;
  },

  // Get manuscript metadata
  get: async (id: string): Promise<Manuscript> => {
    const response = await api.get(`/manuscripts/${id}`);
    return response.data;
  },

  // Get manuscript content
  getContent: async (id: string): Promise<{ content: string }> => {
    const response = await api.get(`/manuscripts/${id}/content`);
    return response.data;
  },

  // Update style preferences
  updateStylePrefs: async (id: string, prefs: Record<string, string>) => {
    const response = await api.put(`/manuscripts/${id}/style`, prefs);
    return response.data;
  },

  // Get version history
  getHistory: async (id: string) => {
    const response = await api.get(`/manuscripts/${id}/history`);
    return response.data;
  },

  // Export manuscript
  export: async (id: string, format: 'markdown' | 'docx'): Promise<Blob> => {
    const response = await api.post(`/manuscripts/${id}/export`, null, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  },

  // Revert to previous version
  revert: async (id: string, toVersionId: string) => {
    const response = await api.post(`/manuscripts/${id}/revert`, { to_version_id: toVersionId });
    return response.data;
  },

  // Re-process for embeddings
  ingest: async (id: string) => {
    const response = await api.post(`/manuscripts/${id}/ingest`);
    return response.data;
  },
};

export const editApi = {
  // Get edit suggestions
  suggest: async (request: EditSuggestRequest): Promise<EditSuggestResponse> => {
    const response = await api.post('/edits/suggest', request);
    return response.data;
  },

  // Apply an edit
  apply: async (request: ApplyEditRequest) => {
    const response = await api.post('/edits/apply', request);
    return response.data;
  },
};

export default api;
