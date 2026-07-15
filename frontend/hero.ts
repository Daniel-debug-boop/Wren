import { heroui } from "@heroui/react";

export default heroui({
  defaultTheme: "dark",
  layout: {
    radius: {
      small: "6px",
      medium: "8px",
      large: "9px",
    },
  },
  themes: {
    dark: {
      colors: {
        primary: "#c9b974",
        focus: "#5599e7",
      },
    },
    light: {
      colors: {
        primary: "#b8a85c",
        focus: "#5599e7",
      },
    },
  },
});
