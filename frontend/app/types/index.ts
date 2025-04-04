// Employee Types
export interface Employee {
  name: string;
  employee_number: string;
  first_line_support_count: number;
  known_absences: string[];
  metadata: Record<string, any>;
}

export interface EmployeeCreateRequest {
  name: string;
  employee_number: string;
  known_absences?: string[];
  metadata?: Record<string, any>;
}

// Schedule Types
export interface Schedule {
  date: string;
  first_line_support: string;
}

export interface ScheduleCreateRequest {
  date: string;
  first_line_support: string;
}

// Rules Types
export interface Rules {
  max_days_per_week: number;
  preferred_balance: number;
}

export interface RulesUpdateRequest {
  max_days_per_week?: number;
  preferred_balance?: number;
}

// export interface ScheduleChange {
//   target_date: string;
//   suggested_replacement: string;
// }


// LLM communication types
// Base structure for all responses
interface BaseResponse {
  thoughts: string; // The AI's thought process while analyzing the request
  original_query: string; // The original query text that was analyzed
  response: string; // The response to the question
  reasoning: string; // Detailed explanation for the response
}

// Specific response types
interface QuestionResponse extends BaseResponse {
  type: "question";
}

interface OtherResponse extends BaseResponse {
  type: "other";
}

interface ComplaintResponse extends BaseResponse {
  type: "complaint";
  solution_proposal: string; // Proposed solution
}

// Schedule change submodel
interface ScheduleChange {
  employee_name: string; // Name of the originally scheduled employee
  target_date: string; // Format: YYYY-MM-DD
  suggested_replacement: string; // Suggested replacement employee
}

// Schedule change analysis response
interface ScheduleChangeAnalysis extends BaseResponse {
  type: "schedulechange";
  changes: ScheduleChange[];
  recommendation: "approve" | "deny" | "discuss"; // Recommendation outcome
}

// Union type for all possible response types
type AIResponse =
  | QuestionResponse
  | OtherResponse
  | ComplaintResponse
  | ScheduleChangeAnalysis;



// Schedule Change Types
// export interface ScheduleChangeAnalysis {
//   thoughts: string;
//   original_query: string;
//   reason?: string;
//   changes: ScheduleChange[];
//   recommendation: 'approve' | 'deny' | 'discuss';
//   reasoning: string;
// }

export interface ScheduleChangeRequest {
  request_text: string;
  metadata?: Record<string, any>;
}

export interface ScheduleChangeResponse {
  request: string;
  analysis: AIResponse;
}

// API Response Types
export interface MessageResponse {
  message: string;
}

// UI State Types
export interface ScheduleWithEmployee extends Schedule {
  employee_name: string; // Augmented with employee name for display
}

export interface UIState {
  employees: Employee[];
  schedules: ScheduleWithEmployee[];
  rules: Rules;
  isLoading: boolean;
  error: string | null;
}

export interface SimpleRequest {
  request: string
}

export interface SimpleResponse {
  request: string
}