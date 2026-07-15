import { useLocation } from "react-router";

export function useIsOnTosPage(): boolean {
  const location = useLocation();
  return location.pathname === "/terms-of-service";
}
