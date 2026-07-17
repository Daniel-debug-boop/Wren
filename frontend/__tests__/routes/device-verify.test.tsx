import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { createRoutesStub } from "react-router";
import DeviceVerify from "#/routes/device-verify";

const RouterStub = createRoutesStub([
  {
    Component: DeviceVerify,
    path: "/device-verify",
  },
]);

describe("DeviceVerify", () => {
  it("should render the device verification page", () => {
    render(<RouterStub initialEntries={["/device-verify"]} />);

    expect(screen.getByTestId("device-verify-page")).toBeInTheDocument();
    expect(screen.getByText("Device Verification")).toBeInTheDocument();
    expect(
      screen.getByText("Enter the code shown on your device."),
    ).toBeInTheDocument();
  });
});
