import { render, screen } from "@testing-library/react";
import App from "../App";

describe("App", () => {
  it("renders the main heading", () => {
    render(<App />);
    expect(screen.getByText("HealthInsight Core")).toBeInTheDocument();
  });

  it("renders the welcome message", () => {
    render(<App />);
    expect(
      screen.getByText("Welcome to HealthInsight Core")
    ).toBeInTheDocument();
  });

  it("renders the description", () => {
    render(<App />);
    expect(
      screen.getByText("Medical test analysis and patient management system")
    ).toBeInTheDocument();
  });
});
