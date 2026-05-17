import type { Preview } from "@storybook/react-vite";
import "../src/index.css";

const preview: Preview = {
  parameters: {
    layout: "fullscreen",
    backgrounds: {
      default: "forensic dark",
      values: [{ name: "forensic dark", value: "#0d1117" }],
    },
  },
};

export default preview;
