import { useSearchParams } from "react-router";
import { useCallback } from "react";

export function useInvitation() {
  const [searchParams] = useSearchParams();

  const invitationToken = searchParams.get("invitation_token");
  const hasInvitation = !!invitationToken;

  const buildOAuthStateData = useCallback(
    (baseState: Record<string, string>) => {
      if (invitationToken) {
        return { ...baseState, invitation_token: invitationToken };
      }
      return baseState;
    },
    [invitationToken],
  );

  const clearInvitation = useCallback(() => {
    // Clear invitation from state
  }, []);

  return {
    invitationToken,
    hasInvitation,
    buildOAuthStateData,
    clearInvitation,
  };
}
