import { resources } from "./resources.js";

export function renderTable(resource, data, handlers) {
  const settings = resources[resource];
  const items = data[resource];
  const head = document.querySelector("#table-head");
  const body = document.querySelector("#table-body");

  document.querySelector("#list-title").textContent = settings.title;
  document.querySelector("#count").textContent = `${items.length} записей`;
  document.querySelector("#empty").hidden = items.length > 0;
  head.replaceChildren(createHeader(settings.columns));
  body.replaceChildren();

  for (const item of items) {
    const row = document.createElement("tr");
    for (const column of settings.columns) {
      row.append(createCell(column, item, data));
    }
    row.append(createActions(resource, item, handlers));
    body.append(row);
  }
}

function createHeader(columns) {
  const row = document.createElement("tr");
  const labels = columns.map(column => column.label);
  labels.push("Действия");

  for (const label of labels) {
    const cell = document.createElement("th");
    cell.textContent = label;
    row.append(cell);
  }
  return row;
}

function createCell(column, item, data) {
  const cell = document.createElement("td");
  const value = column.value(item, data);

  if (column.badge) {
    const badge = document.createElement("span");
    badge.className = `badge ${value.className}`;
    badge.textContent = value.label;
    cell.append(badge);
  } else {
    cell.textContent = value ?? "—";
  }
  return cell;
}

function createActions(resource, item, handlers) {
  const cell = document.createElement("td");
  cell.className = "actions";

  if (resource === "loans" && !item.returned_on) {
    cell.append(createButton("Вернуть", () => handlers.returnLoan(item)));
  }
  cell.append(createButton("Изменить", () => handlers.edit(item.id)));
  cell.append(createButton("Удалить", () => handlers.delete(item.id), true));
  return cell;
}

function createButton(label, handler, danger = false) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "row-button";
  button.classList.toggle("danger", danger);
  button.textContent = label;
  button.addEventListener("click", handler);
  return button;
}
