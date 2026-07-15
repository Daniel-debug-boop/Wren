export enum SecurityRisk {
  UNKNOWN = "unknown",
  SAFE = "safe",
  MEDIUM = "medium",
  HIGH = "high",
}

export interface TextContent {
  type: "text";
  text: string;
}

export interface ActionEvent {
  id: string;
  timestamp: string;
  source: "agent" | "user";
  thought: TextContent[];
  thinking_blocks: unknown[];
  action: Record<string, unknown>;
  tool_name: string;
  tool_call_id: string;
  tool_call: {
    id: string;
    type: "function";
    function: {
      name: string;
      arguments: string;
    };
  };
  llm_response_id: string;
  security_risk: SecurityRisk;
}

export interface MessageEvent {
  id: string;
  timestamp: string;
  source: "user" | "agent";
  llm_message: {
    role: "user" | "assistant";
    content: TextContent[];
  };
  activated_microagents: string[];
  extended_content: unknown[];
}

export interface ObservationEvent<T = Record<string, unknown>> {
  id: string;
  timestamp: string;
  source: "environment";
  tool_name: string;
  tool_call_id: string;
  action_id: string;
  observation: T;
}

export interface PlanningFileEditorObservation {
  kind: "PlanningFileEditorObservation";
  content: TextContent[];
  is_error: boolean;
  command: string;
  path: string;
  prev_exist: boolean;
  old_content: string | null;
  new_content: string | null;
}

export type AgentEvent = ActionEvent | MessageEvent | ObservationEvent;

export interface ConversationEvents {
  events: AgentEvent[];
  next_page_id: string | null;
}
