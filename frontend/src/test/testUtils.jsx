import { isValidElement } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { render } from "@testing-library/react";

export function renderWithRouter(ui, initialEntries = ["/"]) {
  return render(<MemoryRouter initialEntries={initialEntries}>{ui}</MemoryRouter>);
}

export function renderWithRoutes(routes, initialEntries = ["/"]) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Routes>
        {routes.map((route) => isValidElement(route) ? route : (
          <Route key={route.path || "layout"} {...route} />
        ))}
      </Routes>
    </MemoryRouter>
  );
}
