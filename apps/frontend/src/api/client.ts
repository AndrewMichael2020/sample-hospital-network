import axios, { type AxiosInstance, type AxiosResponse } from 'axios';
import { z } from 'zod';
import { 
  FacilitySummarySchema,
  PatientSchema,
  SiteSchema,
  ProgramSchema,
  SubprogramSchema,
  ProjectionPointSchema,
  ScenarioResponseSchema,
  PagedSchema
} from './schemas';
import type {
  FacilitySummary,
  Patient,
  Site,
  Program,
  Subprogram,
  ProjectionPoint,
  ScenarioResponse,
  ScenarioRequest,
  Paged,
  PatientFilters,
  EdProjectionParams,
  ApiError
} from './types';

// Create axios instance with base configuration
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080',
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Add request interceptor to attach request ID
  client.interceptors.request.use((config) => {
    config.headers['x-request-id'] = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    return config;
  });

  // Add response interceptor for error handling
  client.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.data) {
        const apiError: ApiError = {
          error: error.response.data.error || error.message,
          details: error.response.data.details,
          request_id: error.response.data.request_id,
        };
        throw apiError;
      }
      throw new Error(error.message || 'Unknown API error');
    }
  );

  return client;
};

const apiClient = createApiClient();

// Generic function to validate response with Zod schema
function validateResponse<T>(response: AxiosResponse, schema: z.ZodSchema<T>): T {
  try {
    return schema.parse(response.data);
  } catch (error) {
    if (error instanceof z.ZodError) {
      console.error('API response validation failed:', error.issues);
      throw new Error(`Invalid API response: ${error.issues.map(issue => issue.message).join(', ')}`);
    }
    throw error;
  }
}

// API client functions
export const apiClientFunctions = {
  // Reference data endpoints
  async getSites(): Promise<Site[]> {
    const response = await apiClient.get('/reference/sites');
    return validateResponse(response, z.array(SiteSchema));
  },

  async getPrograms(): Promise<Program[]> {
    const response = await apiClient.get('/reference/programs');
    return validateResponse(response, z.array(ProgramSchema));
  },

  async getSubprograms(programId?: number): Promise<Subprogram[]> {
    const params = programId ? { program_id: programId } : {};
    const response = await apiClient.get('/reference/subprograms', { params });
    return validateResponse(response, z.array(SubprogramSchema));
  },

  // Core API endpoints (adapting from the original instructions)
  async getFacilitiesSummary(): Promise<FacilitySummary> {
    const response = await apiClient.get('/facilities/summary');
    return validateResponse(response, FacilitySummarySchema);
  },

  async getPatients(filters: PatientFilters = {}): Promise<Paged<Patient>> {
    const response = await apiClient.get('/patients', { params: filters });
    return validateResponse(response, PagedSchema(PatientSchema));
  },

  async getEdProjections(params: EdProjectionParams): Promise<ProjectionPoint[]> {
    const response = await apiClient.get('/ed/projections', { params });
    return validateResponse(response, z.array(ProjectionPointSchema));
  },

  // Scenario calculation endpoint (main feature)
  async calculateScenario(request: ScenarioRequest): Promise<ScenarioResponse> {
    const response = await apiClient.post('/scenarios/compute', request);
    return validateResponse(response, ScenarioResponseSchema);
  },

  // Additional reference endpoints for staffed beds and baselines
  async getStaffedBeds(scheduleCode = 'Sched-A'): Promise<any[]> {
    const response = await apiClient.get('/reference/staffed-beds', {
      params: { schedule: scheduleCode }
    });
    return response.data; // TODO: Add proper schema validation
  },

  async getBaselines(year = 2022): Promise<any[]> {
    const response = await apiClient.get('/reference/baselines', {
      params: { year }
    });
    return response.data; // TODO: Add proper schema validation  
  },

  async getSeasonality(year = 2022): Promise<any[]> {
    const response = await apiClient.get('/reference/seasonality', {
      params: { year }
    });
    return response.data; // TODO: Add proper schema validation
  },

  async getStaffingFactors(): Promise<any[]> {
    const response = await apiClient.get('/reference/staffing-factors');
    return response.data; // TODO: Add proper schema validation
  },
};

export default apiClient;
export { validateResponse };