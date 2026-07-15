import { useConfig } from "#/hooks/query/use-config";

export interface AppModeInfo {
  isOss: boolean;
  isSaas: boolean;
  isCloud: boolean;
  isSelfHosted: boolean;
  isEnterpriseSelfHosted: boolean;
  isEnterpriseCloud: boolean;
  appMode: "oss" | "saas";
  deploymentMode: "cloud" | "self_hosted" | undefined;
}

export function useAppMode(): AppModeInfo {
  const { data: config } = useConfig();

  const appMode = config?.app_mode ?? "oss";
  const deploymentMode = config?.feature_flags?.deployment_mode;

  const isOss = appMode === "oss";
  const isSaas = appMode === "saas";
  const isCloud = isSaas && deploymentMode === "cloud";
  const isSelfHosted = isSaas && deploymentMode === "self_hosted";

  return {
    isOss,
    isSaas,
    isCloud,
    isSelfHosted,
    isEnterpriseSelfHosted: isSelfHosted,
    isEnterpriseCloud: isCloud,
    appMode,
    deploymentMode,
  };
}
