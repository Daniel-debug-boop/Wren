import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { WrenApiKeyHelp } from "#/components/features/settings/wren-api-key-help";

describe("WrenApiKeyHelp", () => {
  it("renders the help link with the provided testId", () => {
    render(<WrenApiKeyHelp testId="wren-api-key-help" />);

    expect(screen.getByTestId("wren-api-key-help")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "SETTINGS$NAV_API_KEYS" }),
    ).toHaveAttribute("href", "https://app.wren.dev/settings/api-keys");
  });

  it("renders the billing info paragraph with the pricing-details link", () => {
    render(<WrenApiKeyHelp testId="wren-api-key-help" />);

    expect(screen.getByText("SETTINGS$LLM_BILLING_INFO")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "SETTINGS$SEE_PRICING_DETAILS" }),
    ).toHaveAttribute(
      "href",
      "https://docs.wren.dev/usage/llms/wren-llms",
    );
  });
});
