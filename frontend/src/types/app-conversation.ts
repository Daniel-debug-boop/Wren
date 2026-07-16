// Frontend types for app conversation API
// These mirror the backend models in wren/app_server/app_conversation/app_conversation_models.py

export interface SuggestedTask {
  name: string;
  description?: string;
  prompt: string;
}

export interface AppConversationStartRequest {
  sandbox_id?: string | null;
  conversation_id?: string | null;
  initial_message?: {
    role: "user";
    content: Array<{ type: "text"; text: string }>;
  } | null;
  system_message_suffix?: string | null;
  llm_model?: string | null;
  selected_repository?: string | null;
  selected_branch?: string | null;
  git_provider?: string | null;
  title?: string | null;
  suggested_task?: SuggestedTask | null;
  trigger?:
    | "resolver"
    | "gui"
    | "suggested_task"
    | "wren_api"
    | "slack"
    | "microagent_management"
    | "jira"
    | "jira_dc"
    | "linear"
    | "bitbucket"
    | "automation"
    | null;
  pr_number?: number[];
  parent_conversation_id?: string | null;
  agent_type?: "default" | "plan";
  mode?: "plan" | "code" | "review" | "debug" | "ask" | "video";
  plugins?: Array<{
    source: string;
    ref?: string | null;
    repo_path?: string | null;
    parameters?: Record<string, unknown> | null;
  }> | null;
  secrets?: Record<string, string> | null;
}

export type AppConversationStartTaskStatus =
  | "WORKING"
  | "WAITING_FOR_SANDBOX"
  | "PREPARING_REPOSITORY"
  | "RUNNING_SETUP_SCRIPT"
  | "SETTING_UP_GIT_HOOKS"
  | "SETTING_UP_SKILLS"
  | "STARTING_CONVERSATION"
  | "READY"
  | "ERROR";

export interface AppConversationStartTask {
  id: string;
  created_by_user_id?: string | null;
  status: AppConversationStartTaskStatus;
  detail?: string | null;
  app_conversation_id?: string | null;
  sandbox_id?: string | null;
  agent_server_url?: string | null;
  request: AppConversationStartRequest;
  created_at: string;
  updated_at: string;
}

export interface AppConversationPage {
  items: AppConversation[];
  next_page_id?: string | null;
}

export interface AppConversation {
  id: string;
  created_by_user_id?: string | null;
  sandbox_id: string;
  selected_repository?: string | null;
  selected_branch?: string | null;
  git_provider?: string | null;
  title?: string | null;
  trigger?: string | null;
  pr_number: number[];
  llm_model?: string | null;
  agent_kind: string;
  metrics?: Record<string, unknown> | null;
  parent_conversation_id?: string | null;
  sub_conversation_ids: string[];
  public?: boolean | null;
  tags: Record<string, string>;
  created_at: string;
  updated_at: string;
  sandbox_status: string;
  execution_status?: string | null;
  conversation_url?: string | null;
  session_api_key?: string | null;
}
